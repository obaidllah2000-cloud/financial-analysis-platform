"""Forecasting & planning (Lectures 5–8, Q4 solution).

  forecast_position   Forecasted financial position — staged iteration with a financial hierarchy (Lecture 5, Q4)
  percent_of_sales    % of sales method with AFN and sustainable sales (Lecture 6)
  breakeven           Break-even & operating leverage (Lecture 8)
  cash_budget         Monthly cash-flow forecast with surplus / deficit (Lecture 7)

All arithmetic is Decimal. `course_rounding=True` rounds every line to whole units at each stage, like
the hand-worked solutions; the default keeps full precision.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

D0 = Decimal(0)


def _r(x: Decimal, on: bool) -> Decimal:
    return x.quantize(Decimal(1), rounding=ROUND_HALF_UP) if on else x


def f(x):
    return None if x is None else float(round(x, 4))


# ---------------------------------------------------------------- simple formulas (kept for tests / API)
def afn(spontaneous_assets: Decimal, spontaneous_liabilities: Decimal, s1: Decimal, s2: Decimal,
        profit_margin: Decimal, payout: Decimal) -> Decimal:
    """Financial sources needed (Lecture 6, slide 5): A/S1·ΔS − L/S1·ΔS − P·S2·(1 − D)."""
    ds = s2 - s1
    return spontaneous_assets / s1 * ds - spontaneous_liabilities / s1 * ds - profit_margin * s2 * (1 - payout)


def sustainable_sales(spontaneous_assets, spontaneous_liabilities, s1, profit_margin, payout) -> Decimal:
    """Sales level at which AFN = 0 (Lecture 6, slide 7)."""
    k = spontaneous_assets / s1 - spontaneous_liabilities / s1
    return k * s1 / (k - profit_margin * (1 - payout))


def breakeven_units(fc: Decimal, price: Decimal, avc: Decimal) -> Decimal:
    """Q = FC / (P − AVC) (Lecture 8, slide 2)."""
    return fc / (price - avc)


def breakeven_sales(fc: Decimal, vc: Decimal, sales: Decimal) -> Decimal:
    """Monetary break-even = TFC / (1 − VC / Sales) (Lecture 8, slide 5)."""
    return fc / (1 - vc / sales)


# ---------------------------------------------------------------- forecasted financial position
@dataclass
class BSLine:
    name: str
    value: Decimal
    side: str  # "A" asset | "L" liability | "E" equity
    spontaneous: bool = False  # grows with sales
    role: str | None = None  # "re" | "st_debt" | "lt_debt" | "common" — financing targets / retained earnings
    category: str | None = None


@dataclass
class ISLine:
    name: str
    value: Decimal  # positive magnitude
    kind: str  # "revenue" | "expense" | "other_income" | "other_expense"
    grows: bool = True


@dataclass
class Hierarchy:
    target: str  # st_debt | lt_debt | common
    pct: Decimal
    rate: Decimal = D0  # annual interest rate for debt


@dataclass
class PositionInput:
    is_lines: list[ISLine]
    bs_lines: list[BSLine]
    interest: Decimal
    tax_rate: Decimal
    pref_div: Decimal
    shares: Decimal | None  # common shares outstanding (millions or units — consistent with DPS)
    dps: Decimal | None  # last dividend per share
    common_div: Decimal  # last common dividends (used if shares/DPS unknown)
    growth: Decimal  # sales growth, e.g. 0.1625
    dps_growth: Decimal
    hierarchy: list[Hierarchy]
    share_price: Decimal | None
    eva_rate: Decimal = Decimal("0.10")
    tolerance: Decimal = Decimal("0.5")
    max_stages: int = 25
    course_rounding: bool = False
    notes: list[str] = field(default_factory=list)


def forecast_position(p: PositionInput) -> dict:
    g = 1 + p.growth
    rnd = p.course_rounding
    total_pct = sum((h.pct for h in p.hierarchy), D0)
    if abs(total_pct - 1) > Decimal("0.0001"):
        raise ValueError(f"Financial hierarchy must total 100% (currently {float(total_pct) * 100:.1f}%).")
    cum = {h.target: D0 for h in p.hierarchy}  # cumulative new financing by source
    stages = []
    need = None
    for stage in range(1, p.max_stages + 1):
        # ---- income statement
        is_rows, revenue, expenses = [], D0, D0
        for ln in p.is_lines:
            v = _r(ln.value * g if ln.grows else ln.value, rnd)
            is_rows.append({"name": ln.name, "actual": f(ln.value), "factor": f(g) if ln.grows else None,
                            "value": f(v), "kind": ln.kind, "rule": f"× {float(g):.4f}" if ln.grows else "no change"})
            if ln.kind in ("revenue", "other_income"):
                revenue += v
            else:
                expenses += v
        ebit = revenue - expenses
        new_interest = sum((cum[h.target] * h.rate for h in p.hierarchy if h.target != "common"), D0)
        interest = _r(p.interest + new_interest, rnd)
        ebt = ebit - interest
        tax = _r(ebt * p.tax_rate, rnd) if ebt > 0 else D0
        np_ = ebt - tax
        ndp = np_ - p.pref_div
        new_dps = p.dps * (1 + p.dps_growth) if p.dps is not None else None
        new_shares = D0
        if cum.get("common") and p.share_price:
            new_shares = cum["common"] / p.share_price
        if new_dps is not None and p.shares is not None:
            cs_div = _r((p.shares + new_shares) * new_dps, rnd)
            div_rule = f"({float(p.shares):,.4g} + {float(new_shares):,.4g} new) shares × DPS {float(new_dps):.4f}"
        else:
            cs_div = _r(p.common_div * (1 + p.dps_growth), rnd)
            div_rule = "last common dividends × (1 + DPS growth) — shares/DPS not provided"
        re_add = ndp - cs_div
        is_summary = {"revenue": f(revenue), "operating_expenses": f(expenses), "ebit": f(ebit), "interest": f(interest),
                      "new_interest": f(new_interest), "ebt": f(ebt), "tax": f(tax), "np": f(np_), "pref_div": f(p.pref_div),
                      "ndp": f(ndp), "common_div": f(cs_div), "dividend_rule": div_rule, "re_addition": f(re_add),
                      "new_shares": f(new_shares), "new_dps": f(new_dps)}
        # ---- financial position
        bs_rows, assets, claims = [], D0, D0
        used_targets = set()
        for ln in p.bs_lines:
            if ln.role == "re":
                v = _r(ln.value + re_add, rnd)
                rule = "previous R/E + retained profit"
            elif ln.spontaneous:
                v = _r(ln.value * g, rnd)
                rule = f"× {float(g):.4f}"
            else:
                v = ln.value
                rule = "no change"
            if ln.role in cum and ln.role not in used_targets:
                v = _r(v + cum[ln.role], rnd)
                used_targets.add(ln.role)
                if cum[ln.role]:
                    rule += f" + new financing {float(cum[ln.role]):,.2f}"
            bs_rows.append({"name": ln.name, "side": ln.side, "actual": f(ln.value), "value": f(v), "rule": rule, "role": ln.role})
            if ln.side == "A":
                assets += v
            else:
                claims += v
        for t, amt in cum.items():  # financing source with no existing line
            if t not in used_targets and amt:
                label = {"st_debt": "New short-term debt", "lt_debt": "New long-term debt", "common": "New common shares"}[t]
                v = _r(amt, rnd)
                bs_rows.append({"name": label, "side": "E" if t == "common" else "L", "actual": 0.0, "value": f(v),
                                "rule": "new financing", "role": t})
                claims += v
        need = assets - claims
        re_close = sum((Decimal(str(r["value"])) for r in bs_rows if r["role"] == "re"), D0)
        is_summary["eva"] = f(np_ - (interest + p.pref_div + cs_div + p.eva_rate * re_close))
        split = [{"target": h.target, "pct": f(h.pct), "amount": f(_r(need * h.pct, rnd)), "rate": f(h.rate),
                  "annual_interest": f(need * h.pct * h.rate) if h.target != "common" else None,
                  "new_shares": f(need * h.pct / p.share_price) if h.target == "common" and p.share_price else None}
                 for h in p.hierarchy]
        stages.append({"stage": stage, "income_statement": is_rows, "is_summary": is_summary, "balance_sheet": bs_rows,
                       "total_assets": f(assets), "total_claims": f(claims), "financing_need": f(need),
                       "cumulative_financing": {k: f(v) for k, v in cum.items()}, "next_split": split})
        if abs(need) <= p.tolerance:
            break
        for h in p.hierarchy:
            cum[h.target] += _r(need * h.pct, rnd) if rnd else need * h.pct
    converged = need is not None and abs(need) <= p.tolerance
    # actual year, same definitions (Q4 compares EVA before / after the expansion)
    rev0 = sum((l.value for l in p.is_lines if l.kind in ("revenue", "other_income")), D0)
    exp0 = sum((l.value for l in p.is_lines if l.kind not in ("revenue", "other_income")), D0)
    ebt0 = rev0 - exp0 - p.interest
    np0 = ebt0 - (ebt0 * p.tax_rate if ebt0 > 0 else D0)
    re0 = sum((l.value for l in p.bs_lines if l.role == "re"), D0)
    actual = {"ebit": f(rev0 - exp0), "interest": f(p.interest), "ebt": f(ebt0), "np": f(np0), "common_div": f(p.common_div),
              "eva": f(np0 - (p.interest + p.pref_div + p.common_div + p.eva_rate * re0)), "eva_rate": f(p.eva_rate)}
    return {"stages": stages, "converged": converged, "actual": actual, "total_new_financing": {k: f(v) for k, v in cum.items()},
            "notes": p.notes + ([] if converged else [f"Did not converge within {p.max_stages} stages."])}


# ---------------------------------------------------------------- % of sales
def percent_of_sales(bs_lines: list[BSLine], s1: Decimal, s2: Decimal, margin: Decimal, payout: Decimal,
                     afn_target: str = "st_debt") -> dict:
    rows, a1, a2, l2, sa, sl = [], D0, D0, D0, D0, D0
    for ln in bs_lines:
        if ln.role == "re":
            v2 = ln.value + margin * s2 * (1 - payout)
            pct = None
        elif ln.spontaneous:
            pct = ln.value / s1
            v2 = pct * s2
            if ln.side == "A":
                sa += ln.value
            else:
                sl += ln.value
        else:
            pct, v2 = None, ln.value
        rows.append({"name": ln.name, "side": ln.side, "actual": f(ln.value), "pct_of_sales": f(pct), "projected": f(v2),
                     "spontaneous": ln.spontaneous, "role": ln.role, "category": ln.category})
        if ln.side == "A":
            a1 += ln.value
            a2 += v2
        else:
            l2 += v2
    need = a2 - l2
    formula = afn(sa, sl, s1, s2, margin, payout)

    def sums(lines, projected: bool, extra: Decimal):
        ca = cl = td = D0
        for r in lines:
            v = Decimal(str(r["projected"] if projected else r["actual"]))
            cat = r["category"] or ""
            if cat.startswith("bs.ca."):
                ca += v
            if cat.startswith("bs.cl."):
                cl += v
            if cat.startswith(("bs.cl.", "bs.ncl.")):
                td += v
        if afn_target == "st_debt":
            cl += extra
            td += extra
        elif afn_target == "lt_debt":
            td += extra
        return ca, cl, td

    ca1, cl1, td1 = sums(rows, False, D0)
    ca2, cl2, td2 = sums(rows, True, max(need, D0))
    k = sa / s1 - sl / s1
    denom = k - margin * (1 - payout)
    sus = k * s1 / denom if denom > 0 else None
    return {"rows": rows, "s1": f(s1), "s2": f(s2), "total_assets_actual": f(a1), "total_assets_projected": f(a2),
            "claims_projected": f(l2), "afn": f(need), "afn_formula": f(formula),
            "formula_text": f"A/S1·ΔS − L/S1·ΔS − P·S2·(1−D) = {float(sa / s1):.4f}×{float(s2 - s1):,.2f} − "
                            f"{float(sl / s1):.4f}×{float(s2 - s1):,.2f} − {float(margin):.4f}×{float(s2):,.2f}×{float(1 - payout):.4f}",
            "sustainable_sales": f(sus), "afn_financed_by": afn_target,
            "ratios": {"current_ratio_before": f(ca1 / cl1) if cl1 else None, "current_ratio_after": f(ca2 / cl2) if cl2 else None,
                       "debt_ratio_before": f(td1 / a1) if a1 else None, "debt_ratio_after": f(td2 / a2) if a2 else None}}


# ---------------------------------------------------------------- break-even
def breakeven(fc: Decimal, price: Decimal | None = None, avc: Decimal | None = None, sales: Decimal | None = None,
              vc: Decimal | None = None, units: Decimal | None = None) -> dict:
    out: dict = {"fc": f(fc)}
    if price is not None and avc is not None:
        if price <= avc:
            raise ValueError("Selling price must exceed average variable cost.")
        q = breakeven_units(fc, price, avc)
        out |= {"bep_units": f(q), "bep_value": f(q * price), "cm_per_unit": f(price - avc)}
        if units is not None:
            sales, vc = units * price, units * avc
        maxq = max(q * 2, units or 0)
        out["chart"] = [{"q": f(maxq * i / 10), "tr": f(maxq * i / 10 * price), "tc": f(fc + maxq * i / 10 * avc), "fc": f(fc)} for i in range(11)]
    if sales is not None and vc is not None and sales > 0:
        cmr = 1 - vc / sales
        if cmr <= 0:
            raise ValueError("Variable costs exceed sales: no break-even point exists.")
        bep = fc / cmr
        ebit = sales - vc - fc
        out |= {"sales": f(sales), "vc": f(vc), "cm_ratio": f(cmr), "bep_sales": f(bep), "operating_profit": f(ebit),
                "margin_of_safety": f((sales - bep) / sales), "dol": f((sales - vc) / ebit) if ebit else None}
        if "chart" not in out:
            mx = max(bep * 2, sales)
            out["chart"] = [{"q": f(mx * i / 10), "tr": f(mx * i / 10), "tc": f(fc + mx * i / 10 * (1 - cmr)), "fc": f(fc)} for i in range(11)]
    return out


# ---------------------------------------------------------------- cash budget
def cash_budget(months: list[str], sales: list[Decimal], cash_pct: Decimal, lags: list[Decimal], other_receipts: list[Decimal],
                payments: dict[str, list[Decimal]], opening: Decimal, min_cash: Decimal, show_from: int = 0) -> dict:
    """Collections: cash_pct of sales now; the credit part (1 − cash_pct) collected by `lags` (lag 1, lag 2, …)."""
    credit = 1 - cash_pct
    rows, bal = [], opening
    for i, m in enumerate(months):
        cash_s = sales[i] * cash_pct
        coll = [sales[i - k - 1] * credit * lag if i - k - 1 >= 0 else D0 for k, lag in enumerate(lags)]
        rec = cash_s + sum(coll, D0) + (other_receipts[i] if i < len(other_receipts) else D0)
        pay = {k: (v[i] if i < len(v) else D0) for k, v in payments.items()}
        out_ = sum(pay.values(), D0)
        if i < show_from:
            continue
        net = rec - out_
        bal = bal + net
        rows.append({"month": m, "sales": f(sales[i]), "cash_sales": f(cash_s), "collections": [f(c) for c in coll],
                     "other_receipts": f(other_receipts[i] if i < len(other_receipts) else D0), "receipts": f(rec),
                     "payments": {k: f(v) for k, v in pay.items()}, "total_payments": f(out_), "net": f(net),
                     "closing_balance": f(bal), "min_cash": f(min_cash), "surplus_deficit": f(bal - min_cash)})
    return {"rows": rows, "peak_deficit": min((r["surplus_deficit"] for r in rows), default=None)}
