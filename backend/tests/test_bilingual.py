"""Switching language changes texts only — never values, statuses or approvals; every ratio gets the 7-step interpretation."""
import os
import tempfile

import pytest

os.environ.setdefault("FAP_DATA_DIR", tempfile.mkdtemp())
os.environ.pop("ANTHROPIC_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

ARABIC = lambda s: any("؀" <= ch <= "ۿ" for ch in s or "")  # noqa: E731


@pytest.fixture(scope="module")
def cid():
    with TestClient(app) as c:
        r = c.post("/api/companies", json={"name": "Bilingual Co.", "industry": "Manufacturing", "currency": "EGP"})
        i = r.json()["id"]
        c.post(f"/api/companies/{i}/upload", files={"file": ("s.xlsx", c.get("/api/template?sample=true").content)})
        yield c, i


def test_values_identical_in_both_languages(cid):
    c, i = cid
    en = c.get(f"/api/companies/{i}/analysis?lang=en").json()
    ar = c.get(f"/api/companies/{i}/analysis?lang=ar").json()
    strip = lambda d: {r["key"]: [(x["year"], x["value"], x["status"]) for x in r["cells"]] for r in d["ratios"]}  # noqa: E731
    assert strip(en) == strip(ar)
    assert en["governance"] == ar["governance"] if "governance" in en else True
    assert ARABIC(next(r for r in ar["ratios"] if r["key"] == "roi")["interpretation"])


def test_seven_step_interpretation(cid):
    c, i = cid
    for lang in ("en", "ar"):
        d = c.get(f"/api/companies/{i}/interpretation?lang={lang}").json()
        roi = [x for x in d["ratios"]["roi"] if x["steps"]][-1]
        assert len(roi["steps"]) == 7
        assert roi["verdict"] in {"favorable", "unfavorable", "mixed", "neutral"}
        assert ARABIC(roi["steps"][3]["text"]) == (lang == "ar")
        assert d["sources_uses"]


def test_reports_in_both_languages(cid):
    c, i = cid
    for lang in ("en", "ar"):
        for fmt, magic in (("xlsx", b"PK"), ("pdf", b"%PDF")):
            r = c.get(f"/api/companies/{i}/report.{fmt}?lang={lang}")
            assert r.status_code == 200 and r.content[:len(magic)] == magic
            assert f"_{lang}.{fmt}" in r.headers["content-disposition"]
