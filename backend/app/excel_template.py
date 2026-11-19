"""Standardised Excel template (blank) and a 5-year sample workbook."""
from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

HEAD = PatternFill("solid", fgColor="1F3A5F")
HFONT = Font(color="FFFFFF", bold=True)
NOTE = Font(italic=True, color="555555")

INDUSTRIES = ["Manufacturing", "Construction", "Trading", "Services", "Real Estate", "Financial Services", "Other"]
ADDITIONAL_KEYS = [
    ("shares_outstanding", "Number of common shares outstanding"),
    ("share_price", "Market price per share (year end)"),
    ("dividends_common", "Common dividends declared (if not in the income statement)"),
    ("dividends_preferred", "Preferred dividends (if not in the income statement)"),
    ("interest_expense", "Interest expense (if not in the income statement)"),
    ("credit_sales", "Credit sales"),
    ("cash_sales", "Cash sales"),
    ("credit_purchases", "Credit purchases"),
    ("fixed_costs", "Total fixed costs (break-even analysis)"),
    ("variable_costs", "Total variable costs (break-even analysis)"),
    ("industry_note", "Industry information (text)"),
    ("other_assumption", "Other financial assumption (text)"),
]

SHEETS = {
    "Balance_Sheet": ["Account Code", "Account Name", "Account Description", "Financial Year", "Reported Value",
                      "Current / Non-Current", "Currency", "Notes"],
    "Income_Statement": ["Account Code", "Account Name", "Account Description", "Financial Year", "Reported Value", "Currency", "Notes"],
    "Cash_Flow": ["Section", "Account Code", "Account Name", "Account Description", "Financial Year", "Reported Value", "Currency", "Notes"],
    "Opening_Balances": ["Account Code", "Account Name", "Financial Year", "Opening Value", "Notes"],
    "Additional_Info": ["Item", "Financial Year", "Value", "Notes"],
}

INSTRUCTIONS = [
    ("AI-Powered Financial Analysis Platform — Data Entry Template", "قالب إدخال البيانات — منصة التحليل المالي"),
    ("", ""),
    ("1. Fill 'Company_Info' (name, industry, currency are required).", "١. املأ ورقة بيانات الشركة (الاسم، القطاع، العملة إلزامية)."),
    ("2. Enter one row per account per financial year (long format). Add as many years and accounts as you need.",
     "٢. أدخل صفاً لكل حساب ولكل سنة مالية. يمكنك إضافة أي عدد من السنوات والحسابات."),
    ("   Alternative: you may instead put years as column headers (e.g. 2021, 2022 …) next to 'Account Name' — the platform detects it.",
     "   بديل: يمكنك وضع السنوات كعناوين أعمدة بجوار اسم الحساب وسيتم التعرف عليها تلقائياً."),
    ("3. Keep the ORIGINAL account names from the company's statements. You do not need to classify accounts before uploading.",
     "٣. احتفظ بأسماء الحسابات الأصلية كما في القوائم المالية. لا يلزم تصنيف الحسابات قبل الرفع."),
    ("4. 'Current / Non-Current' is optional. If you fill it, the platform uses it as a hint and flags conflicts.",
     "٤. عمود متداول / غير متداول اختياري، ويستخدم كمؤشر مساعد."),
    ("5. Values: numbers only. Negatives may be typed as -100 or (100). Accumulated depreciation may be negative or positive.",
     "٥. القيم أرقام فقط. السالب يكتب ‎-100 أو (100)."),
    ("6. Subtotals (Total Assets, Gross Profit, Net Profit …) may be included — they are used ONLY to reconcile, never added twice.",
     "٦. يمكن إدراج الإجماليات وتستخدم للمطابقة فقط ولا تضاف مرتين."),
    ("7. Cash_Flow: choose the Section (Operating / Investing / Financing / Summary) for every line.",
     "٧. قائمة التدفقات: اختر القسم لكل بند (تشغيلي / استثماري / تمويلي / ملخص)."),
    ("8. Opening_Balances: balances at the START of your first financial year (needed for average-balance ratios).",
     "٨. الأرصدة الافتتاحية لأول سنة مالية (مطلوبة لحساب المتوسطات)."),
    ("9. Additional_Info: credit sales, number of shares, share price, fixed/variable costs, etc.",
     "٩. معلومات إضافية: المبيعات الآجلة، عدد الأسهم، سعر السهم، التكاليف الثابتة والمتغيرة."),
    ("10. Re-uploading a revised file creates a new version; previous versions and analyst decisions are kept.",
     "١٠. إعادة رفع ملف معدل تنشئ نسخة جديدة مع الاحتفاظ بالنسخ والقرارات السابقة."),
    ("", ""),
    ("Nothing is approved automatically: after upload, every classification and assumption is reviewed on the website.",
     "لا يتم اعتماد أي شيء تلقائياً: تتم مراجعة كل تصنيف وافتراض على الموقع."),
]


def _header(ws, cols, widths=None):
    ws.append(cols)
    for i, c in enumerate(ws[1], 1):
        c.fill, c.font = HEAD, HFONT
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[c.column_letter].width = (widths or {}).get(i, 22 if i != 2 else 38)
    ws.freeze_panes = "A2"


def build(sample: bool = False) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Instructions"
    for en, ar in INSTRUCTIONS:
        ws.append([en, ar])
    ws.column_dimensions["A"].width = 110
    ws.column_dimensions["B"].width = 80
    ws["A1"].font = Font(bold=True, size=14)
    ws["B1"].font = Font(bold=True, size=14)
    for row in ws.iter_rows(min_row=2, min_col=2, max_col=2):
        for c in row:
            c.alignment = Alignment(horizontal="right")

    lists = wb.create_sheet("Lists")
    for i, v in enumerate(INDUSTRIES, 1):
        lists.cell(i, 1, v)
    for i, v in enumerate(["Current", "Non-Current"], 1):
        lists.cell(i, 2, v)
    for i, v in enumerate(["Operating", "Investing", "Financing", "Summary"], 1):
        lists.cell(i, 3, v)
    for i, (k, _) in enumerate(ADDITIONAL_KEYS, 1):
        lists.cell(i, 4, k)
    for i, v in enumerate(["Standalone", "Consolidated"], 1):
        lists.cell(i, 5, v)
    lists.sheet_state = "hidden"

    ci = wb.create_sheet("Company_Info")
    _header(ci, ["Field", "Value", "Notes"], {1: 30, 2: 40, 3: 60})
    info = [("Company Name", "", "Required"), ("Industry", "", "Manufacturing / Construction / Trading / Services / Real Estate / Financial Services / Other"),
            ("Country", "", ""), ("Reporting Currency", "", "Required, e.g. EGP, USD, SAR"), ("Financial Year End", "", "e.g. 31-Dec"),
            ("Reporting Type", "", "Standalone / Consolidated"), ("Financial Statement Basis", "", "e.g. Audited, Management accounts"),
            ("Accounting Standards", "", "e.g. IFRS, EAS — if known")]
    for r in info:
        ci.append(list(r))
    dv = DataValidation(type="list", formula1="=Lists!$A$1:$A$7", allow_blank=True)
    ci.add_data_validation(dv)
    dv.add("B3")
    dv2 = DataValidation(type="list", formula1="=Lists!$E$1:$E$2", allow_blank=True)
    ci.add_data_validation(dv2)
    dv2.add("B7")

    for name, cols in SHEETS.items():
        sh = wb.create_sheet(name)
        _header(sh, cols)
        if name == "Balance_Sheet":
            v = DataValidation(type="list", formula1="=Lists!$B$1:$B$2", allow_blank=True)
            sh.add_data_validation(v)
            v.add("F2:F5000")
        if name == "Cash_Flow":
            v = DataValidation(type="list", formula1="=Lists!$C$1:$C$4", allow_blank=True)
            sh.add_data_validation(v)
            v.add("A2:A5000")
        if name == "Additional_Info":
            v = DataValidation(type="list", formula1="=Lists!$D$1:$D$12", allow_blank=True)
            sh.add_data_validation(v)
            v.add("A2:A5000")
            k = wb.create_sheet("Additional_Info_Keys")
            k.append(["Item key", "Meaning"])
            for kk, meaning in ADDITIONAL_KEYS:
                k.append([kk, meaning])
            k.column_dimensions["A"].width = 24
            k.column_dimensions["B"].width = 70
        yr = cols.index("Financial Year") + 1
        val = cols.index("Reported Value") + 1 if "Reported Value" in cols else (cols.index("Opening Value") + 1 if "Opening Value" in cols else cols.index("Value") + 1)
        dv_year = DataValidation(type="whole", operator="between", formula1="1900", formula2="2200", allow_blank=True,
                                 showErrorMessage=True, error="Financial Year must be a 4-digit year")
        sh.add_data_validation(dv_year)
        dv_year.add(f"{get_column_letter(yr)}2:{get_column_letter(yr)}5000")
        sh.column_dimensions[get_column_letter(val)].number_format = "#,##0.00;(#,##0.00)"

    if sample:
        _fill_sample(wb)
    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue()


YEARS = [2021, 2022, 2023, 2024, 2025]


def _fill_sample(wb):
    ci = wb["Company_Info"]
    for r, v in zip(range(2, 10), ["Delta Manufacturing Co. (Sample data)", "Manufacturing", "Egypt", "EGP", "31-Dec", "Standalone",
                                   "Audited financial statements", "EAS"]):
        ci.cell(r, 2, v)
    bs = [  # code, name, hint, values
        ("1010", "Cash at banks", "Current", [120, 135, 110, 95, 70]),
        ("1020", "Investments", None, [50, 50, 60, 60, 60]),
        ("1030", "Accounts Receivable", "Current", [300, 340, 400, 470, 560]),
        ("1040", "Inventory", "Current", [400, 450, 560, 700, 850]),
        ("1050", "Prepaid Expenses", "Current", [20, 22, 25, 25, 30]),
        ("1100", "Total Current Assets", None, [890, 997, 1155, 1350, 1570]),
        ("1210", "Land", "Non-Current", [200, 200, 200, 200, 200]),
        ("1220", "Machinery & Equipment", "Non-Current", [900, 950, 1050, 1150, 1250]),
        ("1230", "Accumulated Depreciation", "Non-Current", [-300, -360, -425, -495, -570]),
        ("1999", "Total Assets", None, [1690, 1787, 1980, 2205, 2450]),
        ("2010", "Accounts Payable", "Current", [210, 240, 300, 380, 470]),
        ("2020", "Accrued Expenses", "Current", [40, 45, 50, 55, 60]),
        ("2030", "Bank Loans", "Current", [100, 120, 180, 260, 340]),
        ("2100", "Total Current Liabilities", None, [350, 405, 530, 695, 870]),
        ("2210", "Long-term Loans", "Non-Current", [500, 470, 440, 410, 380]),
        ("3010", "Share Capital", None, [600, 600, 600, 600, 600]),
        ("3020", "Legal Reserve", None, [60, 70, 80, 90, 100]),
        ("3030", "Retained Earnings", None, [180, 242, 330, 410, 500]),
        ("3999", "Total Liabilities & Equity", None, [1690, 1787, 1980, 2205, 2450]),
    ]
    ws = wb["Balance_Sheet"]
    for code, name, hint, vals in bs:
        for y, v in zip(YEARS, vals):
            ws.append([code, name, None, y, v, hint, "EGP", None])
    is_ = [
        ("4010", "Net Sales", [2000, 2250, 2550, 2800, 3050]),
        ("5010", "Cost of Goods Sold", [-1400, -1580, -1800, -2000, -2200]),
        ("5000", "Gross Profit", [600, 670, 750, 800, 850]),
        ("6010", "Selling & Distribution Expenses", [-150, -165, -185, -200, -220]),
        ("6020", "General & Administrative Expenses", [-120, -130, -140, -150, -160]),
        ("6030", "Depreciation", [-55, -60, -65, -70, -75]),
        ("7010", "Other Income", [10, 12, 8, 5, 6]),
        ("7500", "EBIT", [285, 327, 368, 385, 401]),
        ("8010", "Interest Expense", [-55, -54, -60, -72, -85]),
        ("8500", "Profit Before Tax", [230, 273, 308, 313, 316]),
        ("8600", "Income Tax", [-53, -63, -71, -72, -73]),
        ("9000", "Net Profit", [177, 210, 237, 241, 243]),
        ("9100", "Common Dividends", [-100, -138, -139, -151, -143]),
    ]
    ws = wb["Income_Statement"]
    for code, name, vals in is_:
        for y, v in zip(YEARS, vals):
            ws.append([code, name, None, y, v, "EGP", None])
    cf = [
        ("Operating", "C100", "Net cash from operating activities", [230, 215, 150, 120, 95]),
        ("Investing", "C210", "Purchase of fixed assets", [-80, -50, -100, -100, -100]),
        ("Investing", "C220", "Purchase of investments", [0, 0, -10, 0, 0]),
        ("Investing", "C200", "Net cash from investing activities", [-80, -50, -110, -100, -100]),
        ("Financing", "C310", "Dividends paid", [-100, -138, -139, -151, -143]),
        ("Financing", "C320", "Net borrowing / (repayment)", [-30, -12, 74, 116, 123]),
        ("Financing", "C300", "Net cash from financing activities", [-130, -150, -65, -35, -20]),
        ("Summary", "C400", "Net change in cash", [20, 15, -25, -15, -25]),
        ("Summary", "C410", "Opening cash balance", [100, 120, 135, 110, 95]),
        ("Summary", "C420", "Closing cash balance", [120, 135, 110, 95, 70]),
    ]
    ws = wb["Cash_Flow"]
    for sec, code, name, vals in cf:
        for y, v in zip(YEARS, vals):
            ws.append([sec, code, name, None, y, v, "EGP", None])
    ws = wb["Opening_Balances"]
    for code, name, v in [("1030", "Accounts Receivable", 280), ("1040", "Inventory", 380), ("2010", "Accounts Payable", 200)]:
        ws.append([code, name, 2021, v, "Balance at 1 Jan 2021"])
    ws = wb["Additional_Info"]
    for y, sp in zip(YEARS, [18, 20, 22, 21, 19]):
        ws.append(["shares_outstanding", y, 60, "Thousand shares of EGP 10 par"])
        ws.append(["share_price", y, sp, "Year-end market price"])
    for y, s in zip(YEARS, [2000, 2250, 2550, 2800, 3050]):
        ws.append(["credit_sales", y, round(s * 0.85), "85% of sales are on credit (sales ledger)"])
    ws.append(["fixed_costs", 2025, 700, "From cost accounting report"])
    ws.append(["variable_costs", 2025, 1900, "From cost accounting report"])
    ws.append(["industry_note", None, "Cyclical demand; peers hold ~60 days of inventory", None])
