"""Financial Methodology Database — generated from the same registry the engine executes,
so the documentation can never drift from the calculations."""
from __future__ import annotations

from . import assumptions as asm
from .engine.aggregate import CA_CATS, CL_CATS, EQ_CATS, LABELS, NCA_PLUS, NCL_CATS, SUM_DEFS
from .engine.ratios import RATIOS

COMPOSITE = {"ca": CA_CATS, "fa": NCA_PLUS + ["bs.nca.acc_depreciation"], "ta": CA_CATS + NCA_PLUS + ["bs.nca.acc_depreciation"],
             "cl": CL_CATS, "ncl": NCL_CATS, "tl": CL_CATS + NCL_CATS, "equity": EQ_CATS, "common_equity": EQ_CATS,
             "ibd": ["bs.cl.notes_payable", "bs.cl.st_debt", "bs.ncl.lt_loans", "bs.ncl.bonds"],
             "gp": ["is.revenue", "is.cogs"], "op_income": ["is.revenue", "is.cogs", "is.opex.*"],
             "ebit": ["is.revenue", "is.cogs", "is.opex.*", "is.other_income", "is.other_expense", "(is.finance_income per assumption)"],
             "ebt": ["EBIT", "is.interest"], "np": ["EBT", "is.tax"], "ocf": ["cf.total.operating or Σ cf.op.item"],
             "icf": ["cf.total.investing"], "fincf": ["cf.total.financing"], "fcf": ["OCF", "cf.inv.capex"],
             "credit_sales": ["Additional_Info: credit_sales (or sales − cash_sales; or assumption)"],
             "shares_outstanding": ["Additional_Info"], "share_price": ["Additional_Info"], "fixed_costs": ["Additional_Info"],
             "variable_costs": ["Additional_Info"], "credit_purchases": ["Additional_Info"]}

EXTRA = [
    {"category": "Sources & uses of money", "indicator": "Sources & Uses statement", "methodology": "academic",
     "formula": "Change = closing − opening. Asset ↑ = use, asset ↓ = source; liability/equity ↑ = source, ↓ = use; "
                "accumulated depreciation ↑ = source. Σ sources = Σ uses.",
     "required_accounts": "All balance-sheet accounts for two consecutive years", "classifications": "bs.* (subtotals excluded)",
     "interpretation": "Rank sources and uses by %, split short-/long-term (golden rule deviation = |ST sources% − ST uses%|) "
                       "and internal vs external finance.",
     "benchmarks": "Golden rule: short-term uses financed by short-term sources; long-term by long-term.",
     "assumptions": "Gross fixed assets and accumulated depreciation shown separately when available (Lecture 2).",
     "source": "Lecture 2 — Financial Analysis (XYZ Co. example, 49 = 49); Q3 solution (57,200; 6.8% deviation; 77.3% internal)",
     "application": "Explains where money came from and how it was used; tests financing discipline."},
    {"category": "Horizontal analysis", "indicator": "Absolute / % change, CAGR", "methodology": "professional",
     "formula": "Δ = current − previous; %Δ = Δ / |previous|; CAGR = (end/begin)^(1/n) − 1",
     "required_accounts": "Any line with ≥ 2 years", "classifications": "All",
     "interpretation": "Zero base → not meaningful; sign change → flagged; CAGR only when begin and end > 0.",
     "benchmarks": "Company's own history", "assumptions": "None", "source": "Specification §8 (not in the lectures)",
     "application": "Trend detection across 3–5+ years."},
    {"category": "Vertical analysis", "indicator": "Common-size statements", "methodology": "professional",
     "formula": "Balance-sheet item / total assets; income-statement item / sales", "required_accounts": "Total assets, sales",
     "classifications": "All", "interpretation": "Structure of assets, financing and costs.", "benchmarks": "Industry common-size if available",
     "assumptions": "None", "source": "Specification §9.2", "application": "Comparing structure across years and companies."},
    {"category": "Forecasting", "indicator": "Financial sources needed (% of sales)", "methodology": "academic",
     "formula": "AFN = A/S1·ΔS − L/S1·ΔS − P·S2·(1 − D)", "required_accounts": "Spontaneous assets & liabilities, sales, margin, payout",
     "classifications": "Items with a direct relation to sales", "interpretation": "Positive = external finance needed (apply financial hierarchy).",
     "benchmarks": "—", "assumptions": "Spontaneous items move proportionally with sales", "source": "Lecture 6 — Percentage of Sales (231; S2 = 413)",
     "application": "Planning growth financing."},
    {"category": "Forecasting", "indicator": "Forecasted financial position", "methodology": "academic",
     "formula": "Stage 1: grow sales-related IS and BS items by (1 + g); Stage 2: finance the gap per financial hierarchy; iterate for new interest and dividends until balanced.",
     "required_accounts": "Full IS and BS", "classifications": "All", "interpretation": "Determines required financing and its cost.",
     "benchmarks": "—", "assumptions": "Hierarchy %, interest rates, share price, DPS growth", "source": "Lecture 5; Q4 solution",
     "application": "Budgeting future financing."},
    {"category": "Planning & control", "indicator": "Break-even (units & monetary)", "methodology": "academic",
     "formula": "Q = FC / (P − AVC); Monetary BEP = TFC / (1 − VC / Sales)", "required_accounts": "Fixed and variable costs (Additional_Info)",
     "classifications": "—", "interpretation": "High fixed costs = high operating leverage: small sales changes → large profit changes.",
     "benchmarks": "—", "assumptions": "Linear cost behaviour", "source": "Lecture 8 — Break-even & Operating Leverage",
     "application": "Profit planning and risk of operating leverage."},
    {"category": "Planning & control", "indicator": "Cash-flow forecast (budget)", "methodology": "academic",
     "formula": "Receipts (cash sales + collections by credit pattern + asset sales) − payments; compare with minimum cash → surplus/deficit",
     "required_accounts": "Monthly sales, collection pattern, expenditures", "classifications": "—",
     "interpretation": "Deficit months need short-term finance.", "benchmarks": "Minimum cash balance",
     "assumptions": "Collection pattern (e.g. 10% cash, 90% credit: 90% after 1 month, 10% after 2)", "source": "Lecture 7",
     "application": "Short-term financial planning (not computed from annual statements)."},
]


def _req(inputs):
    out, cats = [], set()
    for k in inputs:
        out.append(LABELS.get(k, k))
        if k in SUM_DEFS:
            cats |= set(SUM_DEFS[k][1])
        else:
            cats |= set(COMPOSITE.get(k, []))
    return ", ".join(out), ", ".join(sorted(cats))


def build() -> list[dict]:
    rows = []
    for r in RATIOS:
        req, cats = _req(r.inputs)
        ass = [f"{asm.BY_KEY[a].name}" for a in r.assumptions if a in asm.BY_KEY]
        rows.append({"category": r.category, "indicator": r.name_en, "indicator_ar": r.name_ar, "key": r.key, "methodology": r.methodology,
                     "formula": r.formula, "required_accounts": req, "classifications": cats,
                     "calculation": "Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.",
                     "interpretation": r.interpret.replace("{v}", "X") + (" Higher is better." if r.higher_is_better else
                                                                          " Lower is better." if r.higher_is_better is False else ""),
                     "benchmarks": "Configurable per industry / company; otherwise historical trend (limitation stated).",
                     "assumptions": "; ".join(ass) or "None", "source": r.source,
                     "application": r.action_if_weak or "Monitoring and comparison over time."})
    return rows + EXTRA


def markdown() -> str:
    lines = ["# Financial Methodology Database", "",
             "Generated from the calculation engine's own registry (`backend/app/engine/ratios.py`) — the documentation and the code are the same source.",
             "", "**Academic** = lectures & solved exams (default). **Professional** = additional industry-standard methods. **Both** = identical.", "",
             "## Documented differences between academic and professional formulas", "",
             "| Topic | Academic (course) | Professional | Where configured |", "|---|---|---|---|",
             "| ROE | EBT / Equity (Lecture 3, slide 7) — so ROE = ROI + ROBF holds | Net profit / Equity | Assumption `roe_definition` |",
             "| ROI / ROA | EBIT / Total assets | NP / Total assets shown separately as ROA (net) | `roi_definition` |",
             "| Balances | Closing balances (Q1, Q3, Q5) | Average (opening + closing)/2 | `inventory_basis`, `receivables_basis`, `asset_equity_basis` |",
             "| Days | 360 | 365 | `days_in_year` |",
             "| Cash ratio | (CA − Inv − AR − ST inv) / CL | (Cash + ST inv) / CL | `cash_ratio_definition` |",
             "| OIM | EBIT / Sales (Q3 DuPont) | Operating profit before non-operating items / Sales (separate ratio) | Both shown |",
             "| Operating cycle | 'Liquidity of inventory' = ASP + ACP | CCC = ASP + ACP − payment period | Both shown (professional only adds CCC) |",
             "| EVA | NP − (I + PS div + CS div + r × R/E), r = 10% in Q3 | NOPAT − WACC × capital (not implemented: needs WACC) | `eva_opportunity_rate` |",
             "| ROBF variables | BF = total debts, OE = monetary equity (Lecture 1 slides 29 & 31) | BF = interest-bearing debt | `bf_definition`, `oe_definition` |",
             "", "## Indicators", ""]
    for r in build():
        lines += [f"### {r['indicator']}" + (f" — {r['indicator_ar']}" if r.get("indicator_ar") else ""), "",
                  f"- **Category:** {r['category']} · **Methodology:** {r['methodology']}",
                  f"- **Formula:** {r['formula']}",
                  f"- **Required accounts:** {r['required_accounts']}",
                  f"- **Account classifications:** {r['classifications']}",
                  f"- **Calculation:** {r.get('calculation', '—')}",
                  f"- **Interpretation:** {r['interpretation']}",
                  f"- **Benchmarks:** {r['benchmarks']}",
                  f"- **Assumptions:** {r['assumptions']}",
                  f"- **Source:** {r['source']}",
                  f"- **Practical application:** {r['application']}", ""]
    return "\n".join(lines)
