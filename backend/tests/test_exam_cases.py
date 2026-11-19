"""Reference tests reproduced from the course's solved examinations and lecture examples."""
from decimal import Decimal

import pytest

from app import assumptions as asm
from app.classify import suggest, post_pass
from app.engine import forecast
from app.engine.aggregate import AccountInput
from app.engine.analysis import Analysis
from app.engine.trends import cagr, pct_change, series_stats

D = Decimal


def acc(i, name, st, cat, vals, status="approved"):
    return AccountInput(i, name, st, cat, status, {y: D(str(v)) for y, v in vals.items()})


def analysis(accounts, years, additional=None, methodology="academic", overrides=None, approve_all=True):
    a = asm.defaults(methodology) | (overrides or {})
    st = {k: "accepted" for k in a} if approve_all else {}
    return Analysis(accounts, years, additional or {}, a, st, methodology=methodology)


def val(an, key, year):
    return an.ratio_cell(key, year)["value"]


# ---------------------------------------------------------------- Q1 (Skylight Inc.) — asset utilisation
@pytest.fixture
def q1():
    Y = 2023
    accs = [acc(1, "Cash and Equivalents", "BS", "bs.ca.cash", {Y: 100000}),
            acc(2, "AR", "BS", "bs.ca.receivables", {Y: 300000}),
            acc(3, "Inventory", "BS", "bs.ca.inventory", {Y: 400000}),
            acc(4, "Fixed Assets", "BS", "bs.nca.ppe_net", {Y: 1200000}),
            acc(5, "Equity", "BS", "bs.eq.common", {Y: 2000000}),
            acc(6, "Sales", "IS", "is.revenue", {Y: 5000000}),
            acc(7, "COGS", "IS", "is.cogs", {Y: 3750000})]
    return analysis(accs, [Y], {"credit_sales": {Y: D(4000000)}}), Y


def test_q1_asset_utilisation(q1):
    an, Y = q1
    assert an.books[Y].v("ta") == 2000000 and an.books[Y].v("ca") == 800000
    assert val(an, "tato", Y) == pytest.approx(2.5)
    assert val(an, "tato_credit", Y) == pytest.approx(2.0)
    assert val(an, "tato_cash", Y) == pytest.approx(0.5)
    assert val(an, "fato", Y) == pytest.approx(4.1667, abs=1e-4)
    assert val(an, "cato", Y) == pytest.approx(6.25)
    assert val(an, "cash_turnover", Y) == pytest.approx(50)
    assert val(an, "ar_turnover", Y) == pytest.approx(13.333, abs=1e-3)
    assert val(an, "acp", Y) == pytest.approx(27.0)
    assert val(an, "inventory_turnover", Y) == pytest.approx(9.375)
    assert val(an, "asp", Y) == pytest.approx(38.4)
    assert val(an, "liquidity_of_inventory", Y) == pytest.approx(65.4)
    assert an.ratio_cell("best_liquidity_measure", Y)["value"] == "Current ratio"


def test_q1_status_reflects_assumptions(q1):
    an, Y = q1
    assert an.ratio_cell("tato", Y)["status"] == "approved_assumption"  # uses asset_equity_basis
    assert an.ratio_cell("cato", Y)["status"] == "verified"
    assert an.ratio_cell("current_ratio", Y)["status"] == "needs_info"  # no current liabilities given in Q1


# ---------------------------------------------------------------- Q2 (Outlander) — ACP with credit sales assumed = sales
def test_q2_acp_all_sales_on_credit():
    Y = 2021
    accs = [acc(1, "Cash & marketable securities", "BS", "bs.ca.cash", {Y: 215000}),
            acc(2, "AR", "BS", "bs.ca.receivables", {Y: "149285.5"}),
            acc(3, "Inventory", "BS", "bs.ca.inventory", {Y: "485714.5"}),
            acc(4, "Current liabilities", "BS", "bs.cl.other", {Y: "242857.142857"}),
            acc(5, "Equity", "BS", "bs.eq.common", {Y: "607142.857143"}),
            acc(6, "Sales", "IS", "is.revenue", {Y: "3428573"}),
            acc(7, "COGS", "IS", "is.cogs", {Y: "2914287"})]
    an = analysis(accs, [Y])
    assert val(an, "current_ratio", Y) == pytest.approx(3.5, abs=1e-6)
    assert val(an, "quick_ratio", Y) == pytest.approx(1.5, abs=1e-6)
    assert val(an, "inventory_turnover", Y) == pytest.approx(6.0, abs=1e-3)
    assert val(an, "acp", Y) == pytest.approx(15.67, abs=0.01)
    assert any("all sales assumed on credit" in n for n in an.ratio_cell("acp", Y)["notes"])


# ---------------------------------------------------------------- Q3 (W. F. Bailey) — S&U, DuPont, EVA
@pytest.fixture
def q3():
    y1, y2 = 2021, 2022
    bs = [("Cash", "bs.ca.cash", 52000, 58500), ("Debtors", "bs.ca.receivables", 91000, 104000),
          ("Inventory", "bs.ca.inventory", 84500, 78000), ("Prepaid Expenses", "bs.ca.prepaid", 2600, 3900),
          ("Land", "bs.nca.land", 39000, 39000), ("Net Buildings", "bs.nca.ppe_net", 195000, 187200),
          ("Net Machinery & Equipment", "bs.nca.ppe_net", 78000, 97500),
          ("Creditors", "bs.cl.payables", 83200, 93600), ("Accrued Expenses", "bs.cl.accrued", 5200, 2600),
          ("Advanced Revenues", "bs.cl.advance_revenue", 1300, 3900), ("Loans (5 years)", "bs.ncl.lt_loans", 143000, 128700),
          ("Capital", "bs.eq.common", 234000, 234000), ("Retained Earnings", "bs.eq.retained", 75400, 105300),
          ("Total Assets", "bs.total.assets", 542100, 568100)]
    is_ = [("Sales", "is.revenue", 442000, 494000), ("COGS", "is.cogs", -254150, -291460),
           ("Selling Expenses", "is.opex.selling", 80080, 83330), ("General & Administrative Expenses", "is.opex.ga", 45240, 51090),
           ("Capital Losses", "is.other_expense", -12740, -11570), ("Tax", "is.tax", -12220, -13880),
           ("EBIT", "is.total.ebit", 49790, 56550), ("Net Profit", "is.total.net_profit", 37570, 42670)]
    accs = [acc(i, n, "BS", c, {y1: a, y2: b}) for i, (n, c, a, b) in enumerate(bs)]
    accs += [acc(100 + i, n, "IS", c, {y1: a, y2: b}) for i, (n, c, a, b) in enumerate(is_)]
    return analysis(accs, [y1, y2])


def test_q3_statements_reconcile(q3):
    assert q3.books[2021].v("ta") == 542100 and q3.books[2022].v("ta") == 568100
    assert q3.books[2021].v("ebit") == 49790 and q3.books[2022].v("np") == 42670
    assert not [c for c in q3.checks() if c["severity"] in ("error", "warning")]


def test_q3_sources_and_uses(q3):
    su = q3.sources_uses()[0]
    assert su["total_sources"] == 57200 and su["total_uses"] == 57200 and su["reconciled"]
    rows = {r["account"]: r for r in su["rows"]}
    assert rows["Cash"]["type"] == "use" and rows["Inventory"]["type"] == "source"
    assert rows["Net Buildings"]["type"] == "source" and rows["Loans (5 years)"]["type"] == "use"
    assert rows["Retained Earnings"]["pct"] == pytest.approx(0.5227, abs=1e-3)
    assert rows["Net Machinery & Equipment"]["pct"] == pytest.approx(0.3409, abs=1e-3)
    assert su["short_term_sources_pct"] == pytest.approx(0.341, abs=1e-3)
    assert su["short_term_uses_pct"] == pytest.approx(0.409, abs=1e-3)
    assert su["golden_rule_deviation"] == pytest.approx(0.068, abs=1e-3)
    assert su["internal_sources_pct"] == pytest.approx(0.773, abs=1e-3)
    assert su["external_sources_pct"] == pytest.approx(0.227, abs=1e-3)


def test_q3_dupont_and_eva(q3):
    assert val(q3, "oim", 2021) == pytest.approx(0.1126, abs=1e-4)
    assert val(q3, "oim", 2022) == pytest.approx(0.1144, abs=1e-4)
    assert val(q3, "tato", 2021) == pytest.approx(0.815, abs=1e-3)
    assert val(q3, "tato", 2022) == pytest.approx(0.8696, abs=1e-3)
    assert val(q3, "roi", 2021) == pytest.approx(0.09185, abs=2e-4)  # 9.177% in the solution (rounded factors)
    assert val(q3, "roi", 2022) == pytest.approx(0.09954, abs=2e-4)
    assert val(q3, "dupont_roi", 2022) == pytest.approx(val(q3, "roi", 2022), abs=1e-9)
    assert val(q3, "eva", 2021) == pytest.approx(30030)
    assert val(q3, "eva", 2022) == pytest.approx(32140)
    assert q3.ratio_cell("mva", 2022)["status"] == "needs_info"


# ---------------------------------------------------------------- Q5 — ROE = ROI + ROBF identity
def test_roe_equals_roi_plus_robf():
    Y = 2024
    accs = [acc(1, "Cash", "BS", "bs.ca.cash", {Y: 400}), acc(2, "Fixed", "BS", "bs.nca.ppe_net", {Y: 600}),
            acc(3, "Loans", "BS", "bs.ncl.lt_loans", {Y: 600}), acc(4, "Capital", "BS", "bs.eq.common", {Y: 400}),
            acc(5, "Sales", "IS", "is.revenue", {Y: 1000}), acc(6, "COGS", "IS", "is.cogs", {Y: 900}),
            acc(7, "Interest", "IS", "is.interest", {Y: 70})]
    an = analysis(accs, [Y])
    roi, robf, roe = val(an, "roi", Y), val(an, "robf", Y), val(an, "roe", Y)
    assert roi == pytest.approx(0.10)
    assert robf == pytest.approx((0.10 - 70 / 600) * (600 / 400))
    assert roe == pytest.approx(roi + robf)  # EBT/OE = 30/400
    assert roe == pytest.approx(0.075)


def test_q5_reverse_inventory_relationships():
    # Firm B: Inv TO = 360/ASP; ACP = AR×360/credit sales; liquidity of inventory = ACP + ASP
    Y = 2024
    cogs, inv = D(1636.3636), D(1000)  # ASP = 1000×360/1636.36 = 220 days
    accs = [acc(1, "AR", "BS", "bs.ca.receivables", {Y: 300}), acc(2, "Inventory", "BS", "bs.ca.inventory", {Y: inv}),
            acc(3, "Capital", "BS", "bs.eq.common", {Y: 1300}), acc(4, "Sales", "IS", "is.revenue", {Y: 4000}),
            acc(5, "COGS", "IS", "is.cogs", {Y: cogs})]
    an = analysis(accs, [Y], {"credit_sales": {Y: D(1800)}})
    assert val(an, "acp", Y) == pytest.approx(60)
    assert val(an, "asp", Y) == pytest.approx(220, abs=0.01)
    assert val(an, "liquidity_of_inventory", Y) == pytest.approx(280, abs=0.01)
    assert val(an, "inventory_turnover", Y) == pytest.approx(1.636, abs=1e-3)
    assert an.ratio_cell("best_liquidity_measure", Y)["value"] == "Current ratio"


# ---------------------------------------------------------------- Lecture 2 — Sources & uses (XYZ Co.) with gross FA + depreciation
def test_lecture2_sources_uses_with_contra_depreciation():
    a, b = 2023, 2024
    data = [("Cash", "bs.ca.cash", 10, 5), ("S.T. Invest", "bs.ca.st_investments", 25, 15), ("A/R", "bs.ca.receivables", 15, 20),
            ("Inventory", "bs.ca.inventory", 25, 30), ("Tot. Fixed Assets", "bs.nca.ppe_gross", 150, 180),
            ("(Depreciation)", "bs.nca.acc_depreciation", -40, -50), ("A/P", "bs.cl.payables", 10, 6), ("N/P", "bs.cl.notes_payable", 15, 10),
            ("S. T. Debts", "bs.cl.st_debt", 20, 24), ("L.T. Loans", "bs.ncl.lt_loans", 60, 70), ("Pref. Shares", "bs.eq.preferred", 10, 10),
            ("Ord. Shares", "bs.eq.common", 40, 40), ("R/E", "bs.eq.retained", 30, 40)]
    accs = [acc(i, n, "BS", c, {a: x, b: y}) for i, (n, c, x, y) in enumerate(data)]
    an = analysis(accs, [a, b])
    assert an.books[a].v("ta") == 185 and an.books[b].v("ta") == 200
    su = an.sources_uses()[0]
    assert su["total_sources"] == 49 and su["total_uses"] == 49
    rows = {r["account"]: r for r in su["rows"]}
    assert rows["(Depreciation)"]["type"] == "source" and rows["(Depreciation)"]["amount"] == 10
    assert rows["Tot. Fixed Assets"]["type"] == "use" and rows["Tot. Fixed Assets"]["amount"] == 30


# ---------------------------------------------------------------- Lectures 6 & 8
def test_lecture6_afn_and_sustainable_sales():
    assert forecast.afn(D(600), D(90), D(400), D(600), D("0.10"), D("0.6")) == 231
    assert float(forecast.sustainable_sales(D(600), D(90), D(400), D("0.10"), D("0.6"))) == pytest.approx(412.955, abs=1e-3)


def test_lecture8_breakeven():
    assert forecast.breakeven_units(D(100000), D(2), D("1.5")) == 200000
    assert forecast.breakeven_sales(D(40), D(60), D(100)) == 100
    assert forecast.breakeven_sales(D(40), D(36), D(60)) == 100


# ---------------------------------------------------------------- trends edge cases
def test_trend_edge_cases():
    assert pct_change(D(10), D(0)) == (None, "base_zero")
    v, flag = pct_change(D(-5), D(10))
    assert flag == "sign_change" and float(v) == -1.5
    v, flag = pct_change(D(5), D(-10))
    assert flag == "sign_change" and float(v) == 1.5
    assert cagr(D(-1), D(10), 3) == (None, "not_meaningful_non_positive")
    assert float(cagr(D(100), D(121), 2)[0]) == pytest.approx(0.1)
    s = series_stats({2020: D(100), 2021: None, 2022: D(121)})
    assert s["cagr"] == pytest.approx(0.1) and s["changes"][0]["flag"] == "missing"


def test_profit_to_loss_flagged():
    s = series_stats({2022: D(50), 2023: D(-20)})
    assert s["changes"][0]["flag"] == "sign_change" and s["cagr"] is None


# ---------------------------------------------------------------- classification
@pytest.mark.parametrize("name,st,expected", [
    ("Cash", "BS", "bs.ca.cash"), ("Debtors", "BS", "bs.ca.receivables"), ("Prepaid Expenses", "BS", "bs.ca.prepaid"),
    ("Net Buildings", "BS", "bs.nca.ppe_net"), ("Creditors", "BS", "bs.cl.payables"), ("Accrued Expenses", "BS", "bs.cl.accrued"),
    ("Advanced Revenues", "BS", "bs.cl.advance_revenue"), ("Loans (5 years)", "BS", "bs.ncl.lt_loans"),
    ("Retained Earnings", "BS", "bs.eq.retained"), ("Capital", "BS", "bs.eq.common"), ("Total Current Assets", "BS", "bs.total.ca"),
    ("Total Liabilities & O/E", "BS", "bs.total.le"), ("Total Liabilities", "BS", "bs.total.liabilities"),
    ("Pref. Shares", "BS", "bs.eq.preferred"), ("Notes payable", "BS", "bs.cl.notes_payable"), ("L.T. Bonds", "BS", "bs.ncl.bonds"),
    ("Sales", "IS", "is.revenue"), ("COGS", "IS", "is.cogs"), ("Capital Losses", "IS", "is.other_expense"),
    ("Other Revenues", "IS", "is.other_income"), ("Taxes (40%)", "IS", "is.tax"), ("EBIT", "IS", "is.total.ebit"),
    ("Gross Profit", "IS", "is.total.gross_profit"), ("Interest income", "IS", "is.finance_income"), ("Other expenses", "IS", "is.other_expense"),
    ("المخزون", "BS", "bs.ca.inventory"), ("الأرباح المحتجزة", "BS", "bs.eq.retained"),
])
def test_classifier(name, st, expected):
    assert suggest(name, st).category == expected


def test_ambiguous_investment_asks_question():
    s = suggest("Investments", "BS")
    assert s.question and s.confidence < 0.5 and len(s.options) == 2
    s2 = suggest("Investments", "BS", hint="Current")
    assert s2.category == "bs.ca.st_investments"


def test_hint_conflict_detected():
    s = suggest("Inventory", "BS", hint="Non-Current")
    assert s.hint_conflict and s.question


def test_gross_ppe_without_depreciation_becomes_net():
    items = [{"name": "Machinery", "statement": "BS", "suggestion": suggest("Machinery", "BS")}]
    post_pass(items)
    assert items[0]["suggestion"].category == "bs.nca.ppe_net"


# ---------------------------------------------------------------- governance: statuses & rejected classifications
def test_pending_classification_makes_results_provisional():
    Y = 2024
    accs = [acc(1, "Cash", "BS", "bs.ca.cash", {Y: 50}, status="pending"), acc(2, "Payables", "BS", "bs.cl.payables", {Y: 25}),
            acc(3, "Capital", "BS", "bs.eq.common", {Y: 25})]
    an = analysis(accs, [Y])
    c = an.ratio_cell("current_ratio", Y)
    assert c["value"] == 2 and c["status"] == "provisional"


def test_rejected_classification_excluded_and_unbalanced_is_invalid():
    Y = 2024
    accs = [acc(1, "Cash", "BS", "bs.ca.cash", {Y: 50}, status="rejected"), acc(2, "Payables", "BS", "bs.cl.payables", {Y: 25}),
            acc(3, "Capital", "BS", "bs.eq.common", {Y: 25})]
    an = analysis(accs, [Y])
    assert an.books[Y].v("ca") is None
    assert any(c["code"] == "BS_NOT_BALANCED" for c in an.checks())
    assert an.ratio_cell("current_ratio", Y)["status"] == "invalid"  # balance sheet does not balance


def test_assumption_changes_recalculate():
    a, b = 2023, 2024
    accs = [acc(1, "Inventory", "BS", "bs.ca.inventory", {a: 100, b: 300}), acc(2, "Capital", "BS", "bs.eq.common", {a: 100, b: 300}),
            acc(3, "Sales", "IS", "is.revenue", {a: 1000, b: 1200}), acc(4, "COGS", "IS", "is.cogs", {a: 800, b: 800})]
    closing = analysis(accs, [a, b])
    average = analysis(accs, [a, b], overrides={"inventory_basis": "average"})
    assert val(closing, "inventory_turnover", b) == pytest.approx(800 / 300)
    assert val(average, "inventory_turnover", b) == pytest.approx(800 / 200)
    # first year has no opening → fallback uses closing
    assert val(average, "inventory_turnover", a) == pytest.approx(8.0)
    excl = analysis(accs, [a, b], overrides={"inventory_basis": "average", "missing_opening_fallback": "exclude"})
    assert excl.ratio_cell("inventory_turnover", a)["status"] == "needs_info"
    impact = closing.assumption_impact("inventory_basis", ["closing", "average"])
    it = {o["option"]: next(r for r in o["ratios"] if r["ratio"] == "inventory_turnover")["value"] for o in impact}
    assert it["closing"] == pytest.approx(800 / 300) and it["average"] == pytest.approx(4.0)


def test_unapproved_assumption_is_provisional():
    Y = 2024
    accs = [acc(1, "Inventory", "BS", "bs.ca.inventory", {Y: 100}), acc(2, "Capital", "BS", "bs.eq.common", {Y: 100}),
            acc(3, "COGS", "IS", "is.cogs", {Y: 500})]
    an = analysis(accs, [Y], approve_all=False)
    assert an.ratio_cell("inventory_turnover", Y)["status"] == "provisional"
