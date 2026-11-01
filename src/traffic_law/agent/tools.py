"""The agent's tools: an allow-list, argument validation, and compact results.

Every tool result also records what the model has *seen* (offense ids, section keys), so
the grounding check can later reject an answer that cites something no tool returned.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from ..data.penalties import UnknownOffense, summarize
from ..retrieval.offenses import clause_text
from ..retrieval.retriever import Retriever


# ------------------------------------------------------------------ arguments
class SearchArgs(BaseModel):
    query: str = Field(min_length=2, max_length=500)


class SectionArgs(BaseModel):
    key: str = Field(pattern=r"^[a-z0-9\-]+:\d+(/\d+)?(ทวิ|ตรี|จัตวา|เบญจ)?(/\d+)?$")


class PenaltyArgs(BaseModel):
    offense_ids: list[str] = Field(min_length=1, max_length=10)


SCHEMAS: list[dict[str, Any]] = [
    {"type": "function", "function": {
        "name": "search_offenses",
        "description": "Search the catalogue of traffic offenses that carry demerit points. "
                       "Write the query in formal Thai legal wording describing the act "
                       "(e.g. 'ขับรถในขณะเมาสุรา', 'ขับรถบนทางเท้า'). Returns candidate offenses "
                       "with offense_id, description, points and the statute section key.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "search_law",
        "description": "Search the text of the Land Traffic Act B.E. 2522 (as amended to No.13, 2022) "
                       "and the 2022 point regulation. Returns section keys with a short excerpt.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "get_section",
        "description": "Full current text of one section, by the key a search returned "
                       "(e.g. 'land-traffic-2522:43').",
        "parameters": {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}}},
    {"type": "function", "function": {
        "name": "compute_penalty",
        "description": "Maximum fines, jail and demerit points for the offenses of ONE incident.",
        "parameters": {"type": "object", "properties": {
            "offense_ids": {"type": "array", "items": {"type": "string"}}}, "required": ["offense_ids"]}}},
]
ALLOWED = {s["function"]["name"] for s in SCHEMAS}


@dataclass
class Seen:
    """Everything tools have shown the model in this run."""
    offenses: set[str] = field(default_factory=set)
    sections: set[str] = field(default_factory=set)


class ToolError(ValueError):
    pass


class Toolbox:
    def __init__(self, retriever: Retriever, *, k: int = 8, mode: str = "bm25"):
        self.r = retriever
        self.k = k
        self.mode = mode
        self.seen = Seen()

    def call(self, name: str, raw_args: str | dict) -> str:
        """Run one tool; always returns a JSON string (errors included) for the model."""
        try:
            if name not in ALLOWED:
                raise ToolError(f"unknown tool {name!r}; allowed: {sorted(ALLOWED)}")
            args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            if not isinstance(args, dict):
                raise ToolError("arguments must be a JSON object")
            result = getattr(self, f"_{name}")(args)
        except (ValidationError, ToolError, json.JSONDecodeError, UnknownOffense) as e:
            result = {"error": str(e)[:300]}
        return json.dumps(result, ensure_ascii=False)

    # ---------------------------------------------------------------- tools
    def _search_offenses(self, args: dict) -> dict:
        q = SearchArgs.model_validate(args).query
        out = []
        for rule, _score, _ranks in self.r.search_offenses(q, k=self.k, mode=self.mode):
            key = f"{rule.law}:{rule.section}"
            sec = self.r.sections.get(key)
            self.seen.offenses.add(rule.offense_id)
            if sec is not None:
                self.seen.sections.add(key)
            out.append({
                "offense_id": rule.offense_id, "description": rule.description, "points": rule.points,
                "section_key": key if sec is not None else None,
                "statute": (clause_text(sec, rule.clause)[:200] if sec is not None
                            else "อยู่ใน พ.ร.บ.รถยนต์ (ไม่มีตัวบทในระบบ)"),
            })
        return {"candidates": out}

    def _search_law(self, args: dict) -> dict:
        q = SearchArgs.model_validate(args).query
        out = []
        for h in self.r.search(q, k=5, mode=self.mode):
            self.seen.sections.add(h.key)
            out.append({"key": h.key, "label": h.section.label,
                        "excerpt": re.sub(r"\s+", " ", h.best_chunk)[:350]})
        return {"sections": out}

    def _get_section(self, args: dict) -> dict:
        key = SectionArgs.model_validate(args).key
        sec = self.r.sections.get(key)
        if sec is None:
            raise ToolError(f"no section {key!r}; use a key returned by search_law or search_offenses")
        self.seen.sections.add(key)
        return {"key": key, "label": sec.label, "text": sec.text[:2500]}

    def _compute_penalty(self, args: dict) -> dict:
        ids = PenaltyArgs.model_validate(args).offense_ids
        return summarize(ids, self.r.rules).model_dump()
