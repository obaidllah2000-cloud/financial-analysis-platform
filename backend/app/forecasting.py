"""Builds forecasting inputs from the company's latest approved data, and runs scenarios from user edits."""
from __future__ import annotations

from decimal import Decimal

from . import taxonomy
from .engine.aggregate import USABLE, normalize
from .engine.analysis import Analysis
from .engine import forecast as fc

SPONTANEOUS = {"bs.ca.cash", "bs.ca.receivables", "bs.ca.notes_receivable", "bs.ca.inventory", "bs.ca.prepaid", "bs.ca.other",
               "bs.nca.ppe_gross", "bs.nca.acc_depreciation", "bs.nca.ppe_net", "bs.cl.payables", "bs.cl.accrued",
               "bs.cl.advance_revenue", "bs.cl.tax_payable"}
ROLE = {"bs.cl.notes_payable": "st_debt", "bs.cl.st_debt": "st_debt", "bs.ncl.bonds": "lt_debt", "bs.ncl.lt_loans": "lt_debt",
        "bs.eq.common": "common", "bs.eq.retained": "re"}
IS_KIND = {"is.revenue": "revenue", "is.cogs": "expense", "is.opex.selling": "expense", "is.opex.ga": "expense",
           "is.opex.depreciation": "expense", "is.opex.other": "expense", "is.other_income": "other_income",
           "is.other_expense": "other_expense", "is.finance_income": "other_income"}


def _f(x):
    return None if x is None else float(x)


def base(an: Analysis, benchmarks: dict) -> dict:
    y = an.years[-1]
    b = an.books[y]
    bs, is_, roles_taken = [], [], set()
    for a in an.accounts:
        cat = taxonomy.get(a.category)
        v = a.values.get(y)
        if v is None or a.status not in USABLE or cat.subtotal or a.category == "unclassified":
            continue
        nv, _ = normalize(v, a.category)
        if a.statement == "BS":
            role = ROLE.get(a.category)
            if role in roles_taken and role != "re":
                role = None
            if role:
                roles_taken.add(role)
            bs.append({"name": a.name, "value": float(-nv if cat.contra else nv), "side": {"Asset": "A", "Liability": "L"}.get(cat.element, "E"),
                       "spontaneous": a.category in SPONTANEOUS, "role": role, "category": a.category, "status": a.status})
        elif a.statement == "IS" and a.category in IS_KIND:
            kind = IS_KIND[a.category]
            is_.append({"name": a.name, "value": float(nv), "kind": kind, "grows": kind in ("revenue", "expense"), "category": a.category,
                        "status": a.status})
    sales, np_, cdiv = b.v("sales"), b.v("np"), b.v("common_div")
    shares = b.v("shares_outstanding")
    ebt, tax = b.v("ebt"), b.v("tax")
    return {
        "year": y, "currency": an.ccy, "bs_lines": bs, "is_lines": is_,
        "interest": _f(b.v("interest") or 0), "tax_rate": _f(tax / ebt) if tax is not None and ebt else 0.0,
        "pref_div": _f(b.v("pref_div") or 0), "common_div": _f(cdiv or 0), "shares": _f(shares),
        "dps": _f(cdiv / shares) if cdiv is not None and shares else None, "share_price": _f(b.v("share_price")),
        "sales": _f(sales), "profit_margin": _f(np_ / sales) if np_ is not None and sales else None,
        "payout": _f(cdiv / np_) if cdiv is not None and np_ else 0.0,
        "fixed_costs": _f(b.v("fixed_costs")), "variable_costs": _f(b.v("variable_costs")),
        "benchmarks": {k: benchmarks.get(k) for k in ("current_ratio", "debt_ratio")},
        "provisional": any(x["status"] not in ("approved", "modified") for x in bs + is_),
    }


def D(x) -> Decimal:
    return Decimal(str(x if x not in (None, "") else 0))


def _bs(lines) -> list[fc.BSLine]:
    return [fc.BSLine(l["name"], D(l["value"]), l["side"], bool(l.get("spontaneous")), l.get("role") or None, l.get("category"))
            for l in lines if l.get("include", True)]


def run_position(p: dict) -> dict:
    inp = fc.PositionInput(
        is_lines=[fc.ISLine(l["name"], D(l["value"]), l["kind"], bool(l.get("grows"))) for l in p["is_lines"] if l.get("include", True)],
        bs_lines=_bs(p["bs_lines"]), interest=D(p["interest"]), tax_rate=D(p["tax_rate"]), pref_div=D(p["pref_div"]),
        shares=D(p["shares"]) if p.get("shares") else None, dps=D(p["dps"]) if p.get("dps") not in (None, "") else None,
        common_div=D(p["common_div"]), growth=D(p["growth"]), dps_growth=D(p["dps_growth"]),
        hierarchy=[fc.Hierarchy(h["target"], D(h["pct"]), D(h.get("rate") or 0)) for h in p["hierarchy"] if D(h["pct"]) > 0],
        share_price=D(p["share_price"]) if p.get("share_price") else None, course_rounding=bool(p.get("course_rounding")),
        tolerance=D(p.get("tolerance") or "0.5"), eva_rate=D(p.get("eva_rate") or "0.10"))
    if any(h.target == "common" for h in inp.hierarchy) and not inp.share_price:
        inp.notes.append("No share price given: new shares (and their dividends) cannot be computed.")
    return fc.forecast_position(inp)


def run_percent(p: dict) -> dict:
    return fc.percent_of_sales(_bs(p["bs_lines"]), D(p["s1"]), D(p["s2"]), D(p["profit_margin"]), D(p["payout"]),
                               p.get("afn_target", "st_debt"))
