"""Assumption Confirmation Engine — catalogue, data-driven detection, and impact simulation.

No assumption is hidden inside a formula: every ratio declares which assumption keys it reads, and
the engine reports, for each assumption, the value proposed, why, the supporting data, the
alternatives and the numerical impact of each alternative on the ratios that depend on it.
"""
from __future__ import annotations

from dataclasses import dataclass

COURSE = "Course methodology (lectures & solved exams)"


@dataclass
class AssumptionDef:
    key: str
    name: str
    name_ar: str
    options: list[dict]  # [{"value", "label", "impact"}]
    academic_default: str
    professional_default: str
    reason_academic: str
    reason_professional: str
    critical: bool = True


DEFS: list[AssumptionDef] = [
    AssumptionDef("inventory_basis", "Inventory balance for turnover / ASP", "أساس رصيد المخزون",
                  [{"value": "closing", "label": "Closing inventory", "impact": "Matches the lecture and Q1/Q5 solutions; sensitive to year-end stock levels."},
                   {"value": "average", "label": "Average inventory = (opening + closing) / 2", "impact": "Smooths year-end distortions; needs opening balances."},
                   {"value": "exclude", "label": "Exclude inventory ratios", "impact": "Inventory turnover, ASP and liquidity of inventory are not reported."}],
                  "closing", "average",
                  "Lecture 3 and the solved exams (Q1, Q5) divide COGS by the inventory balance at the reporting date.",
                  "Industry practice uses the average balance so that the numerator (a full-year flow) matches the denominator."),
    AssumptionDef("receivables_basis", "Receivables balance for turnover / ACP", "أساس رصيد المدينين",
                  [{"value": "closing", "label": "Closing receivables", "impact": "Course method (Q1, Q2, Q5)."},
                   {"value": "average", "label": "Average receivables", "impact": "Smooths seasonality; needs opening balances."},
                   {"value": "exclude", "label": "Exclude receivables ratios", "impact": "ACP and AR turnover not reported."}],
                  "closing", "average", "Lecture 3: ACP = (balance of AR × 360) / credit sales.",
                  "Average receivables better match full-year credit sales."),
    AssumptionDef("payables_basis", "Payables balance for turnover / payment period", "أساس رصيد الدائنين",
                  [{"value": "closing", "label": "Closing payables", "impact": "Consistent with course closing-balance practice."},
                   {"value": "average", "label": "Average payables", "impact": "Smooths year-end effects."}],
                  "closing", "average", "Not covered in the lectures; closing balance keeps it consistent with ACP/ASP.",
                  "Average payables match full-year purchases.", critical=False),
    AssumptionDef("asset_equity_basis", "Total assets / equity balance for returns & turnover", "أساس رصيد الأصول وحقوق الملكية",
                  [{"value": "closing", "label": "Closing balances", "impact": "Course method (Q3 DuPont uses year-end total assets)."},
                   {"value": "average", "label": "Average balances", "impact": "Reduces distortion when the asset base changes a lot during the year."}],
                  "closing", "average", "Q3 solution: TATO = sales / year-end total assets.", "Professional analysts average opening and closing balances."),
    AssumptionDef("missing_opening_fallback", "If an opening balance is missing for an average", "عند غياب الرصيد الافتتاحي",
                  [{"value": "use_closing", "label": "Use the closing balance for that year", "impact": "The ratio is reported but is not a true average for the first year."},
                   {"value": "exclude", "label": "Exclude the ratio for that year", "impact": "The first year shows 'requires information'."}],
                  "use_closing", "exclude", "Keeps the first year comparable with the course closing-balance method.",
                  "Avoids mixing averages with closing balances in one trend."),
    AssumptionDef("credit_sales_basis", "Credit sales when not provided", "المبيعات الآجلة عند عدم توفرها",
                  [{"value": "all_sales", "label": "Assume all sales are on credit", "impact": "Lecture 3 rule. Understates ACP and overstates AR turnover if there are cash sales."},
                   {"value": "exclude", "label": "Exclude credit-sales ratios", "impact": "ACP, AR turnover and the TATO split are not reported."}],
                  "all_sales", "all_sales", "Lecture 3, slide 3: 'If credit sales not given, assume all sales are on credit' (also the Q2 solution).",
                  "Common practice when credit sales are not disclosed; the limitation is shown on each affected ratio."),
    AssumptionDef("payables_driver", "Payables turnover driver", "أساس دوران الدائنين",
                  [{"value": "cogs", "label": "Cost of goods sold", "impact": "Always available; includes non-purchased costs (labour, overhead)."},
                   {"value": "credit_purchases", "label": "Credit purchases (Additional Information)", "impact": "Most accurate, but needs purchases data."}],
                  "cogs", "cogs", "Not covered in the lectures; COGS is the usual proxy.", "Credit purchases are preferred when disclosed.", critical=False),
    AssumptionDef("roi_definition", "ROI definition", "تعريف العائد على الاستثمار",
                  [{"value": "ebit_ta", "label": "EBIT / Total assets (course)", "impact": "Return before financing and tax; needed for ROBF and DuPont."},
                   {"value": "np_ta", "label": "Net profit / Total assets", "impact": "After-interest, after-tax return; breaks the ROE = ROI + ROBF identity."}],
                  "ebit_ta", "ebit_ta", "Lecture 3, slide 7: ROA/ROI = EBIT / Total assets; Q3 DuPont and Q5.",
                  "Same as the course; NP/TA is available separately as ROA (net)."),
    AssumptionDef("roe_definition", "ROE definition", "تعريف العائد على حقوق الملكية",
                  [{"value": "ebt_equity", "label": "EBT / Equity (course)", "impact": "Before-tax return; equals ROI + ROBF."},
                   {"value": "np_equity", "label": "Net profit / Equity", "impact": "After-tax return used by most investors; ROI + ROBF will no longer equal ROE."}],
                  "ebt_equity", "np_equity", "Lecture 3, slide 7: ROE = EBT / Equity, and ROE = ROI + ROBF (Q5).",
                  "Investors normally measure ROE on net profit."),
    AssumptionDef("bf_definition", "BF (borrowed funds) in ROBF", "تعريف الأموال المقترضة",
                  [{"value": "total_liabilities", "label": "All liabilities (total debts)", "impact": "Makes ROE = ROI + ROBF hold exactly, because TA = BF + OE (Lecture 1 accounting equation)."},
                   {"value": "interest_bearing", "label": "Interest-bearing debt only", "impact": "Isolates the cost of explicit borrowing; the identity no longer holds exactly."}],
                  "total_liabilities", "total_liabilities",
                  "Lecture 1, slide 31: Total assets = M/E + LTL + STL ('Debts'). With BF = all debts and OE = equity, ROI + ROBF = EBT/OE.",
                  "Same, to keep the decomposition exact."),
    AssumptionDef("oe_definition", "OE (owners' equity) in ROBF / ROE", "تعريف حقوق الملكية",
                  [{"value": "monetary_equity", "label": "Monetary equity (O/E + preferred shares)", "impact": "Lecture 1, slide 29 definition; keeps the balance-sheet identity."},
                   {"value": "common_equity", "label": "Common equity only", "impact": "Excludes preferred capital from the base."}],
                  "monetary_equity", "monetary_equity", "Lecture 1, slide 29: Monetary equity = O/E + preferred shares.", "Same."),
    AssumptionDef("finance_income_treatment", "Financial income", "معالجة الإيرادات التمويلية",
                  [{"value": "in_ebit", "label": "Include in EBIT", "impact": "Treats financial income as part of the return on assets."},
                   {"value": "below_ebit", "label": "Below EBIT (added after interest)", "impact": "EBIT reflects operations only; interest coverage is more conservative."}],
                  "in_ebit", "below_ebit", "The course income statement has no separate financial-income line; other revenues are added before net income (Lecture 9 assignment).",
                  "Professional analysis keeps financial income out of operating returns.", critical=False),
    AssumptionDef("days_in_year", "Days in the year", "عدد أيام السنة",
                  [{"value": "360", "label": "360 days (course)", "impact": "Matches all solved exams."},
                   {"value": "365", "label": "365 days", "impact": "Common in professional reports; days ratios rise by about 1.4%."}],
                  "360", "365", "Lecture 3 and every solved exam use 360 days.", "Calendar days are common in professional reporting.", critical=False),
    AssumptionDef("cash_ratio_definition", "Cash ratio definition", "تعريف نسبة النقدية",
                  [{"value": "academic", "label": "(CA − Inventory − AR − ST investments) / CL", "impact": "Course definition: 'cash in kind'."},
                   {"value": "professional", "label": "(Cash + ST investments) / CL", "impact": "Counts marketable securities as cash."}],
                  "academic", "professional", "Lecture 3, slide 2.", "Marketable securities are near-cash in practice.", critical=False),
    AssumptionDef("eva_opportunity_rate", "Opportunity cost of retained earnings (EVA)", "تكلفة الفرصة البديلة للأرباح المحتجزة",
                  [{"value": "0.10", "label": "10% (Q3 solution)", "impact": "As used in the solved exam."},
                   {"value": "0.15", "label": "15%", "impact": "Higher hurdle → lower EVA."},
                   {"value": "0.05", "label": "5%", "impact": "Lower hurdle → higher EVA."}],
                  "0.10", "0.10", "Q3 solution: EVA = NP − 10% × R/E (assumed bank rate / opportunity cost).",
                  "Should reflect the company's real cost of equity; confirm with the analyst.", critical=False),
]
BY_KEY = {d.key: d for d in DEFS}


def defaults(methodology: str) -> dict[str, str]:
    return {d.key: (d.professional_default if methodology == "professional" else d.academic_default) for d in DEFS}


def detect(methodology: str, data_facts: dict) -> list[dict]:
    """Return the assumption register proposals, with data-specific supporting evidence.

    data_facts: {"has_credit_sales": bool, "has_cash_sales": bool, "has_opening_inventory": bool,
                 "has_opening_receivables": bool, "has_credit_purchases": bool, "has_finance_income": bool,
                 "has_lt_or_st_investments": bool, "first_year": int, "years": [...]}
    """
    out = []
    for d in DEFS:
        proposed = d.professional_default if methodology == "professional" else d.academic_default
        reason = d.reason_professional if methodology == "professional" else d.reason_academic
        support = []
        relevant = True
        if d.key == "credit_sales_basis":
            if data_facts.get("has_credit_sales") or data_facts.get("has_cash_sales"):
                relevant = False
                support.append("Credit or cash sales were provided in Additional Information, so this assumption is not needed.")
            else:
                support.append("No credit-sales or cash-sales figures were provided.")
        if d.key in ("inventory_basis", "receivables_basis", "asset_equity_basis", "payables_basis"):
            missing = data_facts.get("missing_opening", [])
            fy = data_facts.get("first_year")
            if missing:
                support.append(f"No opening balances for the first year ({fy}) for: {', '.join(missing)}.")
            else:
                support.append(f"Opening balances are available for the first year ({fy}).")
            support.append(f"Years available: {', '.join(map(str, data_facts.get('years', [])))}.")
        if d.key == "missing_opening_fallback":
            if not data_facts.get("missing_opening"):
                support.append("All opening balances available — fallback will not be triggered.")
            else:
                support.append("Opening balances are missing for some first-year averages.")
        if d.key == "payables_driver":
            support.append("Credit purchases were provided." if data_facts.get("has_credit_purchases") else
                           "Credit purchases were not provided, so COGS is the only available driver.")
            if not data_facts.get("has_credit_purchases"):
                proposed = "cogs"
        if d.key == "finance_income_treatment":
            if not data_facts.get("has_finance_income"):
                relevant = False
                support.append("No financial-income line was found.")
        if d.key == "eva_opportunity_rate":
            support.append("The course solution assumes 10%. Replace it with the company's cost of equity if known.")
        out.append({"key": d.key, "name": d.name, "name_ar": d.name_ar, "proposed_value": proposed, "reason": reason,
                    "supporting_data": " ".join(support), "options": d.options, "critical": d.critical,
                    "relevant": relevant})
    return out
