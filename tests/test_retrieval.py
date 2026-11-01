"""Retrieval tests on a tiny synthetic corpus; dense parts use a deterministic fake embedder
(no model download, no network)."""
import numpy as np
import pytest

from traffic_law.retrieval.chunks import make_chunks
from traffic_law.retrieval.dense import VectorIndex, build_vector_index
from traffic_law.retrieval.legal_terms import expand, expansions
from traffic_law.retrieval.offenses import build_offense_docs, clause_text, regulation_items
from traffic_law.retrieval.retriever import Retriever
from traffic_law.retrieval.tokenize import tokenize
from traffic_law.schemas import PenaltyRule, Section

DOC = "land-traffic-2522"


def sec(sid, text, doc=DOC, unit="มาตรา"):
    return Section(doc_id=doc, act="พระราชบัญญัติจราจรทางบก พ.ศ. ๒๕๒๒", unit=unit, section=sid, text=text)


SECTIONS = [
    sec("21", "มาตรา ๒๑ ผู้ขับขี่ต้องปฏิบัติให้ถูกต้องตามสัญญาณจราจรและเครื่องหมายจราจร"),
    sec("22", "มาตรา ๒๒ ผู้ขับขี่ซึ่งขับรถมาถึงทางเดินรถที่มีสัญญาณจราจร\n\n(๒) สัญญาณจราจรไฟสีแดง ให้ผู้ขับขี่หยุดรถหลังเส้นให้รถหยุด"),
    sec("43", "มาตรา ๔๓ ห้ามมิให้ผู้ขับขี่ขับรถ\n\n(๒) ในขณะเมาสุราหรือของเมาอย่างอื่น\n\n(๗) บนทางเท้าโดยไม่มีเหตุอันสมควร\n\n(๙) ในขณะใช้โทรศัพท์เคลื่อนที่"),
    sec("122", "มาตรา ๑๒๒ ผู้ขับขี่รถจักรยานยนต์และคนโดยสารรถจักรยานยนต์ต้องสวมหมวกที่จัดทำขึ้นโดยเฉพาะเพื่อป้องกันอันตราย"),
    sec("11", "ข้อ ๑๑ ให้ตัดคะแนน ดังนี้\n๑๑.๑ ตัดคะแนน ครั้งละ ๑ คะแนน\n(๑) ขับรถไม่หยุดให้คนเดินข้ามทาง ณ ทางข้าม (มาตรา ๒๑ วรรคหนึ่ง และมาตรา ๑๕๒)\n"
               "(๒) ขับรถบนทางเท้าโดยไม่มีเหตุอันสมควร (มาตรา ๔๓ (๗) และมาตรา ๑๕๗)\n๑๑.๒ ตัดคะแนน ครั้งละ ๒ คะแนน\n"
               "(๑) ขับรถโดยไม่ปฏิบัติตามสัญญาณจราจรไฟสีแดง (มาตรา ๒๒ (๒) และมาตรา ๑๕๒)\n"
               "ให้ตัดคะแนนความประพฤติในการขับรถตามจำนวนคะแนนที่กำหนด", doc="point-system-reg-2565", unit="ข้อ"),
]


def rule(oid, desc, section, clause, ref):
    return PenaltyRule(offense_id=oid, description=desc, section=section, clause=clause, penalty_section="152",
                       fine_max=4000, points=1, source=f"ระเบียบ ข้อ {ref}")


RULES = {r.offense_id: r for r in [
    rule("crosswalk_no_stop", "ขับรถไม่หยุดให้คนเดินข้ามทาง ณ ทางข้าม", "21", "วรรคหนึ่ง", "11.1(1)"),
    rule("sidewalk", "ขับรถบนทางเท้าโดยไม่มีเหตุอันสมควร", "43", "(๗)", "11.1(2)"),
    rule("red_light", "ฝ่าสัญญาณไฟแดง", "22", "(๒)", "11.2(1)"),
]}


class FakeEmbedder:
    """Bag-of-characters vectors: deterministic and good enough to test the plumbing."""
    name = "fake"

    def encode(self, texts, *, kind):
        out = np.zeros((len(texts), 128), dtype=np.float32)
        for i, t in enumerate(texts):
            for ch in t:
                out[i, ord(ch) % 128] += 1
        return out / np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-9)


def test_tokenize_digits_and_stopwords():
    toks = tokenize("ขับรถเร็วเกิน ๑๒๐ ที่ทางเท้า")
    assert "120" in toks and "เกิน" in toks and "ที่" not in toks


def test_term_table_bridges_colloquial_words():
    q = "ขี่มอไซค์ไม่ใส่หมวกกันน็อค ฝ่าไฟแดง"
    ex = expansions(q)
    assert "รถจักรยานยนต์" in ex and any("หมวก" in e for e in ex) and any("ไฟสีแดง" in e for e in ex)
    assert expand("สวัสดี") == "สวัสดี"
    assert any("ความเร็ว" in e for e in expansions("ขับ 140 ป้ายบอก 90"))


def test_chunks_keep_paragraphs_and_split_long_sections():
    long = sec("4", "มาตรา ๔ บทนิยาม\n\n" + "\n\n".join(f"({i}) คำนิยามที่ {i} " + "ก" * 300 for i in range(1, 8)))
    ch = make_chunks([long], max_chars=900)
    assert len(ch) > 1 and all(len(c.text) <= 900 + 30 for c in ch)
    assert ch[1].text.startswith("มาตรา 4 (ต่อ)")
    assert {c.section_key for c in ch} == {f"{DOC}:4"}


def test_bm25_and_expansion():
    r = Retriever(SECTIONS)
    q = "มอไซค์ไม่ใส่หมวกกันน็อค"
    score = lambda hits: next(h.score for h in hits if h.section.section == "122")
    raw = r.search(q, k=5, mode="bm25", use_expansion=False)
    expanded = r.search(q, k=5, mode="bm25")
    assert expanded[0].section.section == "122"
    assert score(expanded) > 2 * score(raw)   # statutory wording ("รถจักรยานยนต์", "สวมหมวกที่จัดทำขึ้น...") adds matches
    assert "22" in [h.section.section for h in r.search("ฝ่าไฟแดง", k=2, mode="bm25")]


def test_doc_filter():
    r = Retriever(SECTIONS)
    hits = r.search("ทางเท้า", k=5, mode="bm25", docs={"point-system-reg-2565"})
    assert hits and all(h.section.doc_id == "point-system-reg-2565" for h in hits)


def test_hybrid_fuses_with_rrf():
    chunks = make_chunks(SECTIONS)
    emb = FakeEmbedder()
    r = Retriever(SECTIONS, chunks=chunks, vectors=build_vector_index(chunks, emb), embedder=emb)
    hits = r.search("สวมหมวกที่จัดทำขึ้นโดยเฉพาะ", k=3, mode="hybrid")
    assert hits[0].section.section == "122"
    assert set(hits[0].ranks) <= {"bm25", "dense"} and "dense" in hits[0].ranks
    assert hits[0].score <= 2 / 61 + 1e-9                     # RRF scale, not BM25 scale


def test_vector_index_roundtrip_and_stale_check(tmp_path):
    chunks = make_chunks(SECTIONS)
    idx = build_vector_index(chunks, FakeEmbedder())
    idx.save(tmp_path)
    back = VectorIndex.load(tmp_path)
    assert back.chunk_keys == idx.chunk_keys and back.model == "fake"
    stale = VectorIndex(vectors=idx.vectors, chunk_keys=idx.chunk_keys[:-1] + ["x:999#0"], model="fake")
    with pytest.raises(ValueError, match="stale"):
        Retriever(SECTIONS, chunks=chunks, vectors=stale, embedder=FakeEmbedder())


def test_regulation_items_and_offense_docs():
    items = regulation_items(SECTIONS)
    assert set(items) == {"11.1(1)", "11.1(2)", "11.2(1)"}
    assert items["11.1(1)"].startswith("ขับรถไม่หยุดให้คนเดินข้ามทาง")
    assert clause_text(SECTIONS[2], "(๗)") == "บนทางเท้าโดยไม่มีเหตุอันสมควร"
    docs = {d.offense_id: d.text for d in build_offense_docs(RULES, SECTIONS)}
    assert "ทางข้าม" in docs["crosswalk_no_stop"] and "(มาตรา" not in docs["crosswalk_no_stop"]


def test_offense_search_finds_what_the_statute_text_lacks():
    r = Retriever(SECTIONS, rules=RULES)
    top = r.search_offenses("ไม่หยุดให้คนข้ามทางม้าลาย", k=3, mode="bm25")
    assert top[0][0].offense_id == "crosswalk_no_stop"     # มาตรา ๒๑ itself never says "ทางข้าม"
