"""Account classification engine.

Deterministic, explainable rules (English + Arabic keywords). Each suggestion carries:
category, confidence, reasoning, and — when the account could legitimately belong to more
than one category — a question for the analyst plus answer options that map to categories.
The engine never silently resolves a genuine ambiguity: it lowers confidence and asks.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import taxonomy


@dataclass
class Suggestion:
    category: str
    confidence: float
    reason: str
    question: str | None = None
    options: list[dict] = field(default_factory=list)  # [{"label":..., "category":...}]
    hint_conflict: bool = False

    def to_dict(self) -> dict:
        cat = taxonomy.get(self.category)
        return {
            "category": self.category,
            "label_en": cat.label_en,
            "label_ar": cat.label_ar,
            "statement": cat.statement,
            "element": cat.element,
            "group": cat.group,
            "confidence": round(self.confidence, 2),
            "reason": self.reason,
            "question": self.question,
            "options": self.options,
            "hint_conflict": self.hint_conflict,
        }


def norm(s: str) -> str:
    s = (s or "").lower().strip()
    s = s.replace("&", " and ").replace("/", " / ")
    s = re.sub(r"[\.\(\)\-_,:]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _has(n: str, *words: str) -> bool:
    return any(re.search(r"(^|\s)" + re.escape(w) + r"($|\s)", n) for w in words)


# (statement, keywords, category, confidence, reason)
# Order matters: specific rules first. Totals are handled separately.
RULES: list[tuple[str, tuple[str, ...], str, float, str]] = [
    # --- BS assets
    ("BS", ("accumulated depreciation", "acc depreciation", "depreciation", "مجمع الإهلاك", "مجمع الاهلاك", "الإهلاك المتراكم"), "bs.nca.acc_depreciation", 0.9,
     "Accumulated depreciation is a contra-asset that reduces fixed assets (Lecture 2 shows it in parentheses under fixed assets)."),
    ("BS", ("cash", "bank", "cash equivalents", "cash and equivalents", "النقدية", "نقدية", "البنوك", "الصندوق", "نقدية بالبنوك"), "bs.ca.cash", 0.95,
     "Cash and bank balances are the most liquid current asset."),
    ("BS", ("marketable securities", "short term investments", "st invest", "s t invest", "trading securities", "استثمارات قصيرة", "أوراق مالية متداولة"), "bs.ca.st_investments", 0.92,
     "Name states the investment is short-term / marketable, so it is a current financial asset."),
    ("BS", ("notes receivable", "n r", "أوراق القبض", "اوراق القبض"), "bs.ca.notes_receivable", 0.92, "Notes receivable are short-term claims on customers."),
    ("BS", ("accounts receivable", "receivable", "receivables", "debtors", "a r", "trade debtors", "المدينون", "العملاء", "مدينون", "ذمم مدينة"), "bs.ca.receivables", 0.93,
     "Receivables/debtors are amounts owed by customers — a current asset."),
    ("BS", ("inventory", "inventories", "stock", "invent", "المخزون", "مخزون", "بضاعة"), "bs.ca.inventory", 0.95, "Inventory is a current asset (Lecture 1, slide 28)."),
    ("BS", ("prepaid", "prepayments", "prepaid expenses", "مصروفات مدفوعة مقدما", "مدفوعة مقدماً", "مقدما"), "bs.ca.prepaid", 0.9, "Prepaid expenses are consumed within the year."),
    ("BS", ("land", "الأراضي", "اراضي", "أراضي"), "bs.nca.land", 0.93, "Land is a fixed (non-current) asset (Lecture 1, slide 27)."),
    ("BS", ("net buildings", "net building", "net machinery", "net fixed assets", "net ppe", "net equipment", "صافي الأصول الثابتة", "صافي"), "bs.nca.ppe_net", 0.85,
     "Name indicates the fixed asset is shown net of accumulated depreciation."),
    ("BS", ("buildings", "building", "machinery", "machines", "equipment", "ppe", "property plant", "fixed assets", "vehicles", "furniture", "المباني", "الآلات", "المعدات", "الأصول الثابتة", "آلات"), "bs.nca.ppe_gross", 0.8,
     "Buildings, machinery and equipment are fixed assets. Whether the figure is gross (at cost) or net depends on whether accumulated depreciation is reported separately."),
    ("BS", ("goodwill", "intangible", "intangibles", "patent", "trademark", "software", "أصول غير ملموسة", "شهرة"), "bs.nca.intangibles", 0.92, "Intangible assets are non-current (Lecture 1, slide 27)."),
    ("BS", ("long term investment", "long term investments", "lt invest", "l t invest", "investment in subsidiaries", "investments in associates", "استثمارات طويلة"), "bs.nca.lt_investments", 0.9,
     "Name states the investment is long-term, so it is a non-current asset."),
    # --- BS liabilities
    ("BS", ("notes payable", "n p", "أوراق الدفع", "اوراق الدفع"), "bs.cl.notes_payable", 0.92, "Notes payable are short-term debts (Lecture 1, slide 30)."),
    ("BS", ("accounts payable", "payable", "payables", "creditors", "suppliers", "a p", "trade creditors", "الدائنون", "الموردون", "دائنون", "ذمم دائنة"), "bs.cl.payables", 0.92,
     "Creditors/suppliers are short-term operating liabilities."),
    ("BS", ("accrued", "accruals", "accrual expenses", "accrued expenses", "مصروفات مستحقة", "مستحقة"), "bs.cl.accrued", 0.92, "Accrued expenses are current liabilities (Lecture 1, slide 30)."),
    ("BS", ("advance revenue", "advanced revenue", "advanced revenues", "unearned revenue", "deferred revenue", "customer advances", "إيرادات مقدمة", "دفعات مقدمة من العملاء"), "bs.cl.advance_revenue", 0.88,
     "Revenue received in advance is an obligation to deliver within the year."),
    ("BS", ("tax payable", "taxes payable", "income tax payable", "ضرائب مستحقة"), "bs.cl.tax_payable", 0.9, "Taxes payable are settled within the year."),
    ("BS", ("short term loan", "short term loans", "st loan", "s t loan", "s t debts", "st debts", "short term debt", "short term bonds", "overdraft", "current portion", "قروض قصيرة", "سحب على المكشوف", "بنوك دائنة"), "bs.cl.st_debt", 0.92,
     "Name states the debt is short-term — a current liability."),
    ("BS", ("long term loan", "long term loans", "lt loans", "l t loans", "loans 5 years", "term loan", "قروض طويلة"), "bs.ncl.lt_loans", 0.92, "Name states the loan is long-term."),
    ("BS", ("long term bonds", "lt bonds", "l t bonds", "debentures", "سندات طويلة"), "bs.ncl.bonds", 0.92, "Long-term bonds are long-term liabilities (Lecture 1, slide 30)."),
    # --- BS equity
    ("BS", ("preferred shares", "preference shares", "pref shares", "preferred stock", "preferred sticks", "أسهم ممتازة", "الأسهم الممتازة"), "bs.eq.preferred", 0.93,
     "Preferred shares are part of monetary equity (Lecture 1, slide 29: M/E = O/E + preferred shares)."),
    ("BS", ("retained earnings", "retained", "r e", "retained earnings and reserves", "الأرباح المحتجزة", "أرباح محتجزة", "أرباح مرحلة"), "bs.eq.retained", 0.95, "Retained earnings are owners' equity."),
    ("BS", ("reserve", "reserves", "احتياطي", "الاحتياطيات"), "bs.eq.reserves", 0.92, "Reserves are owners' equity."),
    ("BS", ("capital", "share capital", "paid in capital", "common shares", "ordinary shares", "ordinary stocks", "common stock", "ord shares", "رأس المال", "الأسهم العادية"), "bs.eq.common", 0.9,
     "Paid-in capital / ordinary shares are owners' equity."),
    # --- Income statement
    ("IS", ("cost of goods sold", "cogs", "cost of sales", "cost of revenue", "تكلفة المبيعات", "تكلفة البضاعة المباعة"), "is.cogs", 0.95, "Cost of goods sold."),
    ("IS", ("financial income", "interest income", "finance income", "إيرادات تمويلية", "فوائد دائنة"), "is.finance_income", 0.9, "Financial income is earned on financial assets."),
    ("IS", ("capital losses", "capital loss", "loss on sale", "other expenses", "other exp", "خسائر رأسمالية", "مصروفات أخرى"), "is.other_expense", 0.85, "Non-recurring / non-operating expense."),
    ("IS", ("capital gains", "capital gain", "gain on sale", "other revenues", "other income", "أرباح رأسمالية", "إيرادات أخرى"), "is.other_income", 0.85, "Non-recurring / non-operating income."),
    ("IS", ("sales", "revenue", "revenues", "net sales", "turnover", "المبيعات", "الإيرادات", "صافي المبيعات"), "is.revenue", 0.93, "Sales / revenue line."),
    ("IS", ("selling", "distribution", "marketing", "مصروفات بيعية", "مصروفات البيع والتوزيع"), "is.opex.selling", 0.9, "Selling expenses are operating expenses."),
    ("IS", ("general and administrative", "administrative", "g and a", "admin", "مصروفات عمومية", "إدارية"), "is.opex.ga", 0.9, "G&A expenses are operating expenses."),
    ("IS", ("depreciation", "amortisation", "amortization", "deprec", "الإهلاك", "الاهلاك"), "is.opex.depreciation", 0.9, "Depreciation is an operating expense included in total operating expenses (Lecture 5)."),
    ("IS", ("interest", "i", "finance cost", "finance costs", "financial expenses", "financing costs", "فوائد", "مصروفات تمويلية"), "is.interest", 0.93, "Interest is the financing charge deducted after EBIT (Lecture 1, slide 25)."),
    ("IS", ("tax", "taxes", "income tax", "ضريبة", "الضرائب"), "is.tax", 0.92, "Income tax expense."),
    ("IS", ("preferred dividends", "p s dividends", "ps dividends", "p s divid", "preferred share dividends", "توزيعات الأسهم الممتازة"), "is.dividends.preferred", 0.9, "Preferred dividends are deducted after net profit (Lecture 1, slide 25)."),
    ("IS", ("common dividends", "c s dividends", "cs dividends", "c s divid", "ordinary dividends", "dividends", "توزيعات"), "is.dividends.common", 0.85, "Common dividends are deducted from net distributable profit."),
    ("IS", ("operating expenses", "opex", "other operating", "مصروفات التشغيل"), "is.opex.other", 0.75, "Operating expense line."),
    # --- Cash flow
    ("CF", ("purchase of fixed assets", "capital expenditure", "capex", "purchase of property", "acquisition of ppe", "شراء أصول ثابتة"), "cf.inv.capex", 0.9, "Capital expenditure is an investing outflow."),
    ("CF", ("dividends paid", "توزيعات مدفوعة"), "cf.fin.dividends", 0.9, "Dividends paid are a financing outflow."),
]

TOTAL_RULES: list[tuple[str, tuple[str, ...], str]] = [
    ("BS", ("total current assets", "t c a", "tca", "إجمالي الأصول المتداولة"), "bs.total.ca"),
    ("BS", ("total fixed assets", "total non current assets", "total f assets", "tot fixed assets", "إجمالي الأصول الثابتة", "إجمالي الأصول غير المتداولة"), "bs.total.nca"),
    ("BS", ("total assets", "t asset", "t assets", "إجمالي الأصول"), "bs.total.assets"),
    ("BS", ("total current liabilities", "t c liabilities", "tcl", "إجمالي الخصوم المتداولة"), "bs.total.cl"),
    ("BS", ("total long term liabilities", "total non current liabilities", "total lt liabilities", "إجمالي الخصوم طويلة الأجل"), "bs.total.ncl"),
    ("BS", ("total liabilities and", "total l and", "total liab and", "total liabilities and o e", "total liabilities and equity", "إجمالي الخصوم وحقوق الملكية"), "bs.total.le"),
    ("BS", ("total liabilities", "total debts", "total liab", "إجمالي الخصوم", "إجمالي الديون"), "bs.total.liabilities"),
    ("BS", ("total o e", "total equity", "total owners equity", "total shareholders equity", "إجمالي حقوق الملكية"), "bs.total.equity"),
    ("IS", ("gross profit", "gp", "مجمل الربح"), "is.total.gross_profit"),
    ("IS", ("total operating expenses", "total op expense", "t o e", "إجمالي مصروفات التشغيل"), "is.total.opex"),
    ("IS", ("operating profit", "operation net profit", "operating income", "op income", "ربح التشغيل"), "is.total.operating_profit"),
    ("IS", ("ebit", "earnings before interest", "الربح قبل الفوائد"), "is.total.ebit"),
    ("IS", ("ebt", "profit before tax", "earnings before tax", "الربح قبل الضرائب"), "is.total.ebt"),
    ("IS", ("net profit", "net income", "np", "صافي الربح", "صافي الدخل"), "is.total.net_profit"),
    ("IS", ("net distributable profit", "net distr pr", "retained for the year", "re", "r e"), "is.total.retained"),
    ("CF", ("net cash from operating", "operating activities", "cash from operations", "صافي التدفق النقدي من الأنشطة التشغيلية", "الأنشطة التشغيلية"), "cf.total.operating"),
    ("CF", ("net cash from investing", "investing activities", "الأنشطة الاستثمارية"), "cf.total.investing"),
    ("CF", ("net cash from financing", "financing activities", "الأنشطة التمويلية"), "cf.total.financing"),
    ("CF", ("net change in cash", "net increase in cash", "net decrease in cash", "صافي التغير في النقدية"), "cf.total.net_change"),
    ("CF", ("opening cash", "cash at beginning", "beginning cash", "رصيد النقدية أول"), "cf.opening_cash"),
    ("CF", ("closing cash", "cash at end", "ending cash", "رصيد النقدية آخر"), "cf.closing_cash"),
]

HINT_MAP = {"current": "Current", "متداول": "Current", "non-current": "Non-Current", "non current": "Non-Current",
            "noncurrent": "Non-Current", "غير متداول": "Non-Current", "long-term": "Non-Current", "short-term": "Current"}


def parse_hint(h: str | None) -> str | None:
    if not h:
        return None
    h2 = str(h).strip().lower()
    for k, v in HINT_MAP.items():
        if h2 == k:
            return v
    if "non" in h2 or "غير" in h2 or "long" in h2:
        return "Non-Current"
    if "current" in h2 or "متداول" in h2 or "short" in h2:
        return "Current"
    return None


def _match(rules, n: str, statement: str):
    for st, words, cat, *rest in rules:
        if st != statement:
            continue
        if _has(n, *words):
            return (cat, *rest)
    return None


def suggest(name: str, statement: str, hint: str | None = None, section: str | None = None,
            description: str | None = None) -> Suggestion:
    """Suggest a category for one account. `statement` is BS/IS/CF from the Excel sheet."""
    n = norm(name)
    d = norm(description or "")
    hint_grp = parse_hint(hint)

    if not n:
        return Suggestion("unclassified", 0.0, "Account name is missing — it cannot be classified.",
                          question="This line has no account name. What is it?")

    # 1) Reported totals / subtotals
    is_totalish = n.startswith("total") or n.startswith("إجمالي") or n.startswith("مجموع") or n.startswith("tot ")
    tm = _match(TOTAL_RULES, n, statement)
    if tm and (is_totalish or statement in ("IS", "CF")):
        cat = tm[0]
        return Suggestion(cat, 0.9, "Line is a reported subtotal. It is kept for reconciliation only and is never added "
                                    "into aggregates, to avoid double counting.")
    if is_totalish:
        return Suggestion("unclassified", 0.4, "Line looks like a subtotal but its scope is not recognised.",
                          question=f"'{name}' looks like a total. Which subtotal does it represent?",
                          options=[{"label": taxonomy.get(k).label_en, "category": k} for k in
                                   ("bs.total.ca", "bs.total.nca", "bs.total.assets", "bs.total.cl", "bs.total.liabilities", "bs.total.equity")]
                          if statement == "BS" else [])

    # 2) Cash-flow statement: section column drives classification
    if statement == "CF":
        m = _match(RULES, n, "CF")
        if m:
            return Suggestion(m[0], m[1], m[2])
        sec = (section or "").lower()
        if sec.startswith("oper") or "تشغيل" in sec:
            return Suggestion("cf.op.item", 0.85, "Listed under Operating Activities in the Excel 'Section' column.")
        if sec.startswith("inv") or "استثمار" in sec:
            return Suggestion("cf.inv.item", 0.85, "Listed under Investing Activities in the Excel 'Section' column.")
        if sec.startswith("fin") or "تمويل" in sec:
            return Suggestion("cf.fin.item", 0.85, "Listed under Financing Activities in the Excel 'Section' column.")
        return Suggestion("unclassified", 0.3, "Cash-flow line without a recognised section.",
                          question=f"Which activity does '{name}' belong to?",
                          options=[{"label": "Operating", "category": "cf.op.item"},
                                   {"label": "Investing", "category": "cf.inv.item"},
                                   {"label": "Financing", "category": "cf.fin.item"}])

    # 3) Genuinely ambiguous balance-sheet names — ask instead of assuming
    if statement == "BS":
        if _has(n, "investment", "investments", "استثمارات", "استثمار") and not _has(
                n, "short term", "long term", "marketable", "trading", "lt", "st", "subsidiaries", "associates", "قصيرة", "طويلة"):
            q = ("Is this investment readily convertible into cash and held for short-term trading, "
                 "or is it a long-term strategic investment?")
            opts = [{"label": "Short-term / readily convertible (current asset)", "category": "bs.ca.st_investments"},
                    {"label": "Long-term / strategic (non-current asset)", "category": "bs.nca.lt_investments"}]
            if hint_grp == "Current":
                return Suggestion("bs.ca.st_investments", 0.7, "Name does not state the investment horizon; the Excel "
                                  "Current/Non-Current column says Current, so it is suggested as a current asset.", q, opts)
            if hint_grp == "Non-Current":
                return Suggestion("bs.nca.lt_investments", 0.7, "Name does not state the investment horizon; the Excel "
                                  "Current/Non-Current column says Non-Current.", q, opts)
            return Suggestion("bs.nca.lt_investments", 0.45, "Investment horizon is unknown. It changes liquidity ratios, "
                              "so the analyst must confirm before it is used.", q, opts)
        if _has(n, "loan", "loans", "قروض", "قرض", "borrowings") and not _has(n, "short term", "long term", "st", "lt", "قصيرة", "طويلة", "5 years", "term"):
            q = "Is this loan repayable within one year (current) or after more than one year (long-term)?"
            opts = [{"label": "Within one year (current liability)", "category": "bs.cl.st_debt"},
                    {"label": "After one year (long-term liability)", "category": "bs.ncl.lt_loans"}]
            cat = "bs.cl.st_debt" if hint_grp == "Current" else "bs.ncl.lt_loans"
            conf = 0.7 if hint_grp else 0.45
            return Suggestion(cat, conf, "Loan maturity is not stated in the name" + (
                "; the Excel Current/Non-Current column was used." if hint_grp else "."), q, opts)
        if _has(n, "bonds", "bond", "سندات") and not _has(n, "long term", "short term", "lt", "st", "طويلة", "قصيرة"):
            q = "Do these bonds mature within one year (current) or later (long-term)?"
            opts = [{"label": "Within one year", "category": "bs.cl.st_debt"},
                    {"label": "Long-term", "category": "bs.ncl.bonds"}]
            cat = "bs.cl.st_debt" if hint_grp == "Current" else "bs.ncl.bonds"
            return Suggestion(cat, 0.7 if hint_grp else 0.55, "Bond maturity is not stated in the name.", q, opts)
        if _has(n, "provision", "provisions", "مخصص", "مخصصات"):
            q = "Is this provision expected to be settled within one year, or is it a long-term provision / asset allowance?"
            opts = [{"label": "Current liability", "category": "bs.cl.other"},
                    {"label": "Long-term liability", "category": "bs.ncl.other"},
                    {"label": "Allowance deducted from receivables", "category": "bs.ca.receivables"}]
            return Suggestion("bs.cl.other" if hint_grp != "Non-Current" else "bs.ncl.other", 0.4,
                              "Provisions vary in nature (liability vs. asset allowance).", q, opts)
        if _has(n, "related parties", "related party", "due to", "due from", "أطراف ذات علاقة"):
            q = "Is this a receivable from or a payable to related parties, and is it due within one year?"
            opts = [{"label": "Receivable — current", "category": "bs.ca.other"},
                    {"label": "Receivable — non-current", "category": "bs.nca.other"},
                    {"label": "Payable — current", "category": "bs.cl.other"},
                    {"label": "Payable — non-current", "category": "bs.ncl.other"}]
            return Suggestion("bs.ca.other" if "from" in n else "bs.cl.other", 0.4, "Related-party balances need context.", q, opts)

    # 4) Keyword rules
    m = _match(RULES, n, statement)
    if not m and d:
        m = _match(RULES, d, statement)
        if m:
            m = (m[0], m[1] - 0.15, m[2] + " (matched on the account description).")
    if m:
        cat, conf, reason = m
        sug = Suggestion(cat, conf, reason)
        grp = taxonomy.get(cat).group
        if hint_grp and grp in ("Current", "Non-Current") and hint_grp != grp:
            sug.hint_conflict = True
            sug.confidence = min(conf, 0.5)
            sug.reason += f" NOTE: the Excel file marks this account as {hint_grp}, which conflicts with the suggested {grp} classification."
            sug.question = f"The uploaded file says '{name}' is {hint_grp}, but its name suggests {grp}. Which is correct?"
            sug.options = [{"label": f"Keep {taxonomy.get(cat).label_en}", "category": cat},
                           {"label": f"Treat as other {hint_grp.lower()} item",
                            "category": _other_for(taxonomy.get(cat).element, hint_grp)}]
        return sug

    # 5) Unknown: fall back to the analyst hint
    if statement == "BS":
        q = f"'{name}' was not recognised. What type of balance-sheet item is it?"
        opts = [{"label": taxonomy.get(k).label_en, "category": k} for k in
                ("bs.ca.other", "bs.nca.other", "bs.cl.other", "bs.ncl.other", "bs.eq.other")]
        if hint_grp == "Current":
            return Suggestion("bs.ca.other", 0.3, "Not recognised; Excel marks it Current. Asset vs liability is unknown.", q, opts)
        if hint_grp == "Non-Current":
            return Suggestion("bs.nca.other", 0.3, "Not recognised; Excel marks it Non-Current. Asset vs liability is unknown.", q, opts)
        return Suggestion("unclassified", 0.1, "Account name not recognised.", q, opts)
    if statement == "IS":
        q = f"'{name}' was not recognised. Is it operating or non-operating, income or expense?"
        opts = [{"label": taxonomy.get(k).label_en, "category": k} for k in
                ("is.opex.other", "is.other_income", "is.other_expense", "is.revenue", "is.cogs")]
        return Suggestion("unclassified", 0.1, "Account name not recognised.", q, opts)
    return Suggestion("unclassified", 0.1, "Account name not recognised.")


def _other_for(element: str, grp: str) -> str:
    if element == "Asset":
        return "bs.ca.other" if grp == "Current" else "bs.nca.other"
    if element == "Liability":
        return "bs.cl.other" if grp == "Current" else "bs.ncl.other"
    return "bs.eq.other"


def post_pass(accounts: list[dict]) -> None:
    """Company-level checks that need to see all accounts at once.

    accounts: [{"name", "statement", "suggestion": Suggestion}]  (mutated in place)
    """
    cats = {a["suggestion"].category for a in accounts}
    has_gross = "bs.nca.ppe_gross" in cats
    has_accdep = "bs.nca.acc_depreciation" in cats
    for a in accounts:
        s: Suggestion = a["suggestion"]
        n = norm(a["name"])
        # 'Net fixed assets' alongside gross + accumulated depreciation = probable subtotal
        if s.category == "bs.nca.ppe_net" and has_gross and has_accdep and "fixed assets" in n:
            s.confidence = 0.4
            s.question = ("Gross fixed assets and accumulated depreciation are both reported separately. Is "
                          f"'{a['name']}' a subtotal of those lines (exclude from sums) or a separate asset?")
            s.options = [{"label": "Subtotal — reconcile only", "category": "bs.total.nca"},
                         {"label": "Separate net asset", "category": "bs.nca.ppe_net"}]
            s.reason += " Possible double counting with gross fixed assets less accumulated depreciation."
        # Gross PPE without accumulated depreciation → it is probably net
        if s.category == "bs.nca.ppe_gross" and not has_accdep:
            s.category = "bs.nca.ppe_net"
            s.reason = ("Fixed asset reported without a separate accumulated-depreciation line, so it is treated as a net "
                        "book value.")
