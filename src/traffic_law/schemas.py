"""Pydantic models shared by every layer: corpus, penalty table, agent output, API."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

# section ids look like "43", "122/1", "43ทวิ", "43ทวิ/1", "160ตรี/3" -- Arabic digits, no spaces
SECTION_ID_PATTERN = r"^\d+(/\d+)?(ทวิ|ตรี|จัตวา|เบญจ)?(/\d+)?$"


# ---------------------------------------------------------------- corpus
class Section(BaseModel):
    """One มาตรา of one act -- the retrieval unit (NitiBench: section chunking works best)."""

    doc_id: str = Field(description="short id of the source act, e.g. 'land-traffic-2522'")
    act: str = Field(description="full Thai name of the act")
    unit: Literal["มาตรา", "ข้อ"] = "มาตรา"
    section: str = Field(pattern=SECTION_ID_PATTERN)
    text: str
    amends: list[str] = Field(
        default_factory=list,
        description="for an amending act: section ids of the main act this section replaces/inserts",
    )
    amended_by: list[str] = Field(
        default_factory=list, description="after consolidation: amending act sections applied here"
    )
    previous_text: str | None = Field(
        default=None, description="wording before the amendments in amended_by (for 'what was it before?')"
    )
    effective_from: str | None = Field(default=None, description="ISO date the act took effect")
    source: str = ""

    @property
    def key(self) -> str:
        return f"{self.doc_id}:{self.section}"

    @property
    def label(self) -> str:
        """Human citation, e.g. 'มาตรา 43 ทวิ/1 พระราชบัญญัติจราจรทางบก พ.ศ. ๒๕๒๒'."""
        import re

        sid = re.sub(r"(\d)(ทวิ|ตรี|จัตวา|เบญจ)", r"\1 \2", self.section)
        return f"{self.unit} {sid} {self.act}"


# ---------------------------------------------------------------- penalties
class PenaltyRule(BaseModel):
    """One row of data/penalties.csv -- curated from the Act and the point-system regulation."""

    offense_id: str
    description: str
    law: str = Field(default="land-traffic-2522", description="doc_id of the act holding `section`")
    section: str = Field(pattern=SECTION_ID_PATTERN, description="section that defines the duty")
    clause: str = Field(default="", description="sub-clause / paragraph, e.g. '(๔)' or 'วรรคหนึ่ง'")
    penalty_section: str = Field(default="", description="section that sets the punishment")
    fine_max: int | None = Field(default=None, ge=0, description="max fine in baht; None = not in corpus")
    jail_max_months: int | None = Field(default=0, ge=0, description="None = depends on another law")
    points: int = Field(default=0, ge=0, description="points deducted under the point system")
    source: str = Field(description="where this row comes from")
    verified: bool = False
    note: str = ""

    @field_validator("penalty_section")
    @classmethod
    def _empty_or_section(cls, v: str) -> str:
        import re

        if v and not re.match(SECTION_ID_PATTERN, v):
            raise ValueError(f"bad section id {v!r}")
        return v


# ---------------------------------------------------------------- agent output
class Violation(BaseModel):
    offense_id: str
    reason: str = Field(description="which fact in the user's story triggers this offense")
    citation_key: str = Field(description="Section.key of the passage that supports it")


class Verdict(BaseModel):
    """Final answer of the agent, validated before it is shown to the user."""

    status: Literal["violations_found", "no_violation", "need_more_info", "out_of_scope"]
    violations: list[Violation] = Field(default_factory=list)
    follow_up_question: str | None = None
    summary_th: str = ""


class PenaltySummary(BaseModel):
    """Computed by code from PenaltyRule rows -- the LLM never does this arithmetic."""

    offense_ids: list[str]
    total_fine_max: int = Field(description="sum over offenses whose fine_max is known")
    fine_unknown: list[str] = Field(default_factory=list, description="offenses with no fine in corpus")
    points_raw: int = Field(description="sum of points before the per-incident cap")
    total_points: int = Field(description="points actually deducted (capped per incident)")
    points_capped: bool = False
    points_left: int
    license_suspension_risk: bool
    any_jail: bool
    unverified: list[str] = Field(default_factory=list)
