"""Excel extraction & validation. Produces raw rows (verbatim), parsed values, and validation issues.

Supports the long layout of the template (one row per account per year) and a wide layout
(years as column headers). Never modifies values: parsing failures are reported, not fixed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal
from io import BytesIO

from openpyxl import load_workbook

from .classify import norm
from .engine.num import D

SHEET_ALIASES = {
    "company_info": ["company_info", "company information", "company info", "بيانات الشركة"],
    "BS": ["balance_sheet", "balance sheet", "financial position", "statement of financial position", "الميزانية", "المركز المالي"],
    "IS": ["income_statement", "income statement", "profit and loss", "p&l", "قائمة الدخل"],
    "CF": ["cash_flow", "cash flow", "cash flow statement", "التدفقات النقدية"],
    "opening": ["opening_balances", "opening balances", "الأرصدة الافتتاحية"],
    "additional": ["additional_info", "additional information", "additional info", "معلومات إضافية"],
}

COL_ALIASES = {
    "code": ["account code", "code", "كود الحساب"],
    "name": ["account name", "account", "name", "item", "اسم الحساب", "البند"],
    "description": ["account description", "description", "الوصف"],
    "year": ["financial year", "year", "fiscal year", "السنة المالية", "السنة"],
    "value": ["reported value", "value", "amount", "opening value", "القيمة"],
    "hint": ["current / non-current", "current/non-current", "classification", "current non current", "متداول / غير متداول"],
    "currency": ["currency", "العملة"],
    "notes": ["notes", "note", "ملاحظات"],
    "section": ["section", "activity", "القسم"],
}

INFO_FIELDS = {"company name": "name", "industry": "industry", "country": "country", "reporting currency": "currency",
               "currency": "currency", "financial year end": "fy_end", "reporting type": "reporting_type",
               "financial statement basis": "basis", "accounting standards": "standards"}


@dataclass
class Row:
    sheet: str
    row_no: int
    code: str | None
    name: str | None
    description: str | None
    section: str | None
    year_raw: str | None
    year: int | None
    value_raw: str | None
    value: Decimal | None
    hint: str | None
    currency: str | None
    notes: str | None


@dataclass
class Parsed:
    company_info: dict = field(default_factory=dict)
    rows: dict[str, list[Row]] = field(default_factory=lambda: {"BS": [], "IS": [], "CF": [], "opening": [], "additional": []})
    issues: list[dict] = field(default_factory=list)

    def issue(self, severity, code, message, sheet=None, row=None, account=None, year=None):
        self.issues.append({"severity": severity, "code": code, "message": message, "sheet": sheet, "row_no": row,
                            "account": account, "year": year})

    @property
    def years(self) -> list[int]:
        ys = {r.year for k in ("BS", "IS", "CF") for r in self.rows[k] if r.year is not None and r.value is not None}
        return sorted(ys)


def _s(v) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _match_sheet(title: str) -> str | None:
    t = title.strip().lower().replace("-", "_")
    for k, aliases in SHEET_ALIASES.items():
        if t in aliases or t.replace("_", " ") in aliases:
            return k
    return None


def _year(v) -> int | None:
    if v is None:
        return None
    if isinstance(v, (int, float)) and float(v).is_integer():
        y = int(v)
    else:
        m = re.fullmatch(r"\s*(?:FY)?\s*(\d{4})\s*", str(v), re.I)
        if not m:
            return None
        y = int(m.group(1))
    return y if 1900 <= y <= 2200 else None


def _header_map(header: list) -> tuple[dict, dict]:
    cols, year_cols = {}, {}
    for i, h in enumerate(header):
        hs = (_s(h) or "").lower()
        y = _year(h)
        if y and hs.isdigit():
            year_cols[i] = y
            continue
        for key, aliases in COL_ALIASES.items():
            if key not in cols and hs in aliases:
                cols[key] = i
                break
    return cols, year_cols


def parse(content: bytes) -> Parsed:
    p = Parsed()
    try:
        wb = load_workbook(BytesIO(content), data_only=True)
    except Exception as e:  # noqa: BLE001 — any parse failure is reported to the user
        p.issue("error", "FILE_UNREADABLE", f"The file could not be read as an Excel workbook: {e}")
        return p
    found = {}
    for ws in wb.worksheets:
        k = _match_sheet(ws.title)
        if k and k not in found:
            found[k] = ws
    if "BS" not in found and "IS" not in found:
        p.issue("error", "NO_STATEMENTS", "No Balance_Sheet or Income_Statement sheet was found. Use the standard template.")
        return p
    if "company_info" in found:
        for r in found["company_info"].iter_rows(min_row=1, values_only=True):
            if not r or r[0] is None:
                continue
            key = INFO_FIELDS.get(str(r[0]).strip().lower())
            if key and len(r) > 1 and _s(r[1]):
                p.company_info[key] = _s(r[1])
    for sk in ("BS", "IS", "CF", "opening", "additional"):
        if sk not in found:
            if sk in ("BS", "IS"):
                p.issue("warning", "MISSING_STATEMENT", f"Sheet for {'Balance Sheet' if sk == 'BS' else 'Income Statement'} is missing — "
                        "related ratios cannot be calculated.", sheet=sk)
            elif sk == "CF":
                p.issue("info", "MISSING_STATEMENT", "No Cash Flow sheet — cash-flow analysis will be unavailable.", sheet="Cash_Flow")
            continue
        _parse_sheet(p, found[sk], sk)
    _validate(p)
    return p


def _parse_sheet(p: Parsed, ws, sk: str):
    rows = list(ws.iter_rows(values_only=True))
    hdr_idx, cols, ycols = None, {}, {}
    for i, r in enumerate(rows[:10]):
        c, y = _header_map(list(r))
        if ("name" in c or (sk == "additional" and "name" in c)) and ("value" in c or y):
            hdr_idx, cols, ycols = i, c, y
            break
    if hdr_idx is None:
        p.issue("error", "BAD_STRUCTURE", f"Sheet '{ws.title}': header row not recognised (needs 'Account Name' and 'Reported Value' "
                "or year columns).", sheet=ws.title)
        return
    get = lambda r, k: r[cols[k]] if k in cols and cols[k] < len(r) else None  # noqa: E731
    for i, r in enumerate(rows[hdr_idx + 1:], start=hdr_idx + 2):
        if r is None or all(v is None or str(v).strip() == "" for v in r):
            continue
        base = dict(sheet=ws.title, row_no=i, code=_s(get(r, "code")), name=_s(get(r, "name")), description=_s(get(r, "description")),
                    section=_s(get(r, "section")), hint=_s(get(r, "hint")), currency=_s(get(r, "currency")), notes=_s(get(r, "notes")))
        if ycols:  # wide layout
            for ci, y in ycols.items():
                raw = r[ci] if ci < len(r) else None
                if raw is None or str(raw).strip() == "":
                    continue
                p.rows[sk].append(Row(**base, year_raw=str(y), year=y, value_raw=_s(raw), value=D(raw)))
        else:
            yraw, vraw = get(r, "year"), get(r, "value")
            if sk == "additional" and vraw is not None and D(vraw) is None:
                p.rows[sk].append(Row(**base, year_raw=_s(yraw), year=_year(yraw), value_raw=_s(vraw), value=None))
                continue
            p.rows[sk].append(Row(**base, year_raw=_s(yraw), year=_year(yraw), value_raw=_s(vraw), value=D(vraw)))


def _validate(p: Parsed):
    ccy = (p.company_info.get("currency") or "").upper()
    if not p.company_info.get("name"):
        p.issue("warning", "COMPANY_INFO", "Company name is missing in Company_Info.")
    if not ccy:
        p.issue("warning", "COMPANY_INFO", "Reporting currency is missing in Company_Info — currency consistency cannot be checked.")
    for sk, rows in p.rows.items():
        seen = {}
        for r in rows:
            label = r.name or r.code or f"row {r.row_no}"
            if sk == "additional":
                if r.value_raw is not None and r.value is None and r.name not in ("industry_note", "other_assumption"):
                    p.issue("error", "NON_NUMERIC", f"'{r.name}': value '{r.value_raw}' is not numeric.", r.sheet, r.row_no, r.name, r.year)
                continue
            if not r.name and not r.code:
                if r.value_raw is not None:
                    p.issue("error", "MISSING_NAME", f"A value ({r.value_raw}) has no account name.", r.sheet, r.row_no, None, r.year)
                continue
            if r.year_raw is None and r.value_raw is None:
                p.issue("info", "EMPTY_LINE", f"'{label}' has no year and no value — ignored (unused template line).", r.sheet, r.row_no, label)
                continue
            if r.year is None:
                p.issue("error", "INVALID_YEAR", f"'{label}': financial year '{r.year_raw}' is not a valid 4-digit year.", r.sheet, r.row_no, label)
            if r.value_raw is None:
                p.issue("warning", "MISSING_VALUE", f"'{label}' has no value for {r.year_raw}.", r.sheet, r.row_no, label, r.year)
            elif r.value is None:
                p.issue("error", "NON_NUMERIC", f"'{label}': value '{r.value_raw}' is not numeric.", r.sheet, r.row_no, label, r.year)
            if r.currency and ccy and r.currency.upper() != ccy:
                p.issue("error", "CURRENCY_MISMATCH", f"'{label}' is in {r.currency} but the reporting currency is {ccy}.", r.sheet, r.row_no, label, r.year)
            key = (norm(r.name or "") or r.code, r.year, r.section if sk == "CF" else None)
            if r.year is not None and key in seen:
                p.issue("error", "DUPLICATE", f"'{label}' appears more than once for {r.year} (rows {seen[key]} and {r.row_no}).",
                        r.sheet, r.row_no, label, r.year)
            seen[key] = r.row_no
    ys = {k: sorted({r.year for r in p.rows[k] if r.year}) for k in ("BS", "IS", "CF")}
    if ys["BS"] and ys["IS"] and ys["BS"] != ys["IS"]:
        p.issue("warning", "YEAR_INCONSISTENT", f"Balance-sheet years {ys['BS']} differ from income-statement years {ys['IS']}. "
                "Ratios that combine both statements will only be computed for common years.")
    if ys["CF"] and ys["BS"] and set(ys["CF"]) - set(ys["BS"]):
        p.issue("warning", "YEAR_INCONSISTENT", f"Cash-flow years {ys['CF']} include years not in the balance sheet.")
    allyears = sorted(set(ys["BS"]) | set(ys["IS"]))
    if allyears:
        gaps = [y for y in range(allyears[0], allyears[-1] + 1) if y not in allyears]
        if gaps:
            p.issue("warning", "MISSING_YEARS", f"Missing financial years inside the range: {gaps}. Year-over-year changes skip these gaps.")
    if ys["BS"] and not p.rows["opening"]:
        p.issue("warning", "MISSING_OPENING", f"No opening balances for {ys['BS'][0]} — average-balance ratios for the first year need an "
                "assumption (use closing balance or exclude).", year=ys["BS"][0])
    if len(allyears) == 1:
        p.issue("info", "SINGLE_YEAR", "Only one financial year — trend and growth analysis are not possible.")
