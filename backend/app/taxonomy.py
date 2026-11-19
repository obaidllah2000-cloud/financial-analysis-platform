"""Standard chart of analytical categories.

Every uploaded account is mapped (after analyst review) to exactly one category key.
Category keys drive aggregation; aggregation drives ratios. Subtotal ("total") categories
are never summed — they are only used to reconcile reported totals with computed totals.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    key: str
    statement: str  # BS | IS | CF
    element: str  # Asset | Liability | Equity | Revenue | Expense | Other | Subtotal | CashFlow
    group: str  # Current | Non-Current | Operating | Non-Operating | Financing | Investing | Other | N/A
    label_en: str
    label_ar: str
    contra: bool = False  # reduces its parent group (e.g. accumulated depreciation)
    subtotal: bool = False


C = Category
CATEGORIES: list[Category] = [
    # ---------------- Balance sheet: current assets
    C("bs.ca.cash", "BS", "Asset", "Current", "Cash & cash equivalents", "النقدية وما في حكمها"),
    C("bs.ca.st_investments", "BS", "Asset", "Current", "Short-term investments / marketable securities", "استثمارات قصيرة الأجل / أوراق مالية متداولة"),
    C("bs.ca.receivables", "BS", "Asset", "Current", "Accounts receivable / debtors", "المدينون / الذمم المدينة"),
    C("bs.ca.notes_receivable", "BS", "Asset", "Current", "Notes receivable", "أوراق القبض"),
    C("bs.ca.inventory", "BS", "Asset", "Current", "Inventory", "المخزون"),
    C("bs.ca.prepaid", "BS", "Asset", "Current", "Prepaid expenses", "مصروفات مدفوعة مقدماً"),
    C("bs.ca.other", "BS", "Asset", "Current", "Other current assets", "أصول متداولة أخرى"),
    # ---------------- Balance sheet: non-current assets
    C("bs.nca.land", "BS", "Asset", "Non-Current", "Land", "الأراضي"),
    C("bs.nca.ppe_gross", "BS", "Asset", "Non-Current", "Property, plant & equipment (at cost)", "الأصول الثابتة بالتكلفة"),
    C("bs.nca.acc_depreciation", "BS", "Asset", "Non-Current", "Accumulated depreciation (contra-asset)", "مجمع الإهلاك (حساب مقابل)", contra=True),
    C("bs.nca.ppe_net", "BS", "Asset", "Non-Current", "Property, plant & equipment (net)", "الأصول الثابتة بالصافي"),
    C("bs.nca.intangibles", "BS", "Asset", "Non-Current", "Intangible assets", "أصول غير ملموسة"),
    C("bs.nca.lt_investments", "BS", "Asset", "Non-Current", "Long-term investments", "استثمارات طويلة الأجل"),
    C("bs.nca.other", "BS", "Asset", "Non-Current", "Other non-current assets", "أصول غير متداولة أخرى"),
    # ---------------- Balance sheet: current liabilities
    C("bs.cl.payables", "BS", "Liability", "Current", "Accounts payable / creditors", "الدائنون / الموردون"),
    C("bs.cl.notes_payable", "BS", "Liability", "Current", "Notes payable", "أوراق الدفع"),
    C("bs.cl.accrued", "BS", "Liability", "Current", "Accrued expenses", "مصروفات مستحقة"),
    C("bs.cl.st_debt", "BS", "Liability", "Current", "Short-term loans / bonds / current portion of debt", "قروض وسندات قصيرة الأجل"),
    C("bs.cl.advance_revenue", "BS", "Liability", "Current", "Advance (unearned) revenue", "إيرادات مقدمة"),
    C("bs.cl.tax_payable", "BS", "Liability", "Current", "Taxes payable", "ضرائب مستحقة"),
    C("bs.cl.other", "BS", "Liability", "Current", "Other current liabilities", "خصوم متداولة أخرى"),
    # ---------------- Balance sheet: long-term liabilities
    C("bs.ncl.lt_loans", "BS", "Liability", "Non-Current", "Long-term loans", "قروض طويلة الأجل"),
    C("bs.ncl.bonds", "BS", "Liability", "Non-Current", "Long-term bonds", "سندات طويلة الأجل"),
    C("bs.ncl.other", "BS", "Liability", "Non-Current", "Other long-term liabilities", "خصوم طويلة الأجل أخرى"),
    # ---------------- Balance sheet: equity (monetary equity = O/E + preferred shares)
    C("bs.eq.common", "BS", "Equity", "N/A", "Paid-in capital / common (ordinary) shares", "رأس المال المدفوع / الأسهم العادية"),
    C("bs.eq.preferred", "BS", "Equity", "N/A", "Preferred shares", "الأسهم الممتازة"),
    C("bs.eq.reserves", "BS", "Equity", "N/A", "Reserves", "الاحتياطيات"),
    C("bs.eq.retained", "BS", "Equity", "N/A", "Retained earnings", "الأرباح المحتجزة"),
    C("bs.eq.other", "BS", "Equity", "N/A", "Other equity", "حقوق ملكية أخرى"),
    # ---------------- Balance sheet: reported subtotals (reconciliation only)
    C("bs.total.ca", "BS", "Subtotal", "Current", "Total current assets (reported)", "إجمالي الأصول المتداولة", subtotal=True),
    C("bs.total.nca", "BS", "Subtotal", "Non-Current", "Total non-current / fixed assets (reported)", "إجمالي الأصول الثابتة", subtotal=True),
    C("bs.total.assets", "BS", "Subtotal", "N/A", "Total assets (reported)", "إجمالي الأصول", subtotal=True),
    C("bs.total.cl", "BS", "Subtotal", "Current", "Total current liabilities (reported)", "إجمالي الخصوم المتداولة", subtotal=True),
    C("bs.total.ncl", "BS", "Subtotal", "Non-Current", "Total long-term liabilities (reported)", "إجمالي الخصوم طويلة الأجل", subtotal=True),
    C("bs.total.liabilities", "BS", "Subtotal", "N/A", "Total liabilities / total debts (reported)", "إجمالي الخصوم", subtotal=True),
    C("bs.total.equity", "BS", "Subtotal", "N/A", "Total equity (reported)", "إجمالي حقوق الملكية", subtotal=True),
    C("bs.total.le", "BS", "Subtotal", "N/A", "Total liabilities & equity (reported)", "إجمالي الخصوم وحقوق الملكية", subtotal=True),
    # ---------------- Income statement
    C("is.revenue", "IS", "Revenue", "Operating", "Revenue / sales", "المبيعات / الإيرادات"),
    C("is.cogs", "IS", "Expense", "Operating", "Cost of goods sold", "تكلفة المبيعات"),
    C("is.opex.selling", "IS", "Expense", "Operating", "Selling expenses", "مصروفات بيعية"),
    C("is.opex.ga", "IS", "Expense", "Operating", "General & administrative expenses", "مصروفات عمومية وإدارية"),
    C("is.opex.depreciation", "IS", "Expense", "Operating", "Depreciation & amortisation", "الإهلاك والاستهلاك"),
    C("is.opex.other", "IS", "Expense", "Operating", "Other operating expenses", "مصروفات تشغيل أخرى"),
    C("is.other_income", "IS", "Revenue", "Non-Operating", "Other income / capital gains", "إيرادات أخرى / أرباح رأسمالية"),
    C("is.other_expense", "IS", "Expense", "Non-Operating", "Other expenses / capital losses", "مصروفات أخرى / خسائر رأسمالية"),
    C("is.finance_income", "IS", "Revenue", "Financing", "Financial income (interest received)", "إيرادات تمويلية"),
    C("is.interest", "IS", "Expense", "Financing", "Interest / financial expenses", "الفوائد / المصروفات التمويلية"),
    C("is.tax", "IS", "Expense", "N/A", "Income tax", "ضريبة الدخل"),
    C("is.dividends.preferred", "IS", "Other", "N/A", "Preferred share dividends", "توزيعات الأسهم الممتازة"),
    C("is.dividends.common", "IS", "Other", "N/A", "Common share dividends", "توزيعات الأسهم العادية"),
    C("is.total.gross_profit", "IS", "Subtotal", "Operating", "Gross profit (reported)", "مجمل الربح", subtotal=True),
    C("is.total.opex", "IS", "Subtotal", "Operating", "Total operating expenses (reported)", "إجمالي مصروفات التشغيل", subtotal=True),
    C("is.total.operating_profit", "IS", "Subtotal", "Operating", "Operating profit (reported)", "ربح التشغيل", subtotal=True),
    C("is.total.ebit", "IS", "Subtotal", "N/A", "EBIT (reported)", "الربح قبل الفوائد والضرائب", subtotal=True),
    C("is.total.ebt", "IS", "Subtotal", "N/A", "Profit before tax (reported)", "الربح قبل الضرائب", subtotal=True),
    C("is.total.net_profit", "IS", "Subtotal", "N/A", "Net profit (reported)", "صافي الربح", subtotal=True),
    C("is.total.retained", "IS", "Subtotal", "N/A", "Retained earnings for the year (reported)", "الأرباح المحتجزة للعام", subtotal=True),
    # ---------------- Cash flow statement
    C("cf.op.item", "CF", "CashFlow", "Operating", "Operating cash flow item", "بند تدفق نقدي تشغيلي"),
    C("cf.inv.capex", "CF", "CashFlow", "Investing", "Capital expenditure (purchase of fixed assets)", "شراء أصول ثابتة"),
    C("cf.inv.item", "CF", "CashFlow", "Investing", "Investing cash flow item", "بند تدفق نقدي استثماري"),
    C("cf.fin.dividends", "CF", "CashFlow", "Financing", "Dividends paid", "توزيعات مدفوعة"),
    C("cf.fin.item", "CF", "CashFlow", "Financing", "Financing cash flow item", "بند تدفق نقدي تمويلي"),
    C("cf.total.operating", "CF", "Subtotal", "Operating", "Net cash from operating activities", "صافي التدفق النقدي من التشغيل", subtotal=True),
    C("cf.total.investing", "CF", "Subtotal", "Investing", "Net cash from investing activities", "صافي التدفق النقدي من الاستثمار", subtotal=True),
    C("cf.total.financing", "CF", "Subtotal", "Financing", "Net cash from financing activities", "صافي التدفق النقدي من التمويل", subtotal=True),
    C("cf.total.net_change", "CF", "Subtotal", "N/A", "Net change in cash", "صافي التغير في النقدية", subtotal=True),
    C("cf.opening_cash", "CF", "Subtotal", "N/A", "Opening cash balance", "رصيد النقدية أول المدة", subtotal=True),
    C("cf.closing_cash", "CF", "Subtotal", "N/A", "Closing cash balance", "رصيد النقدية آخر المدة", subtotal=True),
    C("unclassified", "Other", "Other", "N/A", "Unclassified — needs analyst decision", "غير مصنف — يحتاج قرار المحلل"),
]

BY_KEY: dict[str, Category] = {c.key: c for c in CATEGORIES}


def get(key: str) -> Category:
    return BY_KEY.get(key, BY_KEY["unclassified"])


def as_dicts() -> list[dict]:
    return [c.__dict__ for c in CATEGORIES]
