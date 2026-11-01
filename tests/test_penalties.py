"""Calculator tests use a synthetic table (numbers invented), plus a sanity check of the real one."""
import pytest

from traffic_law.data.penalties import UnknownOffense, load_penalties, summarize

CSV = """offense_id,description,law,section,clause,penalty_section,fine_max,jail_max_months,points,source,verified,note
# comment rows are skipped
a,ความผิด A,,10,,50,1000,0,1,test,true,
b,ความผิด B,,11/1,(๑),50,4000,3,3,test,false,
c,ความผิด C,,12ทวิ/1,,,500,0,4,test,true,
d,ความผิด D,other-act,60,,,,,4,test,true,not in corpus
"""


@pytest.fixture
def rules(tmp_path):
    p = tmp_path / "pen.csv"
    p.write_text(CSV, encoding="utf-8")
    return load_penalties(p)


def test_load(rules):
    assert set(rules) == {"a", "b", "c", "d"}
    assert rules["b"].section == "11/1" and rules["b"].verified is False
    assert rules["a"].law == "land-traffic-2522"
    assert rules["d"].fine_max is None and rules["d"].jail_max_months is None


def test_summary_totals(rules):
    s = summarize(["a", "b"], rules, points_start=12, incident_cap=8)
    assert (s.total_fine_max, s.total_points, s.points_left) == (5000, 4, 8)
    assert s.any_jail and not s.license_suspension_risk and not s.points_capped
    assert s.unverified == ["b"]


def test_incident_cap_and_unknown_fine(rules):
    s = summarize(["a", "b", "c", "d", "a"], rules, points_start=12, incident_cap=8)
    assert s.offense_ids == ["a", "b", "c", "d"]
    assert s.points_raw == 12 and s.total_points == 8 and s.points_capped
    assert s.points_left == 4 and not s.license_suspension_risk
    assert s.fine_unknown == ["d"] and s.total_fine_max == 5500
    assert s.any_jail  # unknown jail counts as possible


def test_suspension_when_points_run_out(rules):
    s = summarize(["c"], rules, points_start=3, incident_cap=8)
    assert s.points_left == 0 and s.license_suspension_risk


def test_unknown_offense(rules):
    with pytest.raises(UnknownOffense):
        summarize(["zzz"], rules)


def test_bad_row_reports_line(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text(CSV.splitlines()[0] + "\nx,bad,,มาตรา 5,,,100,0,0,t,true,\n", encoding="utf-8")
    with pytest.raises(ValueError, match="line 2"):
        load_penalties(p)


def test_real_table_matches_regulation():
    """data/penalties.csv mirrors ข้อ ๑๑: 22 regulation items (12 x 1, 3 x 2, 3 x 3, 4 x 4 points).
    One item may span several rows (no_helmet / no_helmet_passenger share ข้อ 11.1(7))."""
    import re

    rules = load_penalties()
    items = {}
    for r in rules.values():
        ref = re.search(r"ข้อ (\d+\.\d+\(\d+\))", r.source).group(1)
        items.setdefault(ref, set()).add(r.points)
    assert all(len(p) == 1 for p in items.values())          # rows of one item agree on points
    by_pts = {p: sum(next(iter(v)) == p for v in items.values()) for p in (1, 2, 3, 4)}
    assert len(items) == 22 and by_pts == {1: 12, 2: 3, 3: 3, 4: 4}


def test_one_regulation_item_counts_its_points_once():
    """no_helmet + no_helmet_passenger share ข้อ 11.1(7): fines add up, points do not."""
    rules = load_penalties()
    s = summarize(["no_helmet", "no_helmet_passenger", "red_light"], rules, points_start=12, incident_cap=8)
    assert s.total_fine_max == 2000 + 4000 + 4000
    assert s.points_raw == 1 + 2 and s.points_left == 9
