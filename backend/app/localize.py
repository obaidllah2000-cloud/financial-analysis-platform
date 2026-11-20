"""Applies the selected language to API payloads. Numbers, statuses and approvals are never changed."""
from __future__ import annotations

from . import taxonomy
from .interpret import RECOMMEND, UNIT_SENTENCE, _group, formula_text
from .server_i18n import EXACT, tr, tr_obs

LABELS_AR = {
    "cash": "النقدية وما في حكمها", "st_inv": "استثمارات قصيرة الأجل", "ar": "المدينون (ذمم + أوراق قبض)", "inventory": "المخزون",
    "prepaid": "مصروفات مدفوعة مقدماً", "other_ca": "أصول متداولة أخرى", "land": "الأراضي", "ppe_gross": "الأصول الثابتة بالتكلفة",
    "acc_dep": "مجمع الإهلاك", "ppe_net_reported": "الأصول الثابتة بالصافي", "intangibles": "أصول غير ملموسة", "lt_inv": "استثمارات طويلة الأجل",
    "other_nca": "أصول غير متداولة أخرى", "ap": "الدائنون / الموردون", "notes_payable": "أوراق الدفع", "accrued": "مصروفات مستحقة",
    "st_debt": "ديون قصيرة الأجل", "adv_rev": "إيرادات مقدمة", "tax_payable": "ضرائب مستحقة", "other_cl": "خصوم متداولة أخرى",
    "lt_loans": "قروض طويلة الأجل", "bonds": "سندات طويلة الأجل", "other_ncl": "خصوم طويلة الأجل أخرى", "pref": "الأسهم الممتازة",
    "common": "رأس المال المدفوع / الأسهم العادية", "reserves": "الاحتياطيات", "retained": "الأرباح المحتجزة", "other_eq": "حقوق ملكية أخرى",
    "sales": "المبيعات", "cogs": "تكلفة المبيعات", "selling": "مصروفات بيعية", "ga": "مصروفات عمومية وإدارية", "depreciation": "الإهلاك",
    "other_opex": "مصروفات تشغيل أخرى", "other_income": "إيرادات أخرى", "other_expense": "مصروفات أخرى / خسائر رأسمالية",
    "finance_income": "إيرادات تمويلية", "interest": "مصروف الفوائد", "tax": "ضريبة الدخل", "pref_div": "توزيعات الأسهم الممتازة",
    "common_div": "توزيعات الأسهم العادية", "capex": "الإنفاق الرأسمالي", "dividends_paid": "التوزيعات المدفوعة",
    "ca": "إجمالي الأصول المتداولة", "fa": "الأصول الثابتة (غير المتداولة)", "ta": "إجمالي الأصول", "cl": "الخصوم المتداولة",
    "ncl": "الخصوم طويلة الأجل", "tl": "إجمالي الديون (الخصوم)", "equity": "حقوق الملكية النقدية", "common_equity": "حقوق المساهمين العاديين",
    "tle": "إجمالي الخصوم وحقوق الملكية", "ibd": "الديون ذات الفوائد", "gp": "مجمل الربح", "opex": "إجمالي المصروفات التشغيلية",
    "op_income": "الدخل التشغيلي", "ebit": "الربح قبل الفوائد والضرائب (EBIT)", "ebt": "الربح قبل الضرائب (EBT)", "np": "صافي الربح",
    "ndp": "صافي الربح القابل للتوزيع", "re_add": "الأرباح المحتجزة للعام", "ocf": "التدفق النقدي التشغيلي", "icf": "التدفق النقدي الاستثماري",
    "fincf": "التدفق النقدي التمويلي", "net_change_cash": "صافي التغير في النقدية", "opening_cash": "نقدية أول المدة",
    "closing_cash": "نقدية آخر المدة", "fcf": "التدفق النقدي الحر", "credit_sales": "المبيعات الآجلة", "cash_sales": "المبيعات النقدية",
    "purchases": "المشتريات الآجلة",
}
AREA_AR = {"Liquidity": "السيولة", "Profitability": "الربحية", "Efficiency": "الكفاءة", "Solvency": "الملاءة المالية",
           "Cash Flow": "التدفقات النقدية", "Financial Structure": "الهيكل المالي"}


def label(key: str, en: str, lang: str) -> str:
    return LABELS_AR.get(key, en) if lang == "ar" else en


SOURCE_AR = [("Lecture 1 — Financial Management", "المحاضرة 1 — الإدارة المالية"), ("Lecture 3 — Financial Ratios", "المحاضرة 3 — النسب المالية"),
             ("Lecture 8 — Break-even & Operating Leverage", "المحاضرة 8 — التعادل والرافعة التشغيلية"), ("Lecture", "المحاضرة"),
             ("slides", "الشرائح"), ("slide", "الشريحة"), ("solutions", "الحلول"), ("solution", "الحل"),
             ("Final exam model B", "الامتحان النهائي نموذج B"), ("not covered in the lectures", "غير مشروح في المحاضرات"),
             ("Professional", "مهني"), ("extends the course's 'liquidity of inventory'", "امتداد لسيولة المخزون في المقرر"),
             ("detailed TATO", "تفصيل TATO"), ("10% on R/E", "10% على الأرباح المحتجزة"), ("complement of the debt ratio", "مكمل نسبة المديونية"),
             ("DuPont 3-step", "ديبونت الثلاثي"), ("capital = equity + LTL", "رأس المال = حقوق الملكية + الخصوم طويلة الأجل"),
             ("OI definition", "تعريف الدخل التشغيلي"), ("quantifies the", "يقيس"), ("concept", "مفهوم"), ("extends", "يمتد"),
             (" & ", " و "), ("Q1", "س1"), ("Q2", "س2"), ("Q3", "س3"), ("Q4", "س4"), ("Q5", "س5")]


def source_text(s: str, lang: str) -> str:
    if lang != "ar" or not s:
        return s
    for en, ar in SOURCE_AR:
        s = s.replace(en, ar)
    return s


def _labels_ar(s: str) -> str:
    """Replace English aggregate labels and assumption keys inside an already translated reason."""
    from .assumptions import BY_KEY as AK
    from .engine.aggregate import LABELS
    for k, en in sorted(LABELS.items(), key=lambda kv: -len(kv[1])):
        if en in s and k in LABELS_AR:
            s = s.replace(en, LABELS_AR[k])
    for k, d in AK.items():
        s = s.replace(k, d.name_ar)
    return s


def _units_ar(d):
    return d.replace(" days", " يوماً") if isinstance(d, str) else d


def ratios(rs: list[dict], lang: str) -> list[dict]:
    if lang != "ar":
        return rs
    out = []
    for r in rs:
        r = dict(r)
        latest = next((c for c in reversed(r["cells"]) if c["value"] is not None), None)
        us = UNIT_SENTENCE.get(r["key"])
        if us and latest:
            r["interpretation"] = us[1].format(v=_units_ar(latest["display"]))
        r["formula"] = formula_text(r["formula"], lang)
        r["source"] = source_text(r["source"], lang)
        r["comment"] = tr(r["comment"], lang).replace(" days", " يوماً")
        r["risk_basis"] = tr(r["risk_basis"], lang)
        if r.get("action"):
            r["action"] = RECOMMEND[_group(r)][3]
        r["cells"] = [dict(c, display=_units_ar(c["display"]), reasons=[_labels_ar(tr(x, lang)) for x in c["reasons"]],
                           notes=[_labels_ar(tr(x, lang)) for x in c["notes"]]) for c in r["cells"]]
        if r.get("benchmark") and r["benchmark"].get("source"):
            r["benchmark"] = dict(r["benchmark"], source=source_text(r["benchmark"]["source"], lang))
        out.append(r)
    return out


def key_lines(kl: list[dict], lang: str) -> list[dict]:
    if lang != "ar":
        return kl
    return [dict(k, label=label(k["key"], k["label"], lang), stats=dict(k["stats"], trend=tr(k["stats"].get("trend"), lang))) for k in kl]


def checks(cs: list[dict], lang: str) -> list[dict]:
    return cs if lang != "ar" else [dict(c, message=tr(c["message"], lang)) for c in cs]


def observations(obs: list[dict], lang: str) -> list[dict]:
    return obs if lang != "ar" else [tr_obs(o, lang) for o in obs]


def statement_rows(rows: list[dict], lang: str) -> list[dict]:
    if lang != "ar":
        return rows
    return [dict(r, category_label=r.get("category_label_ar", r["category_label"]), normalization_notes=[tr(n, lang) for n in r["normalization_notes"]],
                 observations=[tr(o, lang) for o in r.get("observations", [])], stats=dict(r["stats"], trend=tr(r["stats"].get("trend"), lang)))
            for r in rows]


def sources_uses(sus: list[dict], lang: str) -> list[dict]:
    if lang != "ar":
        return sus
    from .interpret import su_desc_ar
    return [dict(s, rows=[dict(r, description=su_desc_ar(r)) for r in s["rows"]]) for s in sus]


def classification(c: dict, lang: str) -> dict:
    if lang != "ar":
        return c
    c = dict(c)
    for k in ("reason", "question"):
        if c.get(k):
            c[k] = tr(c[k], lang)
    c["options"] = [dict(o, label=_opt_label(o, lang)) for o in (c.get("options") or [])]
    c["suggested_group"] = tr(c.get("suggested_group"), lang)
    return c


def _opt_label(o: dict, lang: str) -> str:
    t = tr(o["label"], lang)
    if t == o["label"]:
        cat = taxonomy.BY_KEY.get(o.get("category"))
        if cat:
            return cat.label_ar
    return t


def assumption(a: dict, lang: str) -> dict:
    if lang != "ar":
        return a
    a = dict(a)
    a["name"] = a.get("name_ar") or a["name"]
    a["reason"] = tr(a["reason"], lang)
    a["supporting_data"] = tr(a["supporting_data"], lang)
    a["options"] = [dict(o, label=tr(o["label"], lang), impact=tr(o["impact"], lang)) for o in a["options"]]
    from .engine.ratios import BY_KEY as RB
    a["impact"] = [dict(i, ratios=[dict(x, name=RB[x["ratio"]].name_ar if x["ratio"] in RB else x["name"]) for x in i["ratios"]])
                   for i in a.get("impact", [])]
    return a


def issue(i: dict, lang: str) -> dict:
    return i if lang != "ar" else dict(i, message=tr(i["message"], lang))


def evaluation(ev: dict, lang: str) -> dict:
    if lang != "ar":
        return ev
    ev = dict(ev)
    ev["areas"] = [dict(a, area=AREA_AR.get(a["area"], a["area"]), rating=EXACT.get(a["rating"], a["rating"]), summary=tr(a["summary"], lang))
                   for a in ev["areas"]]
    for k in ("historical_performance", "strengths", "weaknesses", "risks", "recommendations"):
        ev[k] = [_tr_compound(x, lang) for x in ev.get(k, [])]
    return ev


def _tr_compound(s: str, lang: str) -> str:
    """Lines like 'Area: text' or 'Name — comment (basis)'."""
    for sep in (" — ", ": "):
        if sep in s:
            head, tail = s.split(sep, 1)
            return f"{tr(head, lang)}{sep}{tr(tail, lang)}"
    return tr(s, lang)
