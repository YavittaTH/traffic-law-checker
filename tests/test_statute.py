"""Parser tests on synthetic act text. Wording is invented; the LAYOUT copies real cases
found in laws_03.pdf (krisdika) and T_0005.pdf (ฉบับที่ ๑๓)."""
from traffic_law.data.statute import norm_sid, split_sections

MAIN_ACT = """
พระราชบัญญัติ
ตัวอย่างการจราจร
มาตรา ๑ พระราชบัญญัตินี้เรียกว่า "พระราชบัญญัติตัวอย่าง"
มาตรา ๒ ผู้ขับขี่ต้องปฏิบัติตาม
มาตรา ๓ (๑) และหน้าที่อื่น
มาตรา ๓ ผู้ขับขี่ต้องขับรถในช่องซ้าย เว้นแต่กรณีตาม
มาตรา ๒ วรรคหนึ่ง
มาตรา ๓/๑ ผู้ขับขี่ต้องสวมอุปกรณ์ตัวอย่าง
มาตรา ๔ ทวิ ห้ามจอดรถในที่ตัวอย่าง
มาตรา ๔ ทวิ/๑ ในกรณีที่มีอุบัติเหตุตัวอย่าง
มาตรา ๕ (ยกเลิก)
มาตรา ๖ ผู้ใดฝ่าฝืนมาตรา ๓ ต้องระวางโทษปรับตั้งแต่สองร้อยบาทถึงห้าร้อยบาท
ผู้รับสนองพระบรมราชโองการ
นายกรัฐมนตรี
มาตรา ๒ บทเฉพาะกาลของฉบับแก้ไขเก่า
"""

AMENDING_ACT = """
มาตรา ๑ พระราชบัญญัตินี้เรียกว่า "ฉบับแก้ไขตัวอย่าง"
มาตรา ๒ ให้ยกเลิกความในมาตรา ๓ แห่งพระราชบัญญัติตัวอย่าง และให้ใช้ความต่อไปนี้แทน
“มาตรา ๓ ผู้ขับขี่ต้องขับรถในช่องซ้ายสุด
ข้อความต่อ”
มาตรา ๓ ให้เพิ่มความต่อไปนี้เป็นมาตรา ๖/๑ มาตรา ๖/๒ และ
มาตรา ๖ ตรี/๓ แห่งพระราชบัญญัติตัวอย่าง
“มาตรา ๖/๑ ผู้ใดฝ่าฝืนต้องระวางโทษปรับเพิ่ม
มาตรา ๖/๒ ห้ามมิให้ผู้ขับขี่ทำสิ่งตัวอย่าง
มาตรา ๓๗ มาตรา ๓๘ อ้างอิงยาวในโทษ”
มาตรา ๔ ให้ยกเลิกอัตราโทษในมาตรา ๖ แห่งพระราชบัญญัติตัวอย่าง และให้ใช้อัตราโทษดังต่อไปนี้แทน
มาตรา ๖ ... “ต้องระวางโทษปรับไม่เกินสี่พันบาท”
มาตรา ๕ ให้นายกรัฐมนตรีรักษาการ
"""


def _ids(secs):
    return [s.section for s in secs]


def test_norm_sid():
    assert norm_sid("๔๓ ทวิ/๑") == "43ทวิ/1"
    assert norm_sid("๑๖๐ ตรี") == "160ตรี"


def test_main_act_headers_suffixes_repeal_and_end_marker():
    secs = split_sections(MAIN_ACT, doc_id="ex", act="ตัวอย่าง",
                          end_marker="^ผู้รับสนองพระบรมราชโองการ")
    # 5 is "(ยกเลิก)" -> no record; text after the sign-off is cut
    assert _ids(secs) == ["1", "2", "3", "3/1", "4ทวิ", "4ทวิ/1", "6"]
    assert "บทเฉพาะกาล" not in secs[-1].text


def test_wrapped_references_do_not_start_sections():
    secs = {s.section: s for s in split_sections(MAIN_ACT, doc_id="ex", act="ตัวอย่าง")}
    assert "และหน้าที่อื่น" in secs["2"].text      # "มาตรา ๓ (๑)" -> sub-clause lookahead
    assert "วรรคหนึ่ง" in secs["3"].text            # "มาตรา ๒ วรรคหนึ่ง" -> goes backwards
    assert "ฝ่าฝืนมาตรา ๓" in secs["6"].text        # mid-line reference


def test_amending_act_quote_tracking():
    secs = split_sections(AMENDING_ACT, doc_id="am", act="แก้ไข", amending=True)
    # "มาตรา ๖ ตรี/๓ แห่ง..." (wrapped instruction), "มาตรา ๖/๒" inside the quote and
    # the rate line "มาตรา ๖ ... “" must NOT become headers
    assert _ids(secs) == ["1", "2", "3", "4", "5"]
    by = {s.section: s for s in secs}
    assert "ห้ามมิให้ผู้ขับขี่ทำสิ่งตัวอย่าง" in by["3"].text
    assert "ต้องระวางโทษปรับไม่เกินสี่พันบาท" in by["4"].text


def test_regulation_unit():
    reg = "ข้อ ๑ ระเบียบนี้เรียกว่า ตัวอย่าง\nข้อ ๒ ให้ตัดคะแนนตามข้อ ๙ ดังนี้\n๒.๑ ตัด ๑ คะแนน\nข้อ ๓ จบ"
    secs = split_sections(reg, doc_id="reg", act="ระเบียบ", unit="ข้อ")
    assert _ids(secs) == ["1", "2", "3"]
    assert secs[1].label.startswith("ข้อ 2")
    assert "๒.๑ ตัด ๑ คะแนน" in secs[1].text
