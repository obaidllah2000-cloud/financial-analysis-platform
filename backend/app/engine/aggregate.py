"""Builds standardised per-year aggregates from classified accounts.

Pure functions: input = accounts (with original values + category + status), output = aggregates
with full component traceability. Nothing here mutates original data.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from .. import taxonomy
from .num import D0, ssum

USABLE = {"approved", "modified", "pending", "info_requested"}  # rejected → excluded
APPROVED = {"approved", "modified"}

# Income-statement categories whose magnitude is what matters (users often type them as negatives)
ABS_CATEGORIES = {"is.cogs", "is.opex.selling", "is.opex.ga", "is.opex.depreciation", "is.opex.other", "is.other_expense",
                  "is.interest", "is.tax", "is.dividends.preferred", "is.dividends.common", "is.total.opex",
                  "bs.nca.acc_depreciation"}


@dataclass
class AccountInput:
    id: int
    name: str
    statement: str
    category: str
    status: str  # approved | modified | pending | info_requested | rejected
    values: dict[int, Decimal]  # original reported values by year
    opening: dict[int, Decimal] = field(default_factory=dict)  # opening balance for a year (from Opening sheet)
    code: str | None = None


def normalize(value: Decimal | None, category: str) -> tuple[Decimal | None, str | None]:
    """Return (normalized value, note). Original value is never changed; only a normalized copy is produced."""
    if value is None:
        return None, None
    if category in ABS_CATEGORIES and value < 0:
        note = ("Entered as a negative (presentation in parentheses); the magnitude is used because the "
                "category is deducted by formula.")
        return -value, note
    return value, None


@dataclass
class Agg:
    value: Decimal | None
    components: list[dict] = field(default_factory=list)
    source: str = "computed"  # computed | reported | derived | additional | missing
    formula: str = ""
    provisional: bool = False  # any component not yet approved

    def to_dict(self):
        from .num import f
        return {"value": f(self.value), "source": self.source, "formula": self.formula,
                "provisional": self.provisional, "components": self.components}


# Aggregate definitions for simple sums of categories (balance sheet)
SUM_DEFS: dict[str, tuple[str, list[str]]] = {
    "cash": ("Cash & equivalents", ["bs.ca.cash"]),
    "st_inv": ("Short-term investments", ["bs.ca.st_investments"]),
    "ar": ("Receivables (A/R + N/R)", ["bs.ca.receivables", "bs.ca.notes_receivable"]),
    "inventory": ("Inventory", ["bs.ca.inventory"]),
    "prepaid": ("Prepaid expenses", ["bs.ca.prepaid"]),
    "other_ca": ("Other current assets", ["bs.ca.other"]),
    "land": ("Land", ["bs.nca.land"]),
    "ppe_gross": ("PP&E at cost", ["bs.nca.ppe_gross"]),
    "acc_dep": ("Accumulated depreciation", ["bs.nca.acc_depreciation"]),
    "ppe_net_reported": ("PP&E reported net", ["bs.nca.ppe_net"]),
    "intangibles": ("Intangibles", ["bs.nca.intangibles"]),
    "lt_inv": ("Long-term investments", ["bs.nca.lt_investments"]),
    "other_nca": ("Other non-current assets", ["bs.nca.other"]),
    "ap": ("Accounts payable / creditors", ["bs.cl.payables"]),
    "notes_payable": ("Notes payable", ["bs.cl.notes_payable"]),
    "accrued": ("Accrued expenses", ["bs.cl.accrued"]),
    "st_debt": ("Short-term debt", ["bs.cl.st_debt"]),
    "adv_rev": ("Advance revenue", ["bs.cl.advance_revenue"]),
    "tax_payable": ("Taxes payable", ["bs.cl.tax_payable"]),
    "other_cl": ("Other current liabilities", ["bs.cl.other"]),
    "lt_loans": ("Long-term loans", ["bs.ncl.lt_loans"]),
    "bonds": ("Long-term bonds", ["bs.ncl.bonds"]),
    "other_ncl": ("Other long-term liabilities", ["bs.ncl.other"]),
    "pref": ("Preferred shares", ["bs.eq.preferred"]),
    "common": ("Paid-in / common capital", ["bs.eq.common"]),
    "reserves": ("Reserves", ["bs.eq.reserves"]),
    "retained": ("Retained earnings", ["bs.eq.retained"]),
    "other_eq": ("Other equity", ["bs.eq.other"]),
    # income statement
    "sales": ("Sales / revenue", ["is.revenue"]),
    "cogs": ("Cost of goods sold", ["is.cogs"]),
    "selling": ("Selling expenses", ["is.opex.selling"]),
    "ga": ("G&A expenses", ["is.opex.ga"]),
    "depreciation": ("Depreciation", ["is.opex.depreciation"]),
    "other_opex": ("Other operating expenses", ["is.opex.other"]),
    "other_income": ("Other income", ["is.other_income"]),
    "other_expense": ("Other expenses / capital losses", ["is.other_expense"]),
    "finance_income": ("Financial income", ["is.finance_income"]),
    "interest": ("Interest expense", ["is.interest"]),
    "tax": ("Income tax", ["is.tax"]),
    "pref_div": ("Preferred dividends", ["is.dividends.preferred"]),
    "common_div": ("Common dividends", ["is.dividends.common"]),
    # cash flow
    "cf_op_items": ("Operating cash-flow items", ["cf.op.item"]),
    "cf_inv_items": ("Investing cash-flow items", ["cf.inv.item", "cf.inv.capex"]),
    "cf_fin_items": ("Financing cash-flow items", ["cf.fin.item", "cf.fin.dividends"]),
    "capex": ("Capital expenditure", ["cf.inv.capex"]),
    "dividends_paid": ("Dividends paid", ["cf.fin.dividends"]),
}

REPORTED = {
    "ca": "bs.total.ca", "fa": "bs.total.nca", "ta": "bs.total.assets", "cl": "bs.total.cl", "ncl": "bs.total.ncl",
    "tl": "bs.total.liabilities", "equity": "bs.total.equity", "tle": "bs.total.le",
    "gp": "is.total.gross_profit", "opex": "is.total.opex", "op_income": "is.total.operating_profit",
    "ebit": "is.total.ebit", "ebt": "is.total.ebt", "np": "is.total.net_profit",
    "ocf": "cf.total.operating", "icf": "cf.total.investing", "fincf": "cf.total.financing",
    "net_change_cash": "cf.total.net_change", "opening_cash": "cf.opening_cash", "closing_cash": "cf.closing_cash",
}

LABELS = {k: v[0] for k, v in SUM_DEFS.items()} | {
    "ca": "Total current assets", "fa": "Fixed (non-current) assets", "ta": "Total assets", "cl": "Current liabilities",
    "ncl": "Long-term liabilities (LTL)", "tl": "Total debts (liabilities)", "equity": "Monetary equity (O/E incl. preferred)",
    "common_equity": "Common owners' equity", "tle": "Total liabilities & equity", "ibd": "Interest-bearing debt",
    "gp": "Gross profit", "opex": "Total operating expenses", "op_income": "Operating income", "ebit": "EBIT", "ebt": "EBT",
    "np": "Net profit", "ndp": "Net distributable profit", "re_add": "Retained earnings for the year",
    "ocf": "Operating cash flow", "icf": "Investing cash flow", "fincf": "Financing cash flow",
    "net_change_cash": "Net change in cash", "opening_cash": "Opening cash", "closing_cash": "Closing cash",
    "fcf": "Free cash flow", "credit_sales": "Credit sales", "cash_sales": "Cash sales", "purchases": "Credit purchases",
}

CA_CATS = [c.key for c in taxonomy.CATEGORIES if c.key.startswith("bs.ca.")]
NCA_PLUS = ["bs.nca.land", "bs.nca.ppe_gross", "bs.nca.ppe_net", "bs.nca.intangibles", "bs.nca.lt_investments", "bs.nca.other"]
CL_CATS = [c.key for c in taxonomy.CATEGORIES if c.key.startswith("bs.cl.")]
NCL_CATS = [c.key for c in taxonomy.CATEGORIES if c.key.startswith("bs.ncl.")]
EQ_CATS = [c.key for c in taxonomy.CATEGORIES if c.key.startswith("bs.eq.")]


class YearBook:
    """All aggregates for one year."""

    def __init__(self, year: int):
        self.year = year
        self.items: dict[str, Agg] = {}
        self.checks: list[dict] = []

    def v(self, key: str) -> Decimal | None:
        a = self.items.get(key)
        return a.value if a else None


def _collect(accounts: list[AccountInput], year: int, cats: list[str], opening: bool = False) -> Agg:
    comps, vals, prov = [], [], False
    for a in accounts:
        if a.category not in cats or a.status not in USABLE:
            continue
        raw = (a.opening if opening else a.values).get(year)
        if raw is None:
            continue
        nv, note = normalize(raw, a.category)
        sign = -1 if taxonomy.get(a.category).contra else 1
        vals.append(nv * sign)
        p = a.status not in APPROVED
        prov = prov or p
        comps.append({"account_id": a.id, "account": a.name, "code": a.code, "category": a.category,
                      "original": float(raw), "normalized": float(nv * sign), "status": a.status,
                      "note": note})
    return Agg(ssum(vals), comps, "computed" if comps else "missing", " + ".join(cats), prov)


def _combine(book: YearBook, key: str, parts: list[tuple[str, int]], formula: str) -> Agg:
    vals, comps, prov, any_present = [], [], False, False
    for k, sign in parts:
        a = book.items.get(k)
        if a is None or a.value is None:
            continue
        any_present = True
        vals.append(a.value * sign)
        prov = prov or a.provisional
        comps.append({"aggregate": k, "label": LABELS.get(k, k), "value": float(a.value), "sign": sign})
    return Agg(ssum(vals) if any_present else None, comps, "derived" if any_present else "missing", formula, prov)


def build_year(accounts: list[AccountInput], year: int, additional: dict[str, dict[int, Decimal]],
               assumptions: dict[str, str], opening: bool = False) -> YearBook:
    """Build aggregates for one year. If opening=True, use Opening-balance sheet values instead (BS only)."""
    b = YearBook(year)
    for key, (_, cats) in SUM_DEFS.items():
        b.items[key] = _collect(accounts, year, cats, opening)

    def add(key, parts, formula):
        b.items[key] = _combine(b, key, parts, formula)

    # ---- balance sheet
    b.items["ca"] = _collect(accounts, year, CA_CATS, opening)
    b.items["ca"].formula = "Σ current-asset accounts"
    fa = _collect(accounts, year, NCA_PLUS + ["bs.nca.acc_depreciation"], opening)
    fa.formula = "Land + PP&E (cost) − accumulated depreciation + PP&E (net) + intangibles + LT investments + other"
    b.items["fa"] = fa
    add("ta", [("ca", 1), ("fa", 1)], "CA + FA")
    b.items["cl"] = _collect(accounts, year, CL_CATS, opening)
    b.items["cl"].formula = "Σ current-liability accounts"
    b.items["ncl"] = _collect(accounts, year, NCL_CATS, opening)
    b.items["ncl"].formula = "Σ long-term liability accounts"
    add("tl", [("cl", 1), ("ncl", 1)], "CL + LTL (total debts)")
    b.items["equity"] = _collect(accounts, year, EQ_CATS, opening)
    b.items["equity"].formula = "Paid-in capital + preferred + reserves + retained earnings (monetary equity)"
    add("common_equity", [("equity", 1), ("pref", -1)], "Monetary equity − preferred shares")
    add("tle", [("tl", 1), ("equity", 1)], "Total debts + equity")
    add("ibd", [("notes_payable", 1), ("st_debt", 1), ("lt_loans", 1), ("bonds", 1)], "N/P + ST debt + LT loans + bonds")

    if opening:
        # A composite opening balance is only valid if EVERY usable account in it has an opening value;
        # otherwise a partial sum would silently understate the average.
        groups = {"ca": CA_CATS, "fa": NCA_PLUS + ["bs.nca.acc_depreciation"], "cl": CL_CATS, "ncl": NCL_CATS, "equity": EQ_CATS}
        incomplete = set()
        for gk, cats in groups.items():
            for a in accounts:
                if a.category in cats and a.status in USABLE and a.values and a.opening.get(year) is None:
                    incomplete.add(gk)
        deps = {"ca": ["ca", "ta", "tle"], "fa": ["fa", "ta"], "cl": ["cl", "tl", "tle"], "ncl": ["ncl", "tl", "tle"],
                "equity": ["equity", "common_equity", "tle"]}
        for gk in incomplete:
            for k in deps[gk]:
                b.items[k] = Agg(None, [], "missing", "Opening balances incomplete for this group")
        for key, (_, cats) in SUM_DEFS.items():
            if any(a.category in cats and a.status in USABLE and a.values and a.opening.get(year) is None for a in accounts):
                b.items[key] = Agg(None, [], "missing", "Opening balances incomplete")
        return b

    # ---- income statement
    add("gp", [("sales", 1), ("cogs", -1)], "Sales − COGS")
    add("opex", [("selling", 1), ("ga", 1), ("depreciation", 1), ("other_opex", 1)], "Selling + G&A + depreciation + other opex")
    add("op_income", [("gp", 1), ("opex", -1)], "Gross profit − operating expenses")
    fin_in_ebit = assumptions.get("finance_income_treatment", "in_ebit") == "in_ebit"
    ebit_parts = [("op_income", 1), ("other_income", 1), ("other_expense", -1)] + ([("finance_income", 1)] if fin_in_ebit else [])
    add("ebit", ebit_parts, "Operating income + other income − other expenses" + (" + financial income" if fin_in_ebit else ""))
    # interest: statement first, Additional-Info fallback
    if b.v("interest") is None and "interest_expense" in additional and additional["interest_expense"].get(year) is not None:
        b.items["interest"] = Agg(abs(additional["interest_expense"][year]), [{"additional": "interest_expense"}], "additional",
                                  "Additional Information sheet")
    ebt_parts = [("ebit", 1), ("interest", -1)] + ([] if fin_in_ebit else [("finance_income", 1)])
    add("ebt", ebt_parts, "EBIT − interest" + ("" if fin_in_ebit else " + financial income"))
    add("np", [("ebt", 1), ("tax", -1)], "EBT − taxes")
    for k, cat_key in (("pref_div", "dividends_preferred"), ("common_div", "dividends_common")):
        if b.v(k) is None and cat_key in additional and additional[cat_key].get(year) is not None:
            b.items[k] = Agg(abs(additional[cat_key][year]), [{"additional": cat_key}], "additional", "Additional Information sheet")
    add("ndp", [("np", 1), ("pref_div", -1)], "Net profit − preferred dividends")
    add("re_add", [("ndp", 1), ("common_div", -1)], "Net distributable profit − common dividends")

    # ---- cash flow
    add("ocf", [("cf_op_items", 1)], "Σ operating items")
    add("icf", [("cf_inv_items", 1)], "Σ investing items")
    add("fincf", [("cf_fin_items", 1)], "Σ financing items")

    # ---- reported totals: fall back to them when components are missing, and reconcile when both exist
    rep_cats = {}
    for key, cat in REPORTED.items():
        rep_cats[key] = _collect(accounts, year, [cat])
    for key, rep in rep_cats.items():
        if rep.value is None:
            continue
        mine = b.items.get(key)
        if key in ("opex",):
            pass
        if key in ("ocf", "icf", "fincf") and mine is not None and mine.value is not None:
            diff = mine.value - rep.value
            if abs(diff) > 1:
                b.checks.append({"severity": "warning", "code": "TOTAL_MISMATCH", "aggregate": key,
                                 "message": f"{year}: the listed {LABELS.get(key, key)} items sum to {float(mine.value):,.2f} but the "
                                            f"reported total is {float(rep.value):,.2f}. The reported total is used."})
            rep.source, rep.formula = "reported", "Reported section total"
            b.items[key] = rep
            continue
        if mine is None or mine.value is None:
            rep.source = "reported"
            rep.formula = "Reported subtotal (components not available)"
            b.items[key] = rep
            if key in ("gp", "op_income", "ebit"):
                # rebuild dependants from the reported figure
                pass
        else:
            diff = mine.value - rep.value
            tol = max(Decimal("1"), abs(rep.value) * Decimal("0.005"))
            if abs(diff) > tol:
                b.checks.append({"severity": "warning", "code": "TOTAL_MISMATCH", "aggregate": key,
                                 "message": f"{year}: computed {LABELS.get(key, key)} = {float(mine.value):,.2f} but the "
                                            f"reported subtotal = {float(rep.value):,.2f} (difference {float(diff):,.2f}).",
                                 "computed": float(mine.value), "reported": float(rep.value)})
    # Re-derive downstream IS items if an upstream one came from a reported subtotal only
    for key, parts, formula in (
            ("ebt", ebt_parts, "EBIT − interest"),
            ("np", [("ebt", 1), ("tax", -1)], "EBT − taxes"),
            ("ndp", [("np", 1), ("pref_div", -1)], "NP − preferred dividends"),
            ("re_add", [("ndp", 1), ("common_div", -1)], "NDP − common dividends")):
        if b.items[key].source == "missing":
            add(key, parts, formula)
    if b.v("net_change_cash") is None:
        add("net_change_cash", [("ocf", 1), ("icf", 1), ("fincf", 1)], "OCF + ICF + FinCF")
    elif None not in (b.v("ocf"), b.v("icf"), b.v("fincf")):
        s = b.v("ocf") + b.v("icf") + b.v("fincf")
        if abs(s - b.v("net_change_cash")) > 1:
            b.checks.append({"severity": "warning", "code": "CF_SECTIONS", "aggregate": "net_change_cash",
                             "message": f"{year}: operating + investing + financing = {float(s):,.2f} but reported net change in cash = {float(b.v('net_change_cash')):,.2f}."})
    if None not in (b.v("opening_cash"), b.v("net_change_cash"), b.v("closing_cash")):
        if abs(b.v("opening_cash") + b.v("net_change_cash") - b.v("closing_cash")) > 1:
            b.checks.append({"severity": "warning", "code": "CF_CASH_ROLL", "aggregate": "closing_cash",
                             "message": f"{year}: opening cash + net change ≠ closing cash."})
    if b.v("closing_cash") is not None and b.v("cash") is not None and abs(b.v("closing_cash") - b.v("cash")) > 1:
        b.checks.append({"severity": "info", "code": "CF_BS_CASH", "aggregate": "cash",
                         "message": f"{year}: closing cash in the cash-flow statement ({float(b.v('closing_cash')):,.2f}) differs from balance-sheet cash ({float(b.v('cash')):,.2f}). Definitions of cash equivalents may differ."})
    cap = abs(b.v("capex")) if b.v("capex") is not None else None
    if b.v("ocf") is not None:
        b.items["fcf"] = Agg(b.v("ocf") - (cap or D0), [{"aggregate": "ocf", "value": float(b.v("ocf"))},
                                                       {"aggregate": "capex", "value": float(cap or 0)}],
                             "derived", "OCF − capital expenditure" + ("" if cap is not None else " (capex not reported: assumed 0)"),
                             b.items["ocf"].provisional)

    # ---- additional information
    for k in ("credit_sales", "cash_sales", "credit_purchases", "shares_outstanding", "share_price", "fixed_costs",
              "variable_costs"):
        val = additional.get(k, {}).get(year)
        if val is not None:
            b.items[k] = Agg(val, [{"additional": k}], "additional", "Additional Information sheet")

    # ---- balance check
    ta, tle = b.v("ta"), b.v("tle")
    if (ta is None) != (tle is None):
        ta, tle = ta or D0, tle or D0
    if ta is not None and tle is not None and abs(ta - tle) > max(Decimal(1), abs(ta) * Decimal("0.0005")):
        b.checks.append({"severity": "error", "code": "BS_NOT_BALANCED", "aggregate": "ta",
                         "message": f"{year}: total assets {float(ta):,.2f} ≠ total liabilities + equity {float(tle):,.2f} "
                                    f"(difference {float(ta - tle):,.2f}). Check classifications or missing accounts."})
    return b
