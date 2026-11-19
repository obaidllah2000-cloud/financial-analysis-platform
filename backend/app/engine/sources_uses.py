"""Sources & Uses of Money statement (Lecture 2; Q3 solution).

Rules (movement logic):
  Asset ↑ = Use        Asset ↓ = Source
  Liability / equity ↑ = Source   Liability / equity ↓ = Use
  Contra-asset (accumulated depreciation) ↑ = Source (it reduces assets)
Short-term vs long-term follows the account group (current items = short term; fixed assets, LTL and
equity = long term). Internal sources = retained earnings / reserves growth, depreciation and
liquidation of assets; external = new liabilities and new share capital (Q3 solution).
"""
from __future__ import annotations

from decimal import Decimal

from .. import taxonomy
from .aggregate import USABLE, AccountInput, normalize
from .num import f


def build(accounts: list[AccountInput], y0: int, y1: int) -> dict:
    rows = []
    for a in accounts:
        cat = taxonomy.get(a.category)
        if cat.statement != "BS" or cat.subtotal or a.category == "unclassified" or a.status not in USABLE:
            continue
        o_raw, c_raw = a.values.get(y0), a.values.get(y1)
        if o_raw is None and c_raw is None:
            continue
        o = normalize(o_raw, a.category)[0] if o_raw is not None else Decimal(0)
        c = normalize(c_raw, a.category)[0] if c_raw is not None else Decimal(0)
        ch = c - o
        if ch == 0:
            kind = None
        elif cat.element == "Asset" and not cat.contra:
            kind = "use" if ch > 0 else "source"
        else:  # liabilities, equity, contra-assets
            kind = "source" if ch > 0 else "use"
        term = "short" if cat.group == "Current" else "long"
        internal = None
        if kind == "source":
            if cat.element == "Asset" or cat.contra or a.category in ("bs.eq.retained", "bs.eq.reserves"):
                internal = True
            else:
                internal = False
        desc = _describe(a.name, cat, ch, kind)
        rows.append({"account_id": a.id, "account": a.name, "category": a.category, "element": cat.element,
                     "group": cat.group, "opening": f(o), "closing": f(c), "change": f(ch), "type": kind,
                     "term": term, "internal": internal, "description": desc, "status": a.status,
                     "missing_side": o_raw is None or c_raw is None})
    src = sum((abs(Decimal(str(r["change"]))) for r in rows if r["type"] == "source"), Decimal(0))
    use = sum((abs(Decimal(str(r["change"]))) for r in rows if r["type"] == "use"), Decimal(0))
    for r in rows:
        amt = abs(Decimal(str(r["change"])))
        r["amount"] = f(amt)
        base = src if r["type"] == "source" else use
        r["pct"] = f(amt / base) if r["type"] and base else None

    def share(kind, pred):
        base = src if kind == "source" else use
        tot = sum((abs(Decimal(str(r["change"]))) for r in rows if r["type"] == kind and pred(r)), Decimal(0))
        return f(tot / base) if base else None

    st_src, st_use = share("source", lambda r: r["term"] == "short"), share("use", lambda r: r["term"] == "short")
    out = {
        "from_year": y0, "to_year": y1, "rows": rows,
        "total_sources": f(src), "total_uses": f(use), "difference": f(src - use),
        "reconciled": abs(src - use) <= 1,
        "short_term_sources_pct": st_src, "long_term_sources_pct": share("source", lambda r: r["term"] == "long"),
        "short_term_uses_pct": st_use, "long_term_uses_pct": share("use", lambda r: r["term"] == "long"),
        "internal_sources_pct": share("source", lambda r: r["internal"] is True),
        "external_sources_pct": share("source", lambda r: r["internal"] is False),
    }
    out["golden_rule_deviation"] = None if st_src is None or st_use is None else round(abs(st_src - st_use), 6)
    return out


def _describe(name, cat, ch, kind):
    if kind is None:
        return "No change"
    up = ch > 0
    if cat.contra:
        return f"Increase in {name} (non-cash charge retained in the business)" if up else f"Decrease in {name}"
    if cat.element == "Asset":
        return f"Increase in {name}" if up else (f"Liquidation / decrease of {name}" if cat.group == "Non-Current" else f"Decrease in {name}")
    if cat.element == "Liability":
        return f"Increase in {name} (new financing)" if up else f"Repayment / decrease of {name}"
    return f"Increase in {name}" if up else f"Decrease in {name}"
