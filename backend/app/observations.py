"""AI Financial Analyst — deterministic three-level review of VERIFIED calculation outputs.

Level 1  individual accounts      Level 2  relationships between accounts      Level 3  overall picture
Every observation states: finding, supporting data, comparison period, reasoning, possible explanation
(always worded as a hypothesis), financial impact, confidence, required action and its type:
  math_error | accounting_inconsistency | unusual_trend | potential_risk | hypothesis
No arithmetic is delegated to a language model: all numbers come from the calculation engine.
"""
from __future__ import annotations

from decimal import Decimal

from . import taxonomy
from .engine.aggregate import LABELS, normalize
from .engine.analysis import Analysis

TYPE_LABEL = {"math_error": "Confirmed mathematical error", "accounting_inconsistency": "Accounting inconsistency",
              "unusual_trend": "Unusual financial trend", "potential_risk": "Potential risk",
              "hypothesis": "Hypothesis requiring investigation"}


def _g(cur, prev):
    if cur is None or prev in (None, 0):
        return None
    return float((cur - prev) / abs(prev))


def _pct(x):
    return "n/a" if x is None else f"{x * 100:+.1f}%"


def _n(x):
    return "n/a" if x is None else f"{float(x):,.0f}"


def obs(key, level, typ, area, title, finding, data, period, reasoning, explanation, impact, confidence, action,
        question=None, related=None):
    return {"key": key, "level": level, "type": typ, "type_label": TYPE_LABEL[typ], "area": area, "title": title,
            "finding": finding, "supporting_data": data, "comparison_period": period, "reasoning": reasoning,
            "possible_explanation": explanation, "financial_impact": impact, "confidence": confidence,
            "required_action": action, "question": question, "related": related or []}


def review(an: Analysis, pending_questions: list[dict] | None = None) -> list[dict]:
    out: list[dict] = []
    ys = an.years
    if not ys:
        return out
    last = ys[-1]
    prev = ys[-2] if len(ys) > 1 else None
    B = an.books
    v = lambda k, y: B[y].v(k) if y in B else None  # noqa: E731

    # ------------------------------------------------------------ Level 1 — mathematical checks
    for c in an.checks():
        if c["code"] in ("BS_NOT_BALANCED", "TOTAL_MISMATCH", "CF_SECTIONS", "CF_CASH_ROLL"):
            typ = "math_error" if c["code"] in ("BS_NOT_BALANCED", "CF_SECTIONS", "CF_CASH_ROLL") else "accounting_inconsistency"
            out.append(obs(f"chk-{c['code']}-{c['year']}-{c.get('aggregate')}", 1, typ, "data quality",
                           "Totals do not reconcile" if c["code"] != "BS_NOT_BALANCED" else "Balance sheet does not balance",
                           c["message"], {k: c.get(k) for k in ("computed", "reported") if c.get(k) is not None}, str(c["year"]),
                           "Computed from the classified accounts and compared with the reported subtotal / accounting equation.",
                           "Possibly a misclassified account, a pending classification that changes the group (e.g. an investment "
                           "classified as non-current), a missing account, or a typing error in the Excel file.",
                           "Ratios using the affected totals may be wrong until resolved.", "High",
                           "Review the classification of accounts in the affected group, or correct the Excel file and re-upload.",
                           related=[c.get("aggregate")]))

    # ------------------------------------------------------------ Level 1 — individual accounts
    base_ta = v("ta", last) or Decimal(1)
    base_sales = v("sales", last) or Decimal(1)
    for a in an.accounts:
        cat = taxonomy.get(a.category)
        if cat.subtotal or a.status == "rejected" or a.statement == "CF":
            continue
        nv = {y: normalize(a.values.get(y), a.category)[0] for y in ys}
        # negative balances
        for y in ys:
            x = nv[y]
            if x is not None and x < 0 and cat.element in ("Asset", "Revenue") and not cat.contra:
                out.append(obs(f"neg-{a.id}-{y}", 1, "accounting_inconsistency", "data quality", f"Negative balance: {a.name}",
                               f"{a.name} shows a negative balance of {_n(x)} in {y}.", {"value": float(x)}, str(y),
                               f"A {cat.element.lower()} ({cat.label_en}) is normally positive.",
                               "Possibly a contra account entered in the wrong line, a sign error, or an overdraft netted into cash.",
                               "Understates the related total and every ratio that uses it.", "High",
                               "Confirm the sign in the source statements; reclassify if it is a liability (e.g. bank overdraft).",
                               related=[a.name]))
        if prev is None:
            continue
        cur, pv = nv.get(last), nv.get(prev)
        g = _g(cur, pv)
        base = base_ta if a.statement == "BS" else base_sales
        if g is not None and abs(g) >= 0.25 and abs(cur - pv) >= abs(base) * Decimal("0.02"):
            out.append(obs(f"mv-{a.id}", 1, "unusual_trend", "accounts", f"{'Large increase' if g > 0 else 'Large decrease'}: {a.name}",
                           f"{a.name} {'increased' if g > 0 else 'decreased'} by {_pct(g)} ({_n(pv)} → {_n(cur)}).",
                           {str(prev): float(pv), str(last): float(cur), "change_pct": g}, f"{prev}–{last}",
                           "Movement exceeds 25% and is material (≥ 2% of total assets / sales).",
                           "Requires explanation from management (e.g. new financing, expansion, change in credit policy, write-offs).",
                           f"Changes {LABELS.get('ta' if a.statement == 'BS' else 'sales')} composition and dependent ratios.",
                           "Medium", "Obtain the reason for the movement and confirm it is correctly recorded.", related=[a.name]))

    # classification questions surfaced by the classifier
    for q in pending_questions or []:
        out.append(obs(f"cls-{q['account_id']}", 1, "hypothesis", "classification", f"Classification needs confirmation: {q['account']}",
                       q["question"], {"suggested": q["suggested"], "confidence": q["confidence"]}, "All years",
                       q["reason"], "The account name alone does not determine its nature.",
                       "Changes liquidity / solvency ratios depending on the answer.", "Medium",
                       "Answer the question in the Classification Review.", q["question"], [q["account"]]))

    if prev is None:
        return out

    # ------------------------------------------------------------ Level 2 — relationships
    def rel(key, area, title, a_key, b_key, threshold, finding_tpl, reasoning, explanation, impact, action, question=None, typ="unusual_trend"):
        ga, gb = _g(v(a_key, last), v(a_key, prev)), _g(v(b_key, last), v(b_key, prev))
        if ga is None or gb is None or ga - gb < threshold:
            return
        out.append(obs(key, 2, typ, area, title, finding_tpl.format(ga=_pct(ga), gb=_pct(gb)),
                       {LABELS.get(a_key, a_key): {str(prev): float(v(a_key, prev)), str(last): float(v(a_key, last))},
                        LABELS.get(b_key, b_key): {str(prev): float(v(b_key, prev)), str(last): float(v(b_key, last))}},
                       f"{prev}–{last}", reasoning, explanation, impact, "Medium", action, question, [a_key, b_key]))

    rel("rel-cl-ca", "liquidity", "Current liabilities growing faster than current assets", "cl", "ca", 0.05,
        "Current liabilities increased by {ga} while current assets increased by only {gb}.",
        "When short-term obligations outgrow short-term resources, the current ratio and working capital deteriorate.",
        "Hypotheses: short-term borrowing used to finance long-term assets or losses; slower supplier payments.",
        "Weaker liquidity; higher refinancing risk.", "Investigate the main causes of the increase in current liabilities.",
        "Would you like to investigate the main causes of the increase in current liabilities?", "potential_risk")
    rel("rel-ar-sales", "efficiency", "Receivables growing faster than sales", "ar", "sales", 0.10,
        "Receivables grew {ga} versus sales growth of {gb}.",
        "Receivables should broadly track credit sales; faster growth lengthens the collection period.",
        "Hypotheses: looser credit terms, slow-paying or doubtful customers, year-end sales concentration.",
        "More cash tied up in receivables; possible impairment risk.", "Review the receivables ageing and credit policy.",
        "Do you want to review the receivables ageing for the latest year?")
    rel("rel-inv-cogs", "efficiency", "Inventory growing faster than cost of sales", "inventory", "cogs", 0.10,
        "Inventory grew {ga} while cost of goods sold grew {gb}.",
        "Inventory normally moves with COGS; a gap means slower inventory turnover.",
        "Hypotheses: slow-moving or obsolete stock, deliberate stock-building, lower sales than planned.",
        "Cash tied up in stock; possible write-down risk.", "Review inventory composition and ageing.",
        "Would you like to review inventory composition?")
    rel("rel-ta-eq", "solvency", "Assets growing faster than equity", "ta", "equity", 0.10,
        "Total assets grew {ga} versus equity growth of {gb}.",
        "Growth not financed by equity is financed by debt, which raises financial leverage.",
        "Hypothesis: expansion financed mainly by borrowing.", "Higher debt ratio and financial risk.",
        "Confirm the financing plan and debt capacity.", typ="potential_risk")

    # inventory turnover decline
    it_l, it_p = an.ratio_value("inventory_turnover", last)[0], an.ratio_value("inventory_turnover", prev)[0]
    if it_l is not None and it_p not in (None, 0) and (it_l - it_p) / it_p <= Decimal("-0.10"):
        out.append(obs("rel-invto", 2, "unusual_trend", "efficiency", "Inventory turnover declined",
                       f"Inventory turnover declined from {float(it_p):.2f} to {float(it_l):.2f}. This may indicate slower inventory movement.",
                       {str(prev): float(it_p), str(last): float(it_l)}, f"{prev}–{last}",
                       "COGS / inventory fell by more than 10%.", "Hypotheses: overstocking, obsolete items, weaker demand.",
                       "Longer selling period (ASP) and more financing needed for operations.", "High",
                       "Review inventory composition.", "Would you like to review inventory composition?", ["inventory", "cogs"]))

    # debt vs interest
    ibd_l, ibd_p, i_l, i_p = v("ibd", last), v("ibd", prev), v("interest", last), v("interest", prev)
    if ibd_l and i_l is not None and ibd_p and i_p is not None:
        avg = (ibd_l + ibd_p) / 2
        rate = float(i_l / avg) if avg else None
        rate_p = float(i_p / ibd_p) if ibd_p else None
        if rate is not None and (rate > 0.30 or rate < 0.01):
            out.append(obs("rel-int-rate", 2, "accounting_inconsistency", "solvency", "Implied interest rate looks unusual",
                           f"Interest of {_n(i_l)} on average interest-bearing debt of {_n(avg)} implies a rate of {rate * 100:.1f}%.",
                           {"interest": float(i_l), "avg_interest_bearing_debt": float(avg), "implied_rate": rate}, str(last),
                           "Interest should be consistent with the level of borrowing.",
                           "Hypotheses: capitalised interest, debt repaid / drawn during the year, misclassified debt, interest in COGS.",
                           "Interest coverage and ROBF may be misstated.", "Medium", "Reconcile interest expense with the loan schedule.",
                           related=["interest", "ibd"]))
        elif rate is not None and rate_p is not None and rate - rate_p > 0.03:
            out.append(obs("rel-int-up", 2, "potential_risk", "solvency", "Cost of debt increased",
                           f"Implied interest rate rose from {rate_p * 100:.1f}% to {rate * 100:.1f}%.",
                           {"rate_prev": rate_p, "rate_last": rate}, f"{prev}–{last}", "Interest / average interest-bearing debt.",
                           "Hypotheses: higher market rates or more expensive short-term borrowing.", "Lower ROBF and interest coverage.",
                           "Medium", "Review refinancing options.", related=["interest", "ibd"]))
    elif (ibd_l or 0) > 0 and (i_l is None or i_l == 0):
        out.append(obs("rel-no-int", 2, "accounting_inconsistency", "solvency", "Debt without interest expense",
                       f"Interest-bearing debt of {_n(ibd_l)} is reported but no interest expense was found for {last}.",
                       {"interest_bearing_debt": float(ibd_l)}, str(last), "Borrowings normally carry interest.",
                       "Hypotheses: interest capitalised, included in another line, or interest-free related-party loans.",
                       "Interest coverage and ROBF cannot be computed reliably.", "Medium", "Confirm where interest is recorded.",
                       related=["ibd", "interest"]))

    # fixed assets vs depreciation
    dep_l, dep_p, g_l, g_p = v("depreciation", last), v("depreciation", prev), v("ppe_gross", last), v("ppe_gross", prev)
    if None not in (dep_l, dep_p, g_l, g_p) and g_l and g_p:
        r_l, r_p = float(dep_l / g_l), float(dep_p / g_p)
        if abs(r_l - r_p) > 0.02:
            out.append(obs("rel-dep", 2, "hypothesis", "accounts", "Depreciation rate changed",
                           f"Depreciation / gross fixed assets moved from {r_p * 100:.1f}% to {r_l * 100:.1f}%.",
                           {"rate_prev": r_p, "rate_last": r_l}, f"{prev}–{last}", "Depreciation should follow the asset base.",
                           "Hypotheses: change in useful lives, assets acquired late in the year, disposals.", "Affects EBIT and ROI.",
                           "Low", "Ask for the fixed-asset register movement.", related=["depreciation", "ppe_gross"]))

    # ------------------------------------------------------------ Level 3 — overall
    np_l, np_p, ocf_l, ocf_p = v("np", last), v("np", prev), v("ocf", last), v("ocf", prev)
    if None not in (np_l, np_p, ocf_l, ocf_p) and np_l > np_p and ocf_l < ocf_p:
        wc_drivers = []
        for k in ("ar", "inventory"):
            if v(k, last) is not None and v(k, prev) is not None and v(k, last) > v(k, prev):
                wc_drivers.append(f"{LABELS[k]} +{_n(v(k, last) - v(k, prev))}")
        out.append(obs("ovr-np-ocf", 3, "potential_risk", "cash flow", "Profits rising while operating cash flow falls",
                       f"Net profit increased from {_n(np_p)} to {_n(np_l)} while operating cash flow declined from {_n(ocf_p)} to {_n(ocf_l)}.",
                       {"np": {str(prev): float(np_p), str(last): float(np_l)}, "ocf": {str(prev): float(ocf_p), str(last): float(ocf_l)},
                        "working_capital_build_up": wc_drivers}, f"{prev}–{last}",
                       "Profit quality is weak when accounting profit is not converted into cash. " +
                       ("Working capital increased: " + ", ".join(wc_drivers) + "." if wc_drivers else ""),
                       "Hypotheses (unverified): growth in receivables/inventory absorbing cash, aggressive revenue recognition, "
                       "or timing of supplier payments.", "Liquidity pressure despite reported profitability; may need external financing.",
                       "High", "Investigate working-capital movements and revenue recognition before relying on profit growth.",
                       "Would you like to investigate why profit is not converting into cash?", ["np", "ocf"]))
    roi_l, robf_l = an.ratio_value("roi", last)[0], an.ratio_value("robf", last)[0]
    if robf_l is not None and robf_l < 0:
        out.append(obs("ovr-robf", 3, "potential_risk", "profitability", "Borrowing reduces return on equity (negative ROBF)",
                       f"ROBF is {float(robf_l) * 100:.2f}% in {last}: the cost of borrowed funds exceeds the ROI of {float(roi_l) * 100:.2f}%.",
                       {"roi": float(roi_l), "robf": float(robf_l)}, str(last), "ROBF = (ROI − I/BF) × BF/OE (Lecture 3). It is negative when I/BF > ROI.",
                       "Debt is not earning its cost.", "Each additional unit of debt lowers ROE.", "High",
                       "Reduce expensive debt or improve asset returns before borrowing further.", related=["roi", "robf"]))
    cr = [an.ratio_value("current_ratio", y)[0] for y in ys]
    nim = [an.ratio_value("nim", y)[0] for y in ys]
    if len(ys) >= 3 and None not in cr[-3:] and None not in nim[-3:] and cr[-1] < cr[-3] and nim[-1] >= nim[-3]:
        out.append(obs("ovr-liq-prof", 3, "potential_risk", "liquidity", "Liquidity is weakening while margins hold up",
                       f"Current ratio fell from {float(cr[-3]):.2f} to {float(cr[-1]):.2f} over {ys[-3]}–{last}, while net margin "
                       f"moved from {float(nim[-3]) * 100:.1f}% to {float(nim[-1]) * 100:.1f}%.",
                       {"current_ratio": [float(x) for x in cr[-3:]], "nim": [float(x) for x in nim[-3:]]}, f"{ys[-3]}–{last}",
                       "Profitability and liquidity must be read together: growth financed by short-term liabilities can hide a liquidity squeeze.",
                       "Hypothesis: expansion of working capital financed with short-term debt.", "Rising short-term refinancing risk.",
                       "Medium", "Match the maturity of financing with the assets being financed (golden rule).", related=["current_ratio", "nim"]))
    su = an.sources_uses()
    if su:
        s = su[-1]
        if s.get("golden_rule_deviation") is not None and s["golden_rule_deviation"] > 0.10:
            out.append(obs("ovr-golden", 3, "potential_risk", "financial structure", "Deviation from the golden rule of financing",
                           f"Short-term sources are {s['short_term_sources_pct'] * 100:.1f}% of sources while short-term uses are "
                           f"{s['short_term_uses_pct'] * 100:.1f}% of uses ({s['from_year']}–{s['to_year']}): deviation "
                           f"{s['golden_rule_deviation'] * 100:.1f}%.",
                           {k: s[k] for k in ("short_term_sources_pct", "short_term_uses_pct", "long_term_sources_pct", "long_term_uses_pct")},
                           f"{s['from_year']}–{s['to_year']}", "Golden rule (Lecture 1): short-term uses ↔ short-term sources; long-term ↔ long-term.",
                           "Short-term funds may be financing long-term investments (or vice versa).",
                           "Maturity mismatch raises liquidity risk.", "Medium",
                           "Refinance long-term investments with long-term funds.", related=["sources_uses"]))
    return out


AREAS = {
    "Liquidity": ["current_ratio", "quick_ratio", "cash_ratio", "working_capital", "acp", "liquidity_of_inventory"],
    "Profitability": ["gpm", "oim", "nim", "roi", "roe", "robf", "eva"],
    "Efficiency": ["tato", "fato", "inventory_turnover", "ar_turnover", "asp", "acp"],
    "Solvency": ["debt_ratio", "debt_equity", "interest_coverage", "capital_structure_ratio"],
    "Cash Flow": ["ocf", "fcf", "ocf_ratio", "ocf_to_np"],
    "Financial Structure": ["capital_structure_ratio", "debt_ratio", "financial_leverage", "lt_debt_ratio"],
}


def evaluation(an: Analysis, ratios: list[dict], observations: list[dict]) -> dict:
    rmap = {r["key"]: r for r in ratios}
    areas = []
    strengths, weaknesses, risks, recs = [], [], [], []
    for area, keys in AREAS.items():
        items = [rmap[k] for k in keys if k in rmap and any(c["value"] is not None for c in rmap[k]["cells"])]
        if not items:
            areas.append({"area": area, "rating": "Insufficient data", "summary": "Not enough data for this area.", "ratios": []})
            continue
        highs = [r for r in items if r["risk"] == "High"]
        meds = [r for r in items if r["risk"] == "Medium"]
        lows = [r for r in items if r["risk"] == "Low"]
        rating = "Weak" if len(highs) >= 2 or (highs and not lows) else "Needs attention" if highs or len(meds) >= 2 else "Satisfactory" if lows or meds else "Neutral"
        prov = any(c["status"] in ("provisional", "needs_info", "invalid") for r in items for c in r["cells"][-1:])
        lines = []
        for r in items:
            last = next((c for c in reversed(r["cells"]) if c["value"] is not None), None)
            if last:
                lines.append(f"{r['name_en']}: {last['display']} ({r['risk']} risk)")
        areas.append({"area": area, "rating": rating, "provisional": prov, "summary": "; ".join(lines[:5]),
                      "ratios": [r["key"] for r in items]})
        for r in lows:
            if r["critical"]:
                strengths.append(f"{r['name_en']} — {r['comment']}")
        for r in highs + meds:
            weaknesses.append(f"{r['name_en']} — {r['comment']} ({r['risk_basis']})")
            if r.get("action"):
                recs.append(f"{area}: {r['action']}")
    for o in observations:
        if o["type"] == "potential_risk":
            risks.append(f"{o['title']}: {o['finding']}")
            recs.append(f"{o['area'].title()}: {o['required_action']}")
    hist = []
    kl = {k["key"]: k for k in an.key_lines()}
    for k in ("sales", "np", "ta", "equity", "ocf"):
        if k in kl and kl[k]["stats"].get("cagr") is not None:
            hist.append(f"{kl[k]['label']}: CAGR {kl[k]['stats']['cagr'] * 100:.1f}% ({kl[k]['stats']['trend']})")
        elif k in kl:
            hist.append(f"{kl[k]['label']}: {kl[k]['stats'].get('trend')} (CAGR not meaningful)")
    seen = set()
    recs = [r for r in recs if not (r in seen or seen.add(r))]
    return {"areas": areas, "historical_performance": hist, "strengths": strengths[:10], "weaknesses": weaknesses[:12],
            "risks": risks[:10], "recommendations": recs[:12]}
