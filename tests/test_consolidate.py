from traffic_law.data.consolidate import _paragraphs, classify, consolidate
from traffic_law.data.statute import split_sections

from .test_statute import AMENDING_ACT, MAIN_ACT

# paragraphs (วรรค) are separated by blank lines, as build_corpus produces them from indentation
MAIN_WITH_PARAS = MAIN_ACT.replace(
    "มาตรา ๒ ผู้ขับขี่ต้องปฏิบัติตาม\n",
    "มาตรา ๒ ผู้ขับขี่ต้องปฏิบัติตาม\n\n(๑) ข้อย่อยหนึ่ง\n\nวรรคสองของมาตรา ๒\n\nวรรคสามของมาตรา ๒\n",
)

EXTRA = """
มาตรา ๖ ให้ยกเลิกมาตรา ๓/๑ แห่งพระราชบัญญัติจราจรทางบก พ.ศ. ๒๕๒๒
มาตรา ๗ ให้ยกเลิกความในวรรคหนึ่งของมาตรา ๒ แห่งพระราชบัญญัติจราจร
ทางบก พ.ศ. ๒๕๒๒ และให้ใช้ความต่อไปนี้แทน
“มาตรา ๒ ผู้ขับขี่ต้องปฏิบัติตามแบบใหม่”
มาตรา ๘ ให้ยกเลิกความในมาตรา ๔ ทวิ แห่งพระราชบัญญัติจราจรทางบก
พ.ศ. ๒๕๒๒ และให้ใช้ความต่อไปนี้แทน
“มาตรา ๔/๑ ข้อความที่ย้ายเลขใหม่”
มาตรา ๙ ให้เพิ่มความต่อไปนี้เป็นวรรคสี่ของมาตรา ๒ แห่งพระราชบัญญัติจราจรทางบก พ.ศ. ๒๕๒๒
“วรรคสี่ที่เพิ่มใหม่”
มาตรา ๑๐ ให้เพิ่มความต่อไปนี้เป็นวรรคเก้าของมาตรา ๓ แห่งพระราชบัญญัติจราจรทางบก พ.ศ. ๒๕๒๒
“วรรคที่ไม่มีที่ลง”
"""


def _build():
    main = split_sections(MAIN_WITH_PARAS, doc_id="main", act="หลัก", end_marker="^ผู้รับสนอง")
    am_text = (AMENDING_ACT + EXTRA).replace("แห่งพระราชบัญญัติตัวอย่าง",
                                            "แห่งพระราชบัญญัติจราจรทางบก พ.ศ. ๒๕๒๒")
    am = split_sections(am_text, doc_id="no13", act="ฉบับที่ ๑๓", amending=True,
                        effective_from="2022-09-05")
    return consolidate(main, am)


def test_classify():
    assert classify("มาตรา ๒ ให้ยกเลิกความในมาตรา ๓ แห่งพระราชบัญญัติจราจรทางบก “มาตรา ๓ ใหม่”") == "replace"
    assert classify("มาตรา ๕ ให้นายกรัฐมนตรีรักษาการ") == "other"


def test_sub_clauses_stay_in_their_paragraph():
    assert _paragraphs("มาตรา ๑ หัว\n\n(๑) ก\n\n(๒) ข\n\nวรรคสอง") == ["มาตรา ๑ หัว\n(๑) ก\n(๒) ข", "วรรคสอง"]


def test_consolidation_actions():
    final, rep = _build()
    by = {s.section: s for s in final}
    assert rep.replaced == ["3"]
    assert set(rep.inserted) == {"6/1", "6/2", "4/1"}
    assert set(rep.repealed) == {"3/1", "4ทวิ"}
    assert rep.partial.count("2") == 2 and "6" in rep.partial
    assert rep.partial_fallback == ["3"]                 # วรรคเก้า does not exist -> note, no guess
    assert "ช่องซ้ายสุด" in by["3"].text and "no13:2" in by["3"].amended_by
    assert by["6/2"].text.rstrip().endswith("อ้างอิงยาวในโทษ")


def test_rate_change_is_spliced_and_old_text_kept():
    final, _ = _build()
    s = {x.section: x for x in final}["6"]
    assert "ต้องระวางโทษปรับไม่เกินสี่พันบาท" in s.text
    assert "สองร้อยบาท" not in s.text and "[แก้ไขโดย" not in s.text
    assert "ตั้งแต่สองร้อยบาทถึงห้าร้อยบาท" in s.previous_text


def test_paragraph_replace_and_add():
    final, _ = _build()
    s = {x.section: x for x in final}["2"]
    paras = _paragraphs(s.text)
    assert paras[0] == "มาตรา ๒ ผู้ขับขี่ต้องปฏิบัติตามแบบใหม่"   # วรรคหนึ่ง incl. its (๑) replaced
    # (the fixture's wrapped "มาตรา ๓ (๑)" reference stays inside วรรคสาม, as it should)
    assert len(paras) == 4
    assert paras[1] == "วรรคสองของมาตรา ๒"
    assert paras[2].startswith("วรรคสามของมาตรา ๒")
    assert paras[3] == "วรรคสี่ที่เพิ่มใหม่"
    assert "ข้อย่อยหนึ่ง" in s.previous_text


def test_order_keeps_inserted_sections_next_to_their_base():
    final, _ = _build()
    ids = [s.section for s in final]
    assert ids.index("4/1") < ids.index("6") < ids.index("6/1") < ids.index("6/2")
