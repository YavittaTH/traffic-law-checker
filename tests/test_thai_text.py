from traffic_law.thai_text import fix_aa_as_am, normalize_pdf_text, thai_to_arabic


def test_thai_digits():
    assert thai_to_arabic("มาตรา ๑๒๒/๑") == "มาตรา 122/1"


def test_gazette_split_sara_am_is_rejoined():
    assert normalize_pdf_text("ก าหนด ค าสั่ง").startswith("กำหนด คำสั่ง")


def test_tone_before_upper_vowel_is_reordered():
    assert normalize_pdf_text("แก้ไขเพ่ิมเติม") == "แก้ไขเพิ่มเติม"


def test_space_before_combining_mark_removed():
    assert normalize_pdf_text("ให้ไว ้ ณ วันที่") == "ให้ไว้ ณ วันที่"


def test_gazette_running_headers_dropped():
    txt = "หน้า ๕\nเล่ม ๑๓๙ ตอนที่ ๒๘ ก ราชกิจจานุเบกษา ๗ พฤษภาคม ๒๕๖๕\nมาตรา ๑ ข้อความ"
    assert normalize_pdf_text(txt) == "มาตรา ๑ ข้อความ"


def test_krisdika_aa_am_swap():
    # the real krisdika encoding: every า appears as ำ, every real ำ as " ำ"
    garbled = ("ส ำนักงำนคณะกรรมกำรกฤษฎีกำ มำตรำ ๔ ทำงเดินรถ " * 30).strip()
    fixed = fix_aa_as_am(garbled)
    assert fixed.startswith("สำนักงานคณะกรรมการกฤษฎีกา มาตรา ๔ ทางเดินรถ")


def test_krisdika_swap_leaves_normal_text_alone():
    normal = "กำหนด มาตรา ทางเดินรถ " * 50
    assert fix_aa_as_am(normal) == normal


def test_krisdika_header_and_notes_removed():
    txt = ("- ๒ - สำนักงานคณะกรรมการกฤษฎีกา\n"
           "มาตรา ๔/๑ ข้อความจริง*\n"
           "[คำว่า “ผู้บัญชาการตำรวจแห่งชาติ” แก้ไขเพิ่มเติมโดยมาตรา ๔ แห่ง\n"
           "พระราชบัญญัติจราจรทางบก (ฉบับที่ ๑๑) พ.ศ. ๒๕๕๙]\n"
           "มาตรา ๕ ต่อไป")
    out = normalize_pdf_text(txt)
    assert "สำนักงาน" not in out and "แก้ไขเพิ่มเติมโดย" not in out and "*" not in out
    assert "มาตรา ๔/๑ ข้อความจริง" in out and "มาตรา ๕ ต่อไป" in out
