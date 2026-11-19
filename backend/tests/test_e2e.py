"""End-to-end acceptance scenario through the HTTP API (spec: Final Acceptance Criteria)."""
import os
import tempfile

import pytest

os.environ["FAP_DATA_DIR"] = tempfile.mkdtemp()
os.environ.pop("ANTHROPIC_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_acceptance_scenario(client):
    # 1. create company
    r = client.post("/api/companies", json={"name": "Delta Manufacturing Co.", "industry": "Manufacturing", "currency": "EGP"})
    cid = r.json()["id"]
    # 2. template downloads
    assert client.get("/api/template").content[:2] == b"PK"
    sample = client.get("/api/template?sample=true").content
    # 3-4. upload five years
    r = client.post(f"/api/companies/{cid}/upload", files={"file": ("sample.xlsx", sample)})
    assert r.status_code == 200, r.text
    assert r.json()["summary"]["years"] == [2021, 2022, 2023, 2024, 2025]
    # 5. every value extracted
    rev = client.get(f"/api/companies/{cid}/review").json()
    vals = [x for x in rev["rows"] if x["parsed_value"] is not None and x["kind"] == "closing"]
    assert len(vals) == (19 + 13 + 10) * 5
    assert all(str(x["parsed_value"]).rstrip("0").rstrip(".") in x["value"].replace(",", "") or float(x["value"]) == x["parsed_value"] for x in vals)
    # 7. suggestions exist; ambiguous 'Investments' asks a question
    cls = client.get(f"/api/companies/{cid}/classifications").json()
    inv = next(c for c in cls if c["account"] == "Investments")
    assert inv["question"] and inv["status"] == "pending"
    # before decisions: results are provisional, approval blocked
    an = client.get(f"/api/companies/{cid}/analysis").json()
    cr = next(r for r in an["ratios"] if r["key"] == "current_ratio")
    assert {c["status"] for c in cr["cells"]} <= {"provisional", "invalid"}
    assert client.post(f"/api/companies/{cid}/approve").status_code == 409
    # 8. analyst decides: investments are short-term → totals reconcile; dependent ratios recalculated
    r = client.post(f"/api/classifications/{inv['account_id']}/decide", json={"action": "modify", "category": "bs.ca.st_investments",
                                                                          "note": "Treasury bills, < 3 months"}).json()
    assert any(i["ratio"] == "current_ratio" for i in r["impact"])
    for c in client.get(f"/api/companies/{cid}/classifications").json():
        if c["status"] == "pending":
            client.post(f"/api/classifications/{c['account_id']}/decide", json={"action": "approve"})
    # 9-10. assumptions
    ass = client.get(f"/api/companies/{cid}/assumptions").json()
    assert any(a["key"] == "inventory_basis" and a["impact"] for a in ass)
    for a in ass:
        client.post(f"/api/companies/{cid}/assumptions/{a['key']}", json={"action": "accept"})
    gov = client.get(f"/api/companies/{cid}").json()["governance"]
    assert gov["ready_for_approval"], gov
    # 11-12. ratios over all years, no checks failing
    an = client.get(f"/api/companies/{cid}/analysis").json()
    assert not [c for c in an["checks"] if c["severity"] == "error"]
    cr = next(r for r in an["ratios"] if r["key"] == "current_ratio")
    assert cr["cells"][0]["value"] == pytest.approx(890 / 350, abs=1e-5) and cr["cells"][0]["status"] == "verified"
    roe = next(r for r in an["ratios"] if r["key"] == "roe")
    assert roe["cells"][-1]["value"] == pytest.approx(316 / 1200, abs=1e-5)
    assert len(an["sources_uses"]) == 4 and all(s["reconciled"] for s in an["sources_uses"])
    # trace drill-down to original accounts
    t = client.get(f"/api/companies/{cid}/trace/current_ratio/2025").json()
    ca = next(i for i in t["inputs"] if i["key"] == "ca")
    assert {c["account"] for c in ca["detail"]["components"]} >= {"Cash at banks", "Investments", "Inventory"}
    # 13-14. AI review finds the planted patterns
    obs = client.get(f"/api/companies/{cid}/observations").json()
    keys = {o["key"] for o in obs}
    assert "ovr-np-ocf" in keys and "rel-cl-ca" in keys
    assert all(o["type"] in ("math_error", "accounting_inconsistency", "unusual_trend", "potential_risk", "hypothesis") for o in obs)
    # 15. executive evaluation + approval
    ev = client.get(f"/api/companies/{cid}/evaluation").json()
    assert ev["evaluation"]["areas"] and ev["approval_status"] == "ready_for_approval"
    assert client.post(f"/api/companies/{cid}/approve").status_code == 200
    assert client.get(f"/api/companies/{cid}/evaluation").json()["approval_status"] == "approved"
    # 16. exports
    x = client.get(f"/api/companies/{cid}/report.xlsx?years=2023,2024,2025")
    assert x.status_code == 200 and x.content[:2] == b"PK"
    p = client.get(f"/api/companies/{cid}/report.pdf")
    assert p.status_code == 200 and p.content[:4] == b"%PDF"
    # chat falls back to deterministic findings without credentials
    ch = client.post(f"/api/companies/{cid}/chat", json={"question": "Why is cash flow falling?"}).json()
    assert ch["ok"] is False and ch["fallback"]
    # audit trail recorded
    assert len(client.get(f"/api/companies/{cid}/audit").json()) > 10


def test_reupload_keeps_decisions_and_versions(client):
    cid = client.post("/api/companies", json={"name": "Re-upload Co", "currency": "EGP"}).json()["id"]
    sample = client.get("/api/template?sample=true").content
    client.post(f"/api/companies/{cid}/upload", files={"file": ("v1.xlsx", sample)})
    c0 = client.get(f"/api/companies/{cid}/classifications").json()[0]
    client.post(f"/api/classifications/{c0['account_id']}/decide", json={"action": "approve"})
    client.post(f"/api/companies/{cid}/upload", files={"file": ("v2.xlsx", sample)})
    ups = client.get(f"/api/companies/{cid}/uploads").json()
    assert [u["version"] for u in ups] == [2, 1] and ups[0]["active"]
    c1 = next(c for c in client.get(f"/api/companies/{cid}/classifications").json() if c["account_id"] == c0["account_id"])
    assert c1["status"] == "approved" and c1["carried_over"]


def test_bad_file_and_validation(client):
    cid = client.post("/api/companies", json={"name": "Bad Co", "currency": "EGP"}).json()["id"]
    assert client.post(f"/api/companies/{cid}/upload", files={"file": ("x.xlsx", b"not excel")}).status_code == 400
    from io import BytesIO
    from openpyxl import load_workbook
    from app.excel_template import build
    wb = load_workbook(BytesIO(build(sample=True)))
    ws = wb["Balance_Sheet"]
    ws.append(["1010", "Cash at banks", None, 2025, 999, "Current", "EGP", None])  # duplicate
    ws.append(["1099", "Mystery", None, 2025, "abc", None, "EGP", None])  # non-numeric
    ws.append(["1098", "Other thing", None, 2025, 5, None, "USD", None])  # currency mismatch
    bio = BytesIO()
    wb.save(bio)
    client.post(f"/api/companies/{cid}/upload", files={"file": ("bad.xlsx", bio.getvalue())})
    codes = {i["code"] for i in client.get(f"/api/companies/{cid}/review").json()["issues"]}
    assert {"DUPLICATE", "NON_NUMERIC", "CURRENCY_MISMATCH"} <= codes
    an = client.get(f"/api/companies/{cid}/analysis").json()
    cr = next(r for r in an["ratios"] if r["key"] == "current_ratio")
    assert cr["cells"][-1]["status"] == "invalid"  # unresolved error in 2025
    assert client.post(f"/api/companies/{cid}/approve").status_code == 409


def test_viewer_cannot_modify(client):
    users = client.get("/api/users").json()
    viewer = next(u for u in users if u["role"] == "viewer")
    r = client.post("/api/companies", json={"name": "X"}, headers={"X-User-Id": str(viewer["id"])})
    assert r.status_code == 403


def test_compare_and_methodology(client):
    ids = [c["id"] for c in client.get("/api/companies").json()][:2]
    r = client.get(f"/api/compare?ids={ids[0]},{ids[1]}").json()
    assert r["companies"] and "common_years" in r
    m = client.get("/api/methodology").json()
    assert any(x["indicator"].startswith("Return on borrowed funds") for x in m)


def test_forecasting_api(client):
    cid = client.post("/api/companies", json={"name": "Forecast Co", "currency": "EGP"}).json()["id"]
    client.post(f"/api/companies/{cid}/upload", files={"file": ("s.xlsx", client.get("/api/template?sample=true").content)})
    b = client.get(f"/api/companies/{cid}/forecast/base").json()
    assert b["year"] == 2025 and b["shares"] == 60 and b["dps"] == pytest.approx(143 / 60)
    roles = {l["role"] for l in b["bs_lines"]}
    assert {"st_debt", "lt_debt", "common", "re"} <= roles
    body = {**b, "growth": 0.1, "dps_growth": 0.05, "share_price": 19,
            "hierarchy": [{"target": "st_debt", "pct": 0.3, "rate": 0.12}, {"target": "lt_debt", "pct": 0.3, "rate": 0.14}, {"target": "common", "pct": 0.4}]}
    r = client.post(f"/api/companies/{cid}/forecast/position", json=body).json()
    assert r["converged"] and abs(r["stages"][-1]["financing_need"]) <= 0.5
    bad = client.post(f"/api/companies/{cid}/forecast/position", json={**body, "hierarchy": [{"target": "common", "pct": 0.5}]})
    assert bad.status_code == 400
    p = client.post(f"/api/companies/{cid}/forecast/percent-of-sales", json={**b, "s1": b["sales"], "s2": b["sales"] * 1.2}).json()
    assert p["afn"] == pytest.approx(p["afn_formula"], abs=1e-6)
    be = client.post("/api/forecast/breakeven", json={"fc": 700, "sales": 3050, "vc": 1900}).json()
    assert be["bep_sales"] == pytest.approx(700 / (1 - 1900 / 3050), abs=1e-3)
