"""Analysis orchestrator: aggregates → horizontal/vertical → ratios (with status & trace) → sources & uses."""
from __future__ import annotations

from decimal import Decimal

from .. import taxonomy
from .aggregate import APPROVED, LABELS, USABLE, AccountInput, YearBook, build_year, normalize
from .num import f
from .ratios import BY_KEY as RATIO_BY_KEY, RATIOS, Ctx
from .sources_uses import build as build_su
from .trends import FLAG_TEXT, series_stats

KEY_LINES = [  # standardised multi-year summary (spec section 8)
    ("sales", "IS"), ("cogs", "IS"), ("gp", "IS"), ("opex", "IS"), ("op_income", "IS"), ("ebit", "IS"), ("interest", "IS"),
    ("ebt", "IS"), ("tax", "IS"), ("np", "IS"),
    ("cash", "BS"), ("st_inv", "BS"), ("ar", "BS"), ("inventory", "BS"), ("ca", "BS"), ("fa", "BS"), ("ta", "BS"),
    ("cl", "BS"), ("ncl", "BS"), ("tl", "BS"), ("ibd", "BS"), ("equity", "BS"),
    ("ocf", "CF"), ("icf", "CF"), ("fincf", "CF"), ("net_change_cash", "CF"), ("fcf", "CF"),
]

BS_KEYS = {"cash", "st_inv", "ar", "inventory", "prepaid", "other_ca", "land", "ppe_gross", "acc_dep", "ppe_net_reported",
           "intangibles", "lt_inv", "other_nca", "ap", "notes_payable", "accrued", "st_debt", "adv_rev", "tax_payable",
           "other_cl", "lt_loans", "bonds", "other_ncl", "pref", "common", "reserves", "retained", "other_eq", "ca", "fa",
           "ta", "cl", "ncl", "tl", "equity", "common_equity", "tle", "ibd"}

STATUS_ORDER = ["verified", "approved_assumption", "provisional", "needs_info", "invalid"]
STATUS_TEXT = {
    "verified": "Calculated and verified — all inputs approved, no assumptions involved.",
    "approved_assumption": "Based on analyst-approved assumptions.",
    "provisional": "Provisional — uses pending classifications or unapproved assumptions.",
    "needs_info": "Requires additional information.",
    "invalid": "Invalid — critical validation error or mathematically undefined.",
}


def fmt(v, unit: str, ccy: str = "") -> str:
    if v is None:
        return "n/a"
    if unit == "text":
        return str(v)
    x = float(v)
    if unit == "%":
        return f"{x * 100:.2f}%"
    if unit == "days":
        return f"{x:,.1f} days"
    if unit == "ccy":
        return f"{x:,.0f} {ccy}".strip()
    return f"{x:,.2f}"


class Analysis:
    def __init__(self, accounts: list[AccountInput], years: list[int], additional: dict, assumptions: dict[str, str],
                 assumption_status: dict[str, str] | None = None, benchmarks: dict | None = None,
                 methodology: str = "academic", currency: str = "", blocking_errors: dict[int, list[str]] | None = None):
        self.accounts, self.years = accounts, sorted(years)
        self.additional, self.assumptions = additional, assumptions
        self.assumption_status = assumption_status or {}
        self.benchmarks = benchmarks or {}
        self.methodology, self.ccy = methodology, currency
        self.blocking = blocking_errors or {}
        self.books: dict[int, YearBook] = {y: build_year(accounts, y, additional, assumptions) for y in self.years}
        first = self.years[0] if self.years else None
        self.opening_book = build_year(accounts, first, {}, assumptions, opening=True) if first is not None else None

    # ---------------------------------------------------------------- ratios
    def ratio_value(self, key: str, year: int, assumptions: dict | None = None):
        r = RATIO_BY_KEY[key]
        a = assumptions or self.assumptions
        books = self.books if assumptions is None else {y: build_year(self.accounts, y, self.additional, a) for y in self.years}
        prev = books.get(year - 1) if (year - 1) in books else None
        ctx = Ctx(year, books[year], prev, self.opening_book if year == self.years[0] else None, a)
        try:
            val = r.compute(ctx)
        except (ZeroDivisionError, ArithmeticError):
            val = None
        return val, ctx

    def ratio_cell(self, key: str, year: int) -> dict:
        r = RATIO_BY_KEY[key]
        val, ctx = self.ratio_value(key, year)
        book = self.books[year]
        prov_inputs = [k for k in ctx.used if k in book.items and book.items[k].provisional]
        missing = [k for k, v in ctx.used.items() if v is None and not k.startswith(("opening_", "avg_"))]
        used_assumptions = sorted(ctx.assumptions_used)
        unapproved = [k for k in used_assumptions if self.assumption_status.get(k, "pending") not in ("accepted", "modified")]
        rejected = [k for k in used_assumptions if self.assumption_status.get(k) == "rejected"]
        reasons = []
        bs_inputs = [k for k in ctx.used if k in BS_KEYS]
        bs_errors = [c["message"] for c in book.checks if c["severity"] == "error"] if bs_inputs else []
        if self.blocking.get(year) or bs_errors:
            status = "invalid"
            reasons += self.blocking.get(year, []) + bs_errors
        elif val is None:
            if ctx.excluded:
                status = "needs_info"
                reasons.append("Excluded by an approved assumption until more information is available.")
            elif missing:
                status = "needs_info"
                reasons.append("Missing: " + ", ".join(LABELS.get(k, k) for k in missing))
            else:
                status = "invalid"
                reasons.append("Mathematically undefined (zero or non-meaningful denominator).")
            if rejected:
                status = "needs_info"
                reasons.append("Assumption rejected by analyst: " + ", ".join(rejected))
        elif rejected:
            status, val = "needs_info", None
            reasons.append("Assumption rejected by analyst: " + ", ".join(rejected))
        elif prov_inputs or unapproved:
            status = "provisional"
            if prov_inputs:
                reasons.append("Pending classification in: " + ", ".join(LABELS.get(k, k) for k in prov_inputs))
            if unapproved:
                reasons.append("Assumption not yet approved: " + ", ".join(unapproved))
        elif used_assumptions:
            status = "approved_assumption"
        else:
            status = "verified"
        num = val if not isinstance(val, Decimal) else val
        return {"year": year, "value": f(num) if isinstance(num, Decimal) else num, "display": fmt(num, r.unit, self.ccy),
                "status": status, "reasons": reasons, "notes": ctx.notes, "assumptions": used_assumptions,
                "inputs": {k: f(v) for k, v in ctx.used.items()}}

    def ratio_trace(self, key: str, year: int) -> dict:
        r = RATIO_BY_KEY[key]
        cell = self.ratio_cell(key, year)
        book = self.books[year]
        inputs = []
        for k in cell["inputs"]:
            agg = book.items.get(k)
            inputs.append({"key": k, "label": LABELS.get(k, k), "value": cell["inputs"][k],
                           "detail": agg.to_dict() if agg else None})
        return {"ratio": self.ratio_meta(r), "year": year, "cell": cell, "inputs": inputs,
                "assumption_values": {k: self.assumptions.get(k) for k in cell["assumptions"]},
                "assumption_status": {k: self.assumption_status.get(k, "pending") for k in cell["assumptions"]},
                "status_text": STATUS_TEXT[cell["status"]]}

    @staticmethod
    def ratio_meta(r) -> dict:
        return {"key": r.key, "name_en": r.name_en, "name_ar": r.name_ar, "category": r.category, "methodology": r.methodology,
                "formula": r.formula, "unit": r.unit, "higher_is_better": r.higher_is_better, "source": r.source,
                "assumptions": r.assumptions, "critical": r.critical}

    def ratios(self, methodology_filter: str | None = None) -> list[dict]:
        meth = methodology_filter or self.methodology
        out = []
        for r in RATIOS:
            # cash-flow ratios have no academic counterpart in the lectures, so the academic view keeps them as supplementary
            if meth == "academic" and r.methodology == "professional" and r.category != "cashflow":
                continue
            if meth == "professional" and r.key in ("tato_credit", "tato_cash", "best_liquidity_measure", "roe_identity", "cato", "cash_turnover"):
                continue
            cells = [self.ratio_cell(r.key, y) for y in self.years]
            series = {c["year"]: Decimal(str(c["value"])) if isinstance(c["value"], (int, float)) else None for c in cells}
            stats = series_stats(series) if r.unit != "text" else {"changes": []}
            latest = next((c for c in reversed(cells) if c["value"] is not None), None)
            bench = self.benchmarks.get(r.key)
            risk, risk_basis = self._risk(r, cells, bench)
            interp = r.interpret.format(v=latest["display"]) if latest else "Not enough data to interpret."
            comment = self._comment(r, cells, bench)
            out.append({**self.ratio_meta(r), "cells": cells, "stats": stats, "benchmark": bench, "risk": risk,
                        "risk_basis": risk_basis, "interpretation": interp, "comment": comment,
                        "action": r.action_if_weak if risk in ("High", "Medium") else ""})
        return out

    def _risk(self, r, cells, bench):
        vals = [c for c in cells if isinstance(c["value"], (int, float))]
        if not vals or r.higher_is_better is None:
            return "n/a", "Direction-neutral or not available"
        v = vals[-1]["value"]
        # hard rules first
        hard = {"current_ratio": lambda x: x < 1, "interest_coverage": lambda x: x < 1.5, "nim": lambda x: x < 0,
                "ocf": lambda x: x < 0, "roi": lambda x: x < 0, "debt_ratio": lambda x: x > 0.8, "fcf": lambda x: x < 0}
        if r.key in hard and hard[r.key](v):
            return "High", "Absolute threshold breached"
        if bench and bench.get("value") not in (None, 0):
            b = bench["value"]
            q = v / b
            if r.higher_is_better:
                return ("Low" if q >= 1 else "Medium" if q >= 0.8 else "High"), f"Benchmark ({bench.get('source', 'user')})"
            return ("Low" if q <= 1 else "Medium" if q <= 1.2 else "High"), f"Benchmark ({bench.get('source', 'user')})"
        if len(vals) >= 2:
            p = vals[-2]["value"]
            if p:
                ch = (v - p) / abs(p)
                worse = ch < -0.10 if r.higher_is_better else ch > 0.10
                return ("Medium" if worse else "Low"), "Historical trend only — no benchmark available (limitation)"
        return "n/a", "Single year and no benchmark — cannot assess"

    def _comment(self, r, cells, bench) -> str:
        vals = [c for c in cells if isinstance(c["value"], (int, float))]
        parts = []
        if len(vals) >= 2 and r.higher_is_better is not None:
            a, b = vals[0], vals[-1]
            better = (b["value"] > a["value"]) == bool(r.higher_is_better)
            if b["value"] != a["value"]:
                parts.append(f"{'Improved' if better else 'Deteriorated'} from {a['display']} ({a['year']}) to {b['display']} ({b['year']}).")
        if bench and vals:
            b = bench["value"]
            v = vals[-1]["value"]
            rel = "above" if v > b else "below" if v < b else "equal to"
            parts.append(f"Latest value is {rel} the benchmark of {fmt(Decimal(str(b)), r.unit, self.ccy)} ({bench.get('source', '')}).")
        elif vals:
            parts.append("No benchmark set — assessment relies on the company's own trend.")
        return " ".join(parts)

    # ---------------------------------------------------------------- statements
    def statement_rows(self, statement: str) -> list[dict]:
        rows = []
        for a in self.accounts:
            cat = taxonomy.get(a.category)
            if a.statement != statement:
                continue
            vals, norm_vals, notes = {}, {}, []
            for y in self.years:
                v = a.values.get(y)
                vals[y] = f(v)
                nv, note = normalize(v, a.category)
                norm_vals[y] = f(nv)
                if note:
                    notes.append(f"{y}: {note}")
            base_key = "ta" if statement == "BS" else "sales" if statement == "IS" else None
            common = {}
            for y in self.years:
                base = self.books[y].v(base_key) if base_key else None
                nv = norm_vals[y]
                common[y] = None if base in (None, 0) or nv is None else round(nv / float(base), 6)
            series = {y: (Decimal(str(norm_vals[y])) if norm_vals[y] is not None else None) for y in self.years}
            rows.append({"account_id": a.id, "code": a.code, "account": a.name, "category": a.category,
                         "category_label": cat.label_en, "category_label_ar": cat.label_ar, "element": cat.element,
                         "group": cat.group, "subtotal": cat.subtotal, "status": a.status, "values": vals,
                         "normalized": norm_vals, "common_size": common, "stats": series_stats(series),
                         "normalization_notes": notes, "used_in_calculations": a.status in USABLE and not cat.subtotal,
                         "approved": a.status in APPROVED})
        return rows

    def key_lines(self) -> list[dict]:
        out = []
        for key, st in KEY_LINES:
            series = {y: self.books[y].v(key) for y in self.years}
            if all(v is None for v in series.values()):
                continue
            base = "ta" if st == "BS" else "sales" if st == "IS" else None
            cs = {}
            for y in self.years:
                b = self.books[y].v(base) if base else None
                v = series[y]
                cs[y] = None if b in (None, 0) or v is None else f(v / b)
            out.append({"key": key, "label": LABELS.get(key, key), "statement": st,
                        "values": {y: f(v) for y, v in series.items()}, "common_size": cs,
                        "sources": {y: (self.books[y].items[key].source if key in self.books[y].items else "missing") for y in self.years},
                        "provisional": any(self.books[y].items.get(key) and self.books[y].items[key].provisional for y in self.years),
                        "stats": series_stats(series)})
        return out

    def aggregate_detail(self, key: str, year: int) -> dict | None:
        a = self.books[year].items.get(key)
        return a.to_dict() | {"label": LABELS.get(key, key)} if a else None

    def sources_uses(self) -> list[dict]:
        return [build_su(self.accounts, y0, y1) for y0, y1 in zip(self.years, self.years[1:])]

    def checks(self) -> list[dict]:
        out = []
        for y in self.years:
            out += [c | {"year": y} for c in self.books[y].checks]
        return out

    def full(self) -> dict:
        return {"years": self.years, "methodology": self.methodology, "currency": self.ccy,
                "key_lines": self.key_lines(), "ratios": self.ratios(), "sources_uses": self.sources_uses(),
                "checks": self.checks(), "flag_text": FLAG_TEXT, "status_text": STATUS_TEXT,
                "assumptions": self.assumptions}

    # ---------------------------------------------------------------- assumption impact
    def assumption_impact(self, key: str, options: list[str]) -> list[dict]:
        """For each option of an assumption, recompute the dependent ratios for the latest year."""
        if not self.years:
            return []
        y = self.years[-1]
        dependents = [r for r in RATIOS if key in r.assumptions]
        res = []
        for opt in options:
            a = dict(self.assumptions)
            a[key] = opt
            vals = []
            for r in dependents:
                v, _ = self.ratio_value(r.key, y, a)
                vals.append({"ratio": r.key, "name": r.name_en, "value": f(v) if isinstance(v, Decimal) else v,
                             "display": fmt(v, r.unit, self.ccy)})
            res.append({"option": opt, "year": y, "ratios": vals})
        return res

    def dependents_of_category(self, category: str) -> list[str]:
        """Ratios that read any aggregate fed by this category (used to show recalculation impact)."""
        from .aggregate import CA_CATS, CL_CATS, EQ_CATS, NCA_PLUS, NCL_CATS, SUM_DEFS
        aggs = {k for k, (_, cats) in SUM_DEFS.items() if category in cats}
        if category in CA_CATS:
            aggs |= {"ca", "ta"}
        if category in NCA_PLUS or category == "bs.nca.acc_depreciation":
            aggs |= {"fa", "ta"}
        if category in CL_CATS:
            aggs |= {"cl", "tl"}
        if category in NCL_CATS:
            aggs |= {"ncl", "tl"}
        if category in EQ_CATS:
            aggs |= {"equity", "common_equity"}
        if category.startswith("is."):
            aggs |= {"gp", "op_income", "ebit", "ebt", "np", "opex"}
        if category in ("bs.cl.notes_payable", "bs.cl.st_debt", "bs.ncl.lt_loans", "bs.ncl.bonds"):
            aggs.add("ibd")
        return [r.key for r in RATIOS if aggs & set(r.inputs)]
