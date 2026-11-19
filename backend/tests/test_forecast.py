"""Forecasting & planning — reproduced from Lectures 5–8 and the Q4 solution."""
from decimal import Decimal as D

import pytest

from app.engine.forecast import (BSLine, Hierarchy, ISLine, PositionInput, breakeven, cash_budget, forecast_position,
                                 percent_of_sales)


def lecture_position(growth, dps_growth, hierarchy, rounding=False):
    is_lines = [ISLine("Sales", D(3000), "revenue"), ISLine("COGS", D(2616), "expense"), ISLine("Depreciation", D(100), "expense")]
    bs = [BSLine("Cash", D(10), "A", True), BSLine("Debtors", D(375), "A", True), BSLine("Inventory", D(615), "A", True),
          BSLine("Net fixed assets", D(1000), "A", True), BSLine("Creditors", D(60), "L", True),
          BSLine("Short-term loan / N/P", D(110), "L", False, "st_debt"), BSLine("Accrued expenses", D(140), "L", True),
          BSLine("L.T. Bonds", D(754), "L", False, "lt_debt"), BSLine("Preferred shares", D(40), "E"),
          BSLine("Common shares", D(130), "E", False, "common"), BSLine("Retained earnings", D(766), "E", False, "re")]
    return forecast_position(PositionInput(is_lines, bs, D(88), D("0.4"), D(4), D(50), D("1.15"), D(58), growth, dps_growth,
                                           hierarchy, D(23), course_rounding=rounding))


def last(res):
    s = res["stages"][-1]
    bs = {r["name"]: r["value"] for r in s["balance_sheet"]}
    return s, bs


def test_lecture5_forecasted_position():
    res = lecture_position(D("0.10"), D("0.08"), [Hierarchy("st_debt", D("0.25"), D("0.08")), Hierarchy("lt_debt", D("0.25"), D("0.10")),
                                                  Hierarchy("common", D("0.5"))])
    first = res["stages"][0]
    assert first["is_summary"]["ebit"] == pytest.approx(312.4, abs=0.5)  # course: 312
    assert first["financing_need"] == pytest.approx(112, abs=1.5)  # course: 112
    assert res["converged"]
    s, bs = last(res)
    assert s["total_assets"] == pytest.approx(2200)
    assert s["is_summary"]["np"] == pytest.approx(131, abs=1.5)
    assert bs["Retained earnings"] == pytest.approx(827, abs=1.5)
    assert bs["Short-term loan / N/P"] == pytest.approx(140, abs=1.5)
    assert bs["L.T. Bonds"] == pytest.approx(784, abs=1.5)
    assert bs["Common shares"] == pytest.approx(189, abs=1.5)


def test_q4_forecasted_position():
    # Elnady: +16.25% sales; N/P 30% at 4.5% twice yearly (9%), bonds 30% at 11%, common 40% at LE 23; DPS 1.15 +12%
    res = lecture_position(D("0.1625"), D("0.12"), [Hierarchy("st_debt", D("0.30"), D("0.09")), Hierarchy("lt_debt", D("0.30"), D("0.11")),
                                                    Hierarchy("common", D("0.40"))])
    first = res["stages"][0]
    assert first["is_summary"]["ebit"] == pytest.approx(331, abs=1)
    assert first["is_summary"]["common_div"] == pytest.approx(64.4, abs=0.1)
    assert first["financing_need"] == pytest.approx(217, abs=2)
    s, bs = last(res)
    assert s["total_assets"] == pytest.approx(2325, abs=1.5)  # course 2326 (rounded lines)
    assert bs["Short-term loan / N/P"] == pytest.approx(179, abs=2)
    assert bs["L.T. Bonds"] == pytest.approx(823, abs=2)
    assert bs["Common shares"] == pytest.approx(222, abs=2)
    assert bs["Retained earnings"] == pytest.approx(830, abs=2)
    assert abs(s["financing_need"]) <= 0.5
    # EVA before / after (Q4): before = 117.6 − (88 + 4 + 58 + 10% × 766) ≈ −109
    assert res["actual"]["eva"] == pytest.approx(-109, abs=1)
    # after: NP ≈ 138 − (101 + 4 + 70 + 83) ≈ −120. The handwritten solution used 179 (the N/P balance) as NP and got −79.
    assert s["is_summary"]["eva"] == pytest.approx(-120, abs=3)


def test_course_rounding_mode_balances():
    res = lecture_position(D("0.10"), D("0.08"), [Hierarchy("st_debt", D("0.25"), D("0.08")), Hierarchy("lt_debt", D("0.25"), D("0.10")),
                                                  Hierarchy("common", D("0.5"))], rounding=True)
    assert res["converged"] and all(float(r["value"]).is_integer() for r in res["stages"][-1]["balance_sheet"])


def test_hierarchy_must_total_100():
    with pytest.raises(ValueError):
        lecture_position(D("0.1"), D(0), [Hierarchy("st_debt", D("0.5"), D("0.1"))])


def test_lecture6_percent_of_sales():
    bs = [BSLine("Cash", D(10), "A", True, category="bs.ca.cash"), BSLine("Debtors", D(90), "A", True, category="bs.ca.receivables"),
          BSLine("Inventory", D(200), "A", True, category="bs.ca.inventory"), BSLine("F.A", D(300), "A", True, category="bs.nca.ppe_net"),
          BSLine("Creditors", D(40), "L", True, category="bs.cl.payables"), BSLine("S.T loans", D(10), "L", False, "st_debt", "bs.cl.st_debt"),
          BSLine("Acc. Exp", D(50), "L", True, category="bs.cl.accrued"), BSLine("L.T. Bonds", D(150), "L", False, "lt_debt", "bs.ncl.bonds"),
          BSLine("O. Shares", D(50), "E", False, "common", "bs.eq.common"), BSLine("R/E", D(300), "E", False, "re", "bs.eq.retained")]
    r = percent_of_sales(bs, D(400), D(600), D("0.10"), D("0.6"))
    assert r["afn"] == pytest.approx(231) and r["afn_formula"] == pytest.approx(231)
    assert r["sustainable_sales"] == pytest.approx(412.955, abs=1e-3)
    assert r["ratios"]["current_ratio_before"] == pytest.approx(3.0)
    assert r["ratios"]["current_ratio_after"] == pytest.approx(450 / 376, abs=1e-3)  # 1.2 in the lecture
    assert r["ratios"]["debt_ratio_before"] == pytest.approx(250 / 600, abs=1e-3)
    assert r["ratios"]["debt_ratio_after"] == pytest.approx(526 / 900, abs=1e-3)  # 58%


def test_lecture8_breakeven():
    r = breakeven(D(100000), price=D(2), avc=D("1.5"), units=D(350000))
    assert r["bep_units"] == 200000 and r["operating_profit"] == pytest.approx(75000)
    r2 = breakeven(D(40), sales=D(100), vc=D(60))
    assert r2["bep_sales"] == pytest.approx(100) and r2["operating_profit"] == 0
    with pytest.raises(ValueError):
        breakeven(D(10), price=D(1), avc=D(2))


def test_lecture7_cash_budget():
    months = ["Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    sales = [D(x) for x in (300, 350, 250, 200, 250, 300, 350, 380)]
    other = [D(0), D(0), D(0), D(40), D(0), D(0), D(0), D(0)]
    pay = {"Purchases": [D(0), D(0)] + [D(x) for x in (100, 80, 100, 120, 140, 150)],
           "Salaries": [D(0), D(0)] + [D(x) for x in (80, 80, 90, 90, 95, 100)],
           "Overheads": [D(0), D(0)] + [D(50)] * 6,
           "Capital investment": [D(0), D(0)] + [D(x) for x in (0, 150, 20, 0, 0, 20)],
           "Dividends": [D(0), D(0)] + [D(x) for x in (0, 0, 50, 0, 0, 0)],
           "Taxes": [D(0), D(0)] + [D(x) for x in (30, 0, 0, 30, 0, 0)]}
    r = cash_budget(months, sales, D("0.10"), [D("0.9"), D("0.1")], other, pay, D(100), D(75), show_from=2)
    rows = {x["month"]: x for x in r["rows"]}
    assert rows["Jan"]["receipts"] == pytest.approx(335.5) and rows["Jan"]["surplus_deficit"] == pytest.approx(100.5)
    assert rows["Feb"]["receipts"] == pytest.approx(294) and rows["Feb"]["closing_balance"] == pytest.approx(109.5)
    assert rows["Mar"]["surplus_deficit"] == pytest.approx(-66)
    assert rows["Jun"]["receipts"] == pytest.approx(348.5)
