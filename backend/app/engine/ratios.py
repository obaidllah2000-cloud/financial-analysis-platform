"""Ratio registry — deterministic formulas with full metadata.

Every ratio declares: methodology (academic = course lectures/solved exams, professional = industry
practice, both = identical in both), the aggregates it reads, the assumptions it depends on, its
academic source, and an interpretation template. `compute(ctx)` returns (value, trace-inputs, note).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Callable

from .num import div

SRC_L3 = "Lecture 3 — Financial Ratios"
SRC_L1 = "Lecture 1 — Financial Management"


@dataclass
class Ratio:
    key: str
    name_en: str
    name_ar: str
    category: str  # liquidity | debt | activity | profitability | dupont | market | cashflow | breakeven
    methodology: str  # academic | professional | both
    formula: str
    unit: str  # x | % | days | ccy | text
    higher_is_better: bool | None
    inputs: list[str]
    compute: Callable
    source: str = ""
    assumptions: list[str] = field(default_factory=list)
    interpret: str = ""
    action_if_weak: str = ""
    critical: bool = False  # shown in the executive summary


class Ctx:
    """Calculation context for one year."""

    def __init__(self, year, book, prev_book, opening_book, assumptions: dict[str, str]):
        self.year, self.b, self.prev, self.open, self.a = year, book, prev_book, opening_book, assumptions
        self.used: dict[str, Decimal | None] = {}
        self.notes: list[str] = []
        self.assumptions_used: set[str] = set()
        self.excluded = False

    def v(self, key):
        val = self.b.v(key)
        self.used[key] = val
        return val

    def days(self):
        self.assumptions_used.add("days_in_year")
        return Decimal(self.a.get("days_in_year", "360"))

    def opening_of(self, key):
        if self.prev is not None and self.prev.v(key) is not None:
            return self.prev.v(key), "prior-year closing"
        if self.open is not None and self.open.v(key) is not None:
            return self.open.v(key), "Opening Balances sheet"
        return None, None

    def bal(self, key, assumption_key):
        """Closing or average balance depending on the analyst-approved assumption."""
        self.assumptions_used.add(assumption_key)
        basis = self.a.get(assumption_key, "closing")
        close = self.v(key)
        if basis == "exclude":
            self.notes.append(f"{key}: excluded by analyst assumption")
            self.excluded = True
            return None
        if basis != "average" or close is None:
            return close
        op, src = self.opening_of(key)
        if op is None:
            self.assumptions_used.add("missing_opening_fallback")
            fb = self.a.get("missing_opening_fallback", "use_closing")
            if fb == "use_closing":
                self.notes.append(f"Average {key}: no opening balance for {self.year}; closing balance used (approved fallback).")
                return close
            self.notes.append(f"Average {key}: no opening balance for {self.year}; ratio excluded (approved fallback).")
            self.excluded = True
            return None
        avg = (op + close) / 2
        self.used[f"opening_{key}"] = op
        self.used[f"avg_{key}"] = avg
        self.notes.append(f"Average {key} = ({float(op):,.2f} [{src}] + {float(close):,.2f}) / 2")
        return avg

    def credit_sales(self):
        cs = self.b.v("credit_sales")
        if cs is not None:
            self.used["credit_sales"] = cs
            return cs
        sales = self.v("sales")
        cash_sales = self.b.v("cash_sales")
        if cash_sales is not None and sales is not None:
            self.used["cash_sales"] = cash_sales
            self.notes.append("Credit sales = sales − cash sales (Additional Information).")
            return sales - cash_sales
        self.assumptions_used.add("credit_sales_basis")
        if self.a.get("credit_sales_basis", "all_sales") == "all_sales":
            self.notes.append("Credit sales not provided: all sales assumed on credit (Lecture 3 rule).")
            return sales
        self.excluded = True
        self.notes.append("Credit sales not provided and the analyst chose to exclude credit-sales ratios.")
        return None

    def bf(self):
        self.assumptions_used.add("bf_definition")
        return self.v("ibd") if self.a.get("bf_definition", "total_liabilities") == "interest_bearing" else self.v("tl")

    def oe(self):
        self.assumptions_used.add("oe_definition")
        return self.v("common_equity") if self.a.get("oe_definition", "monetary_equity") == "common_equity" else self.v("equity")


def _sub(a, b):
    return None if a is None or b is None else a - b


def _add(*xs):
    return None if any(x is None for x in xs) else sum(xs)


# ------------------------------------------------------------------ formulas
def r_current(c): return div(c.v("ca"), c.v("cl"))
def r_quick(c): return div(_sub(c.v("ca"), c.v("inventory") or Decimal(0)), c.v("cl"))


def r_cash(c):
    c.assumptions_used.add("cash_ratio_definition")
    if c.a.get("cash_ratio_definition", "academic") == "academic":
        ca = c.v("ca")
        if ca is None:
            return None
        num = ca - (c.v("inventory") or 0) - (c.v("ar") or 0) - (c.v("st_inv") or 0)
        return div(num, c.v("cl"))
    return div(_add(c.v("cash") or Decimal(0), c.v("st_inv") or Decimal(0)), c.v("cl"))


def r_wc(c): return _sub(c.v("ca"), c.v("cl"))
def r_acp(c):
    ar = c.bal("ar", "receivables_basis")
    return div(None if ar is None else ar * c.days(), c.credit_sales())
def r_asp(c):
    inv = c.bal("inventory", "inventory_basis")
    return div(None if inv is None else inv * c.days(), c.v("cogs"))
def r_liq_inv(c): return _add(r_acp(c), r_asp(c))


def r_best_liquidity(c):
    acp, li = r_acp(c), r_liq_inv(c)
    if acp is None or li is None:
        return None
    if li < 360:
        return "Current ratio"
    if acp < 360:
        return "Quick ratio"
    return "Cash ratio"


def r_debt(c): return div(c.v("tl"), c.v("ta"))
def r_de(c): return div(c.v("tl"), c.v("equity"))
def r_csr(c): return div(c.v("ncl"), _add(c.v("ncl"), c.v("equity")))
def r_icr(c): return div(c.v("ebit"), c.v("interest"))
def r_eq_ratio(c): return div(c.v("equity"), c.v("ta"))
def r_em(c): return div(c.bal("ta", "asset_equity_basis"), c.bal("equity", "asset_equity_basis"))
def r_ltd(c): return div(c.v("ncl"), c.v("ta"))
def r_tato(c): return div(c.v("sales"), c.bal("ta", "asset_equity_basis"))
def r_tato_credit(c): return div(c.credit_sales(), c.v("ta"))
def r_tato_cash(c):
    cs = c.credit_sales()
    return div(_sub(c.v("sales"), cs), c.v("ta"))
def r_fato(c): return div(c.v("sales"), c.v("fa"))
def r_cato(c): return div(c.v("sales"), c.v("ca"))
def r_cash_to(c): return div(c.v("sales"), c.v("cash"))
def r_ar_to(c): return div(c.credit_sales(), c.bal("ar", "receivables_basis"))
def r_inv_to(c): return div(c.v("cogs"), c.bal("inventory", "inventory_basis"))


def _purch(c):
    c.assumptions_used.add("payables_driver")
    if c.a.get("payables_driver", "cogs") == "credit_purchases":
        p = c.b.v("credit_purchases")
        c.used["credit_purchases"] = p
        if p is None:
            c.notes.append("Credit purchases selected but not provided in Additional Information.")
        return p
    return c.v("cogs")


def r_ap_to(c): return div(_purch(c), c.bal("ap", "payables_basis"))
def r_app(c):
    ap = c.bal("ap", "payables_basis")
    return div(None if ap is None else ap * c.days(), _purch(c))
def r_ccc(c): return _sub(r_liq_inv(c), r_app(c))
def r_gpm(c): return div(c.v("gp"), c.v("sales"))
def r_oim(c): return div(c.v("ebit"), c.v("sales"))
def r_opm(c): return div(c.v("op_income"), c.v("sales"))
def r_nim(c): return div(c.v("np"), c.v("sales"))


def r_roi(c):
    c.assumptions_used.add("roi_definition")
    num = c.v("ebit") if c.a.get("roi_definition", "ebit_ta") == "ebit_ta" else c.v("np")
    return div(num, c.bal("ta", "asset_equity_basis"))


def r_roe(c):
    c.assumptions_used.add("roe_definition")
    num = c.v("ebt") if c.a.get("roe_definition", "ebt_equity") == "ebt_equity" else c.v("np")
    return div(num, c.bal("equity", "asset_equity_basis"))


def r_robf(c):
    roi, bf, oe, i = r_roi(c), c.bf(), c.oe(), c.v("interest")
    if None in (roi, bf, oe) or bf == 0 or oe == 0:
        return None
    return (roi - (i or Decimal(0)) / bf) * (bf / oe)


def r_roe_check(c):
    roi, robf = r_roi(c), r_robf(c)
    return _add(roi, robf)


def r_roa(c): return div(c.v("np"), c.bal("ta", "asset_equity_basis"))
def r_roce(c): return div(c.v("ebit"), _sub(c.v("ta"), c.v("cl")))
def r_dupont_check(c): return None if r_oim(c) is None or r_tato(c) is None else r_oim(c) * r_tato(c)


def r_mva(c):
    s, p, oe = c.v("shares_outstanding"), c.v("share_price"), c.v("equity")
    return None if None in (s, p, oe) else s * p - oe


def r_eva(c):
    c.assumptions_used.add("eva_opportunity_rate")
    rate = Decimal(c.a.get("eva_opportunity_rate", "0.10"))
    np_, re_ = c.v("np"), c.v("retained")
    if np_ is None:
        return None
    cost = (c.v("interest") or 0) + (c.v("pref_div") or 0) + (c.v("common_div") or 0) + rate * (re_ or 0)
    return np_ - cost


def r_bvps(c): return div(c.v("equity"), c.v("shares_outstanding"))
def r_eps(c): return div(_sub(c.v("np"), c.v("pref_div") or Decimal(0)), c.v("shares_outstanding"))
def r_ocf(c): return c.v("ocf")
def r_icf(c): return c.v("icf")
def r_fincf(c): return c.v("fincf")
def r_fcf(c): return c.v("fcf")
def r_ocf_ratio(c): return div(c.v("ocf"), c.v("cl"))
def r_ocf_np(c): return div(c.v("ocf"), c.v("np"))
def r_ocf_debt(c): return div(c.v("ocf"), c.v("tl"))


def r_bep(c):
    fc, vc, s = c.v("fixed_costs"), c.v("variable_costs"), c.v("sales")
    if None in (fc, vc, s) or s == 0:
        return None
    cm = 1 - vc / s
    return div(fc, cm) if cm > 0 else None


def r_mos(c):
    b, s = r_bep(c), c.v("sales")
    return div(_sub(s, b), s)


def r_dol(c):
    fc, vc, s = c.v("fixed_costs"), c.v("variable_costs"), c.v("sales")
    if None in (fc, vc, s):
        return None
    return div(s - vc, s - vc - fc)


R = Ratio
RATIOS: list[Ratio] = [
    # ---------------- Liquidity
    R("current_ratio", "Current ratio", "نسبة التداول", "liquidity", "both", "Current assets / Current liabilities", "x", True,
      ["ca", "cl"], r_current, SRC_L3 + ", slide 2",
      interpret="Every 1 unit of current liabilities is covered by {v} units of current assets.",
      action_if_weak="Lengthen debt maturities, convert short-term borrowing to long-term, or build current assets from retained profit.", critical=True),
    R("quick_ratio", "Quick (acid-test) ratio", "نسبة السيولة السريعة", "liquidity", "both", "(Current assets − Inventory) / Current liabilities", "x", True,
      ["ca", "inventory", "cl"], r_quick, SRC_L3 + ", slide 2",
      interpret="Excluding inventory, every 1 unit of current liabilities is covered by {v} units of liquid assets.",
      action_if_weak="Reduce dependence on inventory to meet obligations; accelerate collections.", critical=True),
    R("cash_ratio", "Cash ratio", "نسبة النقدية", "liquidity", "both", "Academic: (CA − Inventory − AR − ST investments) / CL · Professional: (Cash + ST investments) / CL", "x", True,
      ["ca", "inventory", "ar", "st_inv", "cash", "cl"], r_cash, SRC_L3 + ", slide 2", ["cash_ratio_definition"],
      interpret="Cash-in-kind covers {v} of current liabilities."),
    R("working_capital", "Working capital", "رأس المال العامل", "liquidity", "both", "Current assets − Current liabilities", "ccy", True,
      ["ca", "cl"], r_wc, SRC_L1 + ", slide 13", interpret="Net short-term resources available: {v}."),
    R("acp", "Average collection period (Liquidity of AR)", "متوسط فترة التحصيل", "liquidity", "academic", "(AR × 360) / Credit sales", "days", False,
      ["ar", "credit_sales", "sales"], r_acp, SRC_L3 + ", slide 3; Q1 & Q2 solutions", ["receivables_basis", "credit_sales_basis", "days_in_year"],
      interpret="Receivables are collected on average every {v} days.",
      action_if_weak="Tighten credit terms, offer early-payment discounts, review overdue customers."),
    R("asp", "Average selling period (inventory days)", "متوسط فترة البيع", "liquidity", "academic", "(Inventory × 360) / COGS", "days", False,
      ["inventory", "cogs"], r_asp, SRC_L3 + ", slide 3; Q1 & Q5 solutions", ["inventory_basis", "days_in_year"],
      interpret="Inventory is sold on average every {v} days.",
      action_if_weak="Review slow-moving items, align purchasing with demand."),
    R("liquidity_of_inventory", "Liquidity of inventory (operating cycle)", "سيولة المخزون (الدورة التشغيلية)", "liquidity", "academic", "ASP + ACP", "days", False,
      ["inventory", "cogs", "ar", "credit_sales"], r_liq_inv, SRC_L3 + ", slide 3; Q1 & Q5 solutions", ["inventory_basis", "receivables_basis", "credit_sales_basis", "days_in_year"],
      interpret="It takes {v} days to sell inventory and collect the cash. The larger it is, the more cash is needed to finance operations."),
    R("best_liquidity_measure", "Best measure of liquidity (course rule)", "أفضل مقياس للسيولة", "liquidity", "academic",
      "If ACP+ASP < 360 → current ratio; if ACP < 360 but ACP+ASP ≥ 360 → quick ratio; if ACP ≥ 360 → cash ratio", "text", None,
      ["ar", "inventory", "cogs", "credit_sales"], r_best_liquidity, SRC_L3 + ", slide 4; Q5 solution", ["inventory_basis", "receivables_basis", "credit_sales_basis", "days_in_year"],
      interpret="{v} is the most reliable liquidity measure for this year, because of how quickly receivables and inventory turn into cash."),
    # ---------------- Debt management / solvency
    R("debt_ratio", "Debt ratio", "نسبة المديونية", "debt", "both", "Total debts / Total assets", "%", False, ["tl", "ta"], r_debt, SRC_L3 + ", slide 5",
      interpret="{v} of assets are financed by debt. The higher the ratio, the riskier the company.",
      action_if_weak="Retain more earnings or raise equity before adding new debt.", critical=True),
    R("debt_equity", "Debt / equity", "الديون إلى حقوق الملكية", "debt", "both", "Total debts / Equity", "x", False, ["tl", "equity"], r_de, SRC_L3 + ", slide 5",
      interpret="There are {v} units of debt for every unit of equity."),
    R("capital_structure_ratio", "Capital structure ratio (CSR)", "نسبة هيكل رأس المال", "debt", "academic", "LTL / (LTL + ME)", "%", False,
      ["ncl", "equity"], r_csr, SRC_L3 + ", slide 5", interpret="{v} of long-term capital comes from long-term debt."),
    R("interest_coverage", "Interest coverage", "معدل تغطية الفوائد", "debt", "both", "EBIT / Interest", "x", True, ["ebit", "interest"], r_icr, SRC_L3 + ", slide 5",
      interpret="EBIT covers interest {v} times.", action_if_weak="Reduce interest-bearing debt or refinance at lower cost.", critical=True),
    R("equity_ratio", "Equity ratio", "نسبة الملكية", "debt", "professional", "Equity / Total assets", "%", True, ["equity", "ta"], r_eq_ratio,
      "Professional (complement of the debt ratio)", interpret="{v} of assets are financed by owners."),
    R("financial_leverage", "Financial leverage (equity multiplier)", "الرافعة المالية (مضاعف الملكية)", "debt", "professional", "Total assets / Equity", "x", None,
      ["ta", "equity"], r_em, "Professional (DuPont 3-step)", ["asset_equity_basis"], interpret="Each unit of equity supports {v} units of assets."),
    R("lt_debt_ratio", "Long-term debt ratio", "نسبة الديون طويلة الأجل", "debt", "professional", "LTL / Total assets", "%", False, ["ncl", "ta"], r_ltd,
      "Professional", interpret="{v} of assets are financed by long-term liabilities."),
    # ---------------- Activity / efficiency
    R("tato", "Total assets turnover (TATO)", "معدل دوران الأصول", "activity", "both", "Sales / Total assets", "x", True, ["sales", "ta"], r_tato,
      SRC_L3 + ", slide 6; Q1 & Q3 solutions", ["asset_equity_basis"],
      interpret="Every unit of total assets generates {v} units of sales.",
      action_if_weak="Dispose of idle assets or grow sales on the existing asset base.", critical=True),
    R("tato_credit", "TATO — credit sales", "معدل دوران الأصول — المبيعات الآجلة", "activity", "academic", "Credit sales / Total assets", "x", True,
      ["credit_sales", "ta"], r_tato_credit, "Q1 solution (detailed TATO)", ["credit_sales_basis"],
      interpret="Every unit of total assets generates {v} units of credit sales."),
    R("tato_cash", "TATO — cash sales", "معدل دوران الأصول — المبيعات النقدية", "activity", "academic", "Cash sales / Total assets", "x", True,
      ["sales", "credit_sales", "ta"], r_tato_cash, "Q1 solution (detailed TATO)", ["credit_sales_basis"],
      interpret="Every unit of total assets generates {v} units of cash sales."),
    R("fato", "Fixed assets turnover (FATO)", "معدل دوران الأصول الثابتة", "activity", "both", "Sales / Fixed assets", "x", True, ["sales", "fa"], r_fato,
      SRC_L3 + ", slide 6; Q1 solution", interpret="Every unit of fixed assets generates {v} units of sales."),
    R("cato", "Current assets turnover (CATO)", "معدل دوران الأصول المتداولة", "activity", "academic", "Sales / Current assets", "x", True, ["sales", "ca"], r_cato,
      SRC_L3 + ", slide 6; Q1 solution", interpret="Every unit of current assets generates {v} units of sales."),
    R("cash_turnover", "Cash turnover", "معدل دوران النقدية", "activity", "academic", "Sales / Cash", "x", None, ["sales", "cash"], r_cash_to,
      SRC_L3 + ", slide 6; Q1 solution", interpret="Sales are {v} times the cash balance."),
    R("ar_turnover", "Receivables turnover", "معدل دوران المدينين", "activity", "both", "Credit sales / AR", "x", True, ["credit_sales", "ar"], r_ar_to,
      SRC_L3 + ", slide 6; Q1 & Q5 solutions", ["receivables_basis", "credit_sales_basis"], interpret="Receivables are collected {v} times a year."),
    R("inventory_turnover", "Inventory turnover", "معدل دوران المخزون", "activity", "both", "COGS / Inventory", "x", True, ["cogs", "inventory"], r_inv_to,
      SRC_L3 + ", slide 6; Q1, Q2 & Q5 solutions", ["inventory_basis"], interpret="Inventory is sold and replaced {v} times a year.",
      action_if_weak="Review slow-moving stock and purchasing policy.", critical=True),
    R("payables_turnover", "Payables turnover", "معدل دوران الدائنين", "activity", "professional", "COGS (or credit purchases) / AP", "x", None,
      ["cogs", "credit_purchases", "ap"], r_ap_to, "Professional — not covered in the lectures", ["payables_driver", "payables_basis"],
      interpret="Suppliers are paid {v} times a year."),
    R("app", "Average payment period", "متوسط فترة السداد", "activity", "professional", "(AP × 360) / COGS (or credit purchases)", "days", None,
      ["ap", "cogs", "credit_purchases"], r_app, "Professional — not covered in the lectures", ["payables_driver", "payables_basis", "days_in_year"],
      interpret="Suppliers are paid on average after {v} days."),
    R("ccc", "Cash conversion cycle", "دورة التحويل النقدي", "activity", "professional", "(ASP + ACP) − Average payment period", "days", False,
      ["inventory", "ar", "ap", "cogs", "credit_sales"], r_ccc, "Professional — extends the course's 'liquidity of inventory'",
      ["inventory_basis", "receivables_basis", "payables_basis", "payables_driver", "credit_sales_basis", "days_in_year"],
      interpret="Cash is tied up in operations for {v} days after paying suppliers."),
    # ---------------- Profitability
    R("gpm", "Gross profit margin (GPM)", "هامش مجمل الربح", "profitability", "both", "Gross profit / Sales", "%", True, ["gp", "sales"], r_gpm,
      SRC_L3 + ", slide 7", interpret="Each unit of sales leaves {v} after cost of goods sold.", critical=True),
    R("oim", "Operating income margin (OIM)", "هامش الدخل التشغيلي", "profitability", "academic", "EBIT / Sales", "%", True, ["ebit", "sales"], r_oim,
      SRC_L3 + ", slides 7–8; Q3 & Q5 solutions", interpret="Each unit of sales generates {v} of EBIT.", critical=True),
    R("operating_margin", "Operating profit margin (before non-operating items)", "هامش ربح التشغيل", "profitability", "professional",
      "(Sales − COGS − operating expenses) / Sales", "%", True, ["op_income", "sales"], r_opm, SRC_L3 + ", slide 7 (OI definition)",
      interpret="Core operations earn {v} per unit of sales before non-operating items."),
    R("nim", "Net income margin (NIM)", "هامش صافي الربح", "profitability", "both", "Net income / Sales", "%", True, ["np", "sales"], r_nim,
      SRC_L3 + ", slide 7", interpret="Each unit of sales leaves {v} net profit.", critical=True),
    R("roi", "Return on investment (ROI / ROA academic)", "العائد على الاستثمار", "profitability", "academic", "EBIT / Total assets", "%", True,
      ["ebit", "ta"], r_roi, SRC_L3 + ", slide 7; Q3 & Q5 solutions", ["roi_definition", "asset_equity_basis"],
      interpret="Every unit invested in assets earns {v} before interest and tax.", critical=True),
    R("roe", "Return on equity (ROE)", "العائد على حقوق الملكية", "profitability", "academic", "EBT / Equity (course) · NP / Equity (professional option)", "%", True,
      ["ebt", "np", "equity"], r_roe, SRC_L3 + ", slide 7; Q5 solution", ["roe_definition", "asset_equity_basis"],
      interpret="Owners earn {v} on each unit of equity.", critical=True),
    R("robf", "Return on borrowed funds (ROBF)", "العائد على الأموال المقترضة", "profitability", "academic", "(ROI − Interest / BF) × (BF / OE)", "%", None,
      ["ebit", "ta", "interest", "tl", "ibd", "equity", "common_equity"], r_robf, SRC_L3 + ", slide 7; Q5 solution",
      ["roi_definition", "bf_definition", "oe_definition", "asset_equity_basis"],
      interpret="Borrowing adds {v} to the return on equity. A negative value means debt costs more than it earns."),
    R("roe_identity", "ROE = ROI + ROBF (course identity check)", "تحقق: العائد على الملكية = ROI + ROBF", "profitability", "academic", "ROI + ROBF", "%", True,
      ["ebit", "ta", "interest", "tl", "equity"], r_roe_check, SRC_L3 + ", slide 7 (D)",
      ["roi_definition", "bf_definition", "oe_definition", "asset_equity_basis"],
      interpret="ROI + ROBF = {v}. This equals EBT/Equity exactly only when BF = total liabilities and OE = total equity."),
    R("roa", "Return on assets (net)", "العائد على الأصول (صافي)", "profitability", "professional", "Net profit / Total assets", "%", True, ["np", "ta"], r_roa,
      "Professional", ["asset_equity_basis"], interpret="Assets earn {v} after interest and tax."),
    R("roce", "Return on capital employed (ROCE)", "العائد على رأس المال المستخدم", "profitability", "professional", "EBIT / (Total assets − Current liabilities)", "%", True,
      ["ebit", "ta", "cl"], r_roce, "Professional; capital = equity + LTL (Lecture 1, slide 13)", interpret="Long-term capital earns {v} before interest and tax."),
    R("dupont_roi", "DuPont: OIM × TATO", "نظام ديبونت: هامش التشغيل × دوران الأصول", "dupont", "academic", "(EBIT / Sales) × (Sales / Total assets)", "%", True,
      ["ebit", "sales", "ta"], r_dupont_check, SRC_L3 + ", slide 8; Q3 solution", ["asset_equity_basis"],
      interpret="ROI of {v} = profitability (OIM) × efficiency (TATO)."),
    # ---------------- Modern techniques / market
    R("mva", "Market value added (MVA)", "القيمة السوقية المضافة", "market", "academic", "(No. of shares × market price) − Total O/E", "ccy", True,
      ["shares_outstanding", "share_price", "equity"], r_mva, SRC_L3 + ", slide 9; Q3 solution", interpret="The market values the equity {v} above its book value."),
    R("eva", "Economic value added (EVA — course method)", "القيمة الاقتصادية المضافة", "market", "academic",
      "NP − (Interest + PS dividends + CS dividends + opportunity rate × RE)", "ccy", True,
      ["np", "interest", "pref_div", "common_div", "retained"], r_eva, SRC_L3 + ", slide 9; Q3 solution (10% on R/E)", ["eva_opportunity_rate"],
      interpret="After charging every source of capital, the company created {v} of economic value."),
    R("bvps", "Book value per share", "القيمة الدفترية للسهم", "market", "academic", "O/E / Number of shares", "ccy", True,
      ["equity", "shares_outstanding"], r_bvps, SRC_L1 + ", slide 33", interpret="Book value per share is {v}."),
    R("eps", "Earnings per share", "ربحية السهم", "market", "professional", "(NP − preferred dividends) / Number of shares", "ccy", True,
      ["np", "pref_div", "shares_outstanding"], r_eps, "Professional", interpret="Each common share earned {v}."),
    # ---------------- Cash flow
    R("ocf", "Operating cash flow", "التدفق النقدي التشغيلي", "cashflow", "professional", "Net cash from operating activities", "ccy", True,
      ["ocf"], r_ocf, "Professional", interpret="Operations generated {v} in cash.", critical=True),
    R("icf", "Investing cash flow", "التدفق النقدي الاستثماري", "cashflow", "professional", "Net cash from investing activities", "ccy", None, ["icf"], r_icf,
      "Professional", interpret="Investing activities produced {v}."),
    R("fincf", "Financing cash flow", "التدفق النقدي التمويلي", "cashflow", "professional", "Net cash from financing activities", "ccy", None, ["fincf"], r_fincf,
      "Professional", interpret="Financing activities produced {v}."),
    R("fcf", "Free cash flow", "التدفق النقدي الحر", "cashflow", "professional", "OCF − capital expenditure", "ccy", True, ["ocf", "capex"], r_fcf,
      "Professional", interpret="After investing in fixed assets, {v} of cash remains."),
    R("ocf_ratio", "Operating cash-flow ratio", "نسبة التدفق النقدي التشغيلي", "cashflow", "professional", "OCF / Current liabilities", "x", True,
      ["ocf", "cl"], r_ocf_ratio, "Professional", interpret="Operating cash flow covers current liabilities {v} times."),
    R("ocf_to_np", "Cash quality of earnings", "جودة الأرباح النقدية", "cashflow", "professional", "OCF / Net profit", "x", True, ["ocf", "np"], r_ocf_np,
      "Professional", interpret="Each unit of net profit is backed by {v} units of operating cash."),
    R("ocf_to_debt", "Cash-flow debt coverage", "تغطية الديون بالتدفق النقدي", "cashflow", "professional", "OCF / Total debts", "x", True, ["ocf", "tl"], r_ocf_debt,
      "Professional", interpret="Operating cash flow covers {v} of total debts per year."),
    # ---------------- Break-even (needs Additional Information)
    R("bep_sales", "Monetary break-even point", "نقطة التعادل بالقيمة", "breakeven", "academic", "Fixed costs / (1 − Variable costs / Sales)", "ccy", None,
      ["fixed_costs", "variable_costs", "sales"], r_bep, "Lecture 8 — Break-even & Operating Leverage, slide 5",
      interpret="Sales of {v} are needed to cover all costs."),
    R("margin_of_safety", "Margin of safety", "هامش الأمان", "breakeven", "professional", "(Sales − Break-even sales) / Sales", "%", True,
      ["fixed_costs", "variable_costs", "sales"], r_mos, "Professional (extends Lecture 8)", interpret="Sales can fall {v} before losses begin."),
    R("dol", "Degree of operating leverage", "درجة الرافعة التشغيلية", "breakeven", "professional", "(Sales − VC) / (Sales − VC − FC)", "x", None,
      ["fixed_costs", "variable_costs", "sales"], r_dol, "Professional (quantifies the Lecture 8 concept)",
      interpret="A 1% change in sales changes operating profit by {v}%."),
]

BY_KEY = {r.key: r for r in RATIOS}
