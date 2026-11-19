"""Multi-year (horizontal) statistics with explicit handling of zero / negative bases."""
from __future__ import annotations

from decimal import Decimal

from .num import f


def pct_change(cur: Decimal | None, prev: Decimal | None) -> tuple[Decimal | None, str | None]:
    """(Current − Previous) / |Previous|. Returns (value, flag) where flag explains a non-meaningful case."""
    if cur is None or prev is None:
        return None, "missing"
    if prev == 0:
        return None, "base_zero"
    val = (cur - prev) / abs(prev)
    if (prev < 0) != (cur < 0) and cur != 0:
        return val, "sign_change"
    if prev < 0:
        return val, "negative_base"
    return val, None


def cagr(begin: Decimal | None, end: Decimal | None, periods: int) -> tuple[Decimal | None, str | None]:
    if begin is None or end is None or periods <= 0:
        return None, "missing"
    if begin <= 0 or end <= 0:
        return None, "not_meaningful_non_positive"
    return Decimal(str((float(end) / float(begin)) ** (1 / periods) - 1)), None


FLAG_TEXT = {
    "missing": "Not available — value missing for one of the years.",
    "base_zero": "Not meaningful — the base year value is zero.",
    "sign_change": "Sign changed between years (e.g. profit → loss). The percentage is shown but should be read with care.",
    "negative_base": "Base value is negative; percentage computed on the absolute base.",
    "not_meaningful_non_positive": "CAGR is not meaningful when the first or last value is zero or negative.",
}


def series_stats(values: dict[int, Decimal | None]) -> dict:
    years = sorted(values)
    pts = [(y, values[y]) for y in years]
    changes = []
    for i in range(1, len(pts)):
        (y0, v0), (y1, v1) = pts[i - 1], pts[i]
        p, flag = pct_change(v1, v0)
        changes.append({"year": y1, "from_year": y0, "abs_change": f(None if v0 is None or v1 is None else v1 - v0),
                        "pct_change": f(p), "flag": flag})
    present = [(y, v) for y, v in pts if v is not None]
    out = {"changes": changes, "highest": None, "lowest": None, "average": None, "cumulative_change": None,
           "cumulative_pct": None, "cagr": None, "cagr_flag": None, "trend": "insufficient data"}
    if not present:
        return out
    hi = max(present, key=lambda t: t[1])
    lo = min(present, key=lambda t: t[1])
    out["highest"] = {"year": hi[0], "value": f(hi[1])}
    out["lowest"] = {"year": lo[0], "value": f(lo[1])}
    out["average"] = f(sum(v for _, v in present) / len(present))
    if len(present) >= 2:
        (y0, v0), (yn, vn) = present[0], present[-1]
        out["cumulative_change"] = f(vn - v0)
        cp, cflag = pct_change(vn, v0)
        out["cumulative_pct"] = f(cp)
        out["cumulative_flag"] = cflag
        g, gflag = cagr(v0, vn, yn - y0)
        out["cagr"], out["cagr_flag"] = f(g), gflag
        out["trend"] = trend_direction([v for _, v in present])
    return out


def trend_direction(vals: list[Decimal]) -> str:
    diffs = [b - a for a, b in zip(vals, vals[1:])]
    if not diffs:
        return "insufficient data"
    base = max(abs(v) for v in vals) or Decimal(1)
    small = [abs(d) <= base * Decimal("0.01") for d in diffs]
    if all(small):
        return "stable"
    ups = sum(1 for d, s in zip(diffs, small) if d > 0 and not s)
    downs = sum(1 for d, s in zip(diffs, small) if d < 0 and not s)
    if downs == 0:
        return "increasing"
    if ups == 0:
        return "decreasing"
    return "mostly increasing" if ups > downs and vals[-1] > vals[0] else (
        "mostly decreasing" if downs > ups and vals[-1] < vals[0] else "volatile")
