"""Excel and PDF report exports in English or Arabic. Both render the SAME report dict the dashboard uses,
so a report always reflects the current approved data, classifications and assumptions."""
from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

MODULES = ["profile", "statements", "horizontal", "vertical", "ratios", "interpretation_academic", "comparison", "sources_uses",
           "interpretation", "risks", "recommendations", "assumptions"]
STATUS_FILL = {"verified": "D9F2E3", "approved_assumption": "DDEBFF", "provisional": "FFF2CC", "needs_info": "EEEEEE", "invalid": "F8D7DA"}
HEAD = PatternFill("solid", fgColor="1F3A5F")
FONT_DIR = Path(__file__).resolve().parent / "fonts"

L = {  # report vocabulary (en, ar)
    "title": ("Financial Analysis Report", "تقرير التحليل المالي"),
    "profile": ("Company profile", "بيانات الشركة"), "name": ("Company", "الشركة"), "industry": ("Industry", "القطاع"),
    "country": ("Country", "الدولة"), "currency": ("Currency", "العملة"), "fy_end": ("Financial year end", "نهاية السنة المالية"),
    "reporting_type": ("Reporting type", "نوع التقرير"), "basis": ("Statement basis", "أساس القوائم"), "standards": ("Standards", "المعايير"),
    "methodology": ("Methodology", "المنهجية"), "years": ("Financial period", "الفترة المالية"), "version": ("Data version", "نسخة البيانات"),
    "generated": ("Generated", "تاريخ الإصدار"), "approval": ("Approval status", "حالة الاعتماد"), "legend": ("Result status legend", "دلالات حالة النتائج"),
    "BS": ("Balance Sheet", "الميزانية"), "IS": ("Income Statement", "قائمة الدخل"), "CF": ("Cash Flow", "التدفقات النقدية"),
    "account": ("Original account", "الحساب الأصلي"), "classif": ("Approved classification", "التصنيف المعتمد"), "status": ("Status", "الحالة"),
    "orig": ("original", "أصلي"), "norm": ("normalized", "معدّل"),
    "horizontal": ("Horizontal & trends", "التحليل الأفقي والاتجاهات"), "item": ("Item", "البند"), "trend": ("Trend", "الاتجاه"),
    "average": ("Average", "المتوسط"), "highest": ("Highest", "الأعلى"), "lowest": ("Lowest", "الأدنى"), "cum": ("Cumulative %", "التغير التراكمي %"),
    "cagr": ("CAGR %", "معدل النمو المركب %"), "note": ("Note", "ملاحظة"), "chg": ("Δ%", "التغير %"),
    "vertical": ("Vertical (common size)", "التحليل الرأسي"), "base": ("Base", "الأساس"), "of_ta": ("Total assets", "إجمالي الأصول"), "of_sales": ("Sales", "المبيعات"),
    "ratios": ("Financial ratios", "النسب المالية"), "category": ("Category", "الفئة"), "ratio": ("Ratio", "النسبة"), "formula": ("Formula", "المعادلة"),
    "bench": ("Benchmark", "المعيار"), "risk": ("Risk", "المخاطر"), "risk_basis": ("Risk basis", "أساس المخاطر"), "interp": ("Interpretation", "التفسير"),
    "comment": ("Assessment", "التقييم"), "action": ("Suggested action", "الإجراء المقترح"), "source": ("Source", "المصدر"),
    "acad": ("Academic interpretation", "التفسير الأكاديمي"), "year": ("Year", "السنة"), "basis_col": ("Basis", "الأساس"), "verdict": ("Verdict", "الحكم"),
    "step": ("Step", "الخطوة"), "text": ("Text", "النص"), "dupont": ("DuPont analysis", "تحليل ديبونت"),
    "su": ("Sources & uses of money", "مصادر واستخدامات الأموال"), "opening": ("Opening", "أول المدة"), "closing": ("Closing", "آخر المدة"),
    "change": ("Change", "التغير"), "su_type": ("Source / Use", "مصدر / استخدام"), "term": ("Term", "الأجل"), "internal": ("Internal?", "داخلي؟"),
    "amount": ("Amount", "المبلغ"), "share": ("% of total", "% من الإجمالي"), "desc": ("Description", "الوصف"), "su_analysis": ("Analysis", "التحليل"),
    "evaluation": ("Final financial evaluation", "التقييم المالي النهائي"), "area": ("Area", "المجال"), "rating": ("Rating", "التقييم"),
    "summary": ("Key indicators", "المؤشرات الرئيسية"), "hist": ("Historical performance", "الأداء التاريخي"), "strengths": ("Strengths", "نقاط القوة"),
    "weaknesses": ("Weaknesses", "نقاط الضعف"), "risks": ("Risks", "المخاطر"), "recs": ("Management recommendations", "توصيات للإدارة"),
    "obs": ("AI observations", "ملاحظات المحلل الذكي"), "level": ("Level", "المستوى"), "type": ("Type", "النوع"), "title_c": ("Title", "العنوان"),
    "finding": ("Finding", "الملاحظة"), "period": ("Period", "الفترة"), "reasoning": ("Reasoning", "التعليل"), "hypo": ("Possible explanation (hypothesis)", "التفسير المحتمل (فرضية)"),
    "impact": ("Impact", "الأثر"), "conf": ("Confidence", "الثقة"), "req": ("Required action", "الإجراء المطلوب"),
    "assumptions": ("Assumptions & limitations", "الافتراضات والقيود"), "assumption": ("Assumption", "الافتراض"), "value": ("Value", "القيمة"),
    "reason": ("Reason", "السبب"), "support": ("Supporting data", "البيانات الداعمة"), "decided": ("Decided at", "تاريخ القرار"),
    "limits": ("Limitations", "القيود"), "none": ("None identified.", "لا يوجد."), "no_risk": ("No material risks flagged by the rules.", "لم تُرصد مخاطر جوهرية."),
    "no_rec": ("No specific recommendations.", "لا توجد توصيات محددة."), "multi": ("Multi-year comparison", "مقارنة متعددة السنوات"),
    "common_last": ("Common size (last year)", "النسبة الرأسية (آخر سنة)"), "reconciled": ("Reconciled", "متطابق"),
    "golden": ("Golden-rule deviation", "الانحراف عن القاعدة الذهبية"), "int_src": ("Internal sources", "المصادر الداخلية"),
    "tot_src": ("Total sources", "إجمالي المصادر"), "tot_use": ("Total uses", "إجمالي الاستخدامات"),
    "academic": ("Academic (course)", "أكاديمي (المقرر)"), "professional_m": ("Professional", "مهني"), "professional": ("Professional", "مهني"),
    "favorable": ("Favourable", "إيجابي"), "unfavorable": ("Unfavourable", "سلبي"), "mixed": ("Mixed", "مختلط"), "neutral": ("Neutral", "محايد"), "n/a": ("n/a", "غير متاح"),
    "source_s": ("source", "مصدر"), "use": ("use", "استخدام"), "short": ("short", "قصير"), "long": ("long", "طويل"), "yes": ("yes", "نعم"), "no": ("no", "لا"),
    "verified": ("verified", "مُتحقق"), "approved_assumption": ("approved assumption", "افتراض معتمد"), "provisional": ("provisional", "مبدئي"),
    "needs_info": ("needs info", "يحتاج معلومات"), "invalid": ("invalid", "غير صالح"), "approved": ("approved", "معتمد"), "modified": ("modified", "معدّل"),
    "pending": ("pending", "معلّق"), "rejected": ("rejected", "مرفوض"), "accepted": ("accepted", "مقبول"), "info_requested": ("info requested", "طلب معلومات"),
    "cat_liquidity": ("Liquidity", "السيولة"), "cat_activity": ("Activity & efficiency", "النشاط والكفاءة"), "cat_profitability": ("Profitability", "الربحية"),
    "cat_dupont": ("DuPont", "ديبونت"), "cat_debt": ("Solvency & structure", "الملاءة والهيكل المالي"), "cat_cashflow": ("Cash flow", "التدفقات النقدية"),
    "cat_market": ("Modern techniques", "الأساليب الحديثة"), "cat_breakeven": ("Break-even", "التعادل"),
    "High": ("High", "مرتفعة"), "Medium": ("Medium", "متوسطة"), "Low": ("Low", "منخفضة"),
}


def t(key, lang):
    v = L.get(key)
    return (v[1] if lang == "ar" else v[0]) if v else key


def _pct(x):
    return None if x is None else round(x * 100, 2)


def _rname(r, lang):
    return r["name_ar"] if lang == "ar" else r["name_en"]


# =============================================================== Excel
def excel(rep: dict, modules: list[str]) -> bytes:
    lang = rep.get("lang", "en")
    rtl = lang == "ar"
    wb = Workbook()
    years = rep["years"]

    def sheet(title, first=False):
        sh = wb.active if first else wb.create_sheet()
        sh.title = title[:31]
        sh.sheet_view.rightToLeft = rtl
        return sh

    def header(sh, cols):
        sh.append(cols)
        for cell in sh[sh.max_row]:
            cell.fill, cell.font = HEAD, Font(bold=True, color="FFFFFF")
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    def wrap(sh, widths):
        for col, w in widths.items():
            sh.column_dimensions[col].width = w
        for row in sh.iter_rows(min_row=2):
            for c in row:
                c.alignment = Alignment(wrap_text=True, vertical="top")

    c = rep["company"]
    ws = sheet(t("profile", lang), first=True)
    ws.append([t("title", lang)])
    ws["A1"].font = Font(bold=True, size=14)
    for k in ("name", "industry", "country", "currency", "fy_end", "reporting_type", "basis", "standards", "methodology"):
        ws.append([t(k, lang), t(c.get(k), lang) if k == "methodology" else c.get(k)])
    ws.append([t("years", lang), f"{years[0]} – {years[-1]}" if years else ""])
    ws.append([t("version", lang), rep["governance"].get("version")])
    ws.append([t("generated", lang), datetime.now().strftime("%Y-%m-%d %H:%M")])
    ws.append([t("approval", lang), rep["approval_status_text"]])
    ws.append([])
    ws.append([t("legend", lang)])
    for k, v in rep["status_text"].items():
        ws.append([t(k, lang), v])
        ws.cell(ws.max_row, 1).fill = PatternFill("solid", fgColor=STATUS_FILL[k])
    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 90

    if "statements" in modules:
        for st in ("BS", "IS", "CF"):
            rows = rep["statements"].get(st, [])
            if not rows:
                continue
            sh = sheet(t(st, lang))
            header(sh, [t("account", lang), t("classif", lang), t("status", lang)] + [f"{y} {t('orig', lang)}" for y in years]
                   + [f"{y} {t('norm', lang)}" for y in years])
            for r in rows:
                sh.append([r["account"], r["category_label"], t(r["status"], lang)] + [r["values"].get(y) for y in years]
                          + [r["normalized"].get(y) for y in years])
            sh.column_dimensions["A"].width = 38
            sh.column_dimensions["B"].width = 40

    if "horizontal" in modules or "comparison" in modules:
        sh = sheet(t("horizontal", lang))
        header(sh, [t("item", lang)] + [str(y) for y in years] + [f"{t('chg', lang)} {y}" for y in years[1:]]
               + [t(k, lang) for k in ("trend", "average", "highest", "lowest", "cum", "cagr", "note")])
        for k in rep["key_lines"]:
            s = k["stats"]
            chg = {c_["year"]: c_ for c_ in s["changes"]}
            note = "; ".join(sorted({rep["flag_text"].get(c_["flag"], "") for c_ in s["changes"] if c_.get("flag")}
                                    | ({rep["flag_text"].get(s.get("cagr_flag"), "")} if s.get("cagr_flag") else set())))
            sh.append([k["label"]] + [k["values"].get(y) for y in years] + [_pct(chg.get(y, {}).get("pct_change")) for y in years[1:]]
                      + [s.get("trend"), s.get("average"), (s.get("highest") or {}).get("value"), (s.get("lowest") or {}).get("value"),
                         _pct(s.get("cumulative_pct")), _pct(s.get("cagr")), note])
        sh.column_dimensions["A"].width = 36

    if "vertical" in modules:
        sh = sheet(t("vertical", lang))
        header(sh, [t("item", lang), t("base", lang)] + [f"{y} %" for y in years])
        for k in rep["key_lines"]:
            if k["statement"] == "CF":
                continue
            sh.append([k["label"], t("of_ta" if k["statement"] == "BS" else "of_sales", lang)] + [_pct(k["common_size"].get(y)) for y in years])
        sh.column_dimensions["A"].width = 36

    if "ratios" in modules:
        sh = sheet(t("ratios", lang))
        header(sh, [t("category", lang), t("ratio", lang), t("methodology", lang), t("formula", lang)] + [str(y) for y in years]
               + [f"{t('status', lang)} {y}" for y in years]
               + [t(k, lang) for k in ("bench", "risk", "risk_basis", "interp", "comment", "action", "source")])
        for r in rep["ratios"]:
            cells = {x["year"]: x for x in r["cells"]}
            formula = r["formula"]
            sh.append([t("cat_" + r["category"], lang), _rname(r, lang), t("academic" if r["methodology"] in ("academic", "both") else "professional", lang),
                       formula] + [cells[y]["display"] for y in years] + [t(cells[y]["status"], lang) for y in years]
                      + [(r.get("benchmark") or {}).get("value"), t(r["risk"], lang), r["risk_basis"], r["interpretation"], r["comment"],
                         r["action"], r["source"]])
            for i, y in enumerate(years):
                sh.cell(sh.max_row, 5 + len(years) + i).fill = PatternFill("solid", fgColor=STATUS_FILL[cells[y]["status"]])
        sh.column_dimensions["B"].width = 34
        sh.column_dimensions["D"].width = 40

    if "interpretation_academic" in modules and rep.get("interpretation"):
        it = rep["interpretation"]
        sh = sheet(t("acad", lang))
        header(sh, [t("ratio", lang), t("year", lang), t("basis_col", lang), t("verdict", lang), t("step", lang), t("text", lang)])
        rmap = {r["key"]: r for r in rep["ratios"]}
        for key, per_year in it["ratios"].items():
            for x in per_year:
                for i, s in enumerate(x["steps"]):
                    sh.append([_rname(rmap[key], lang) if i == 0 else "", x["year"] if i == 0 else "",
                               t(x["basis"], lang) if i == 0 else "", t(x["verdict"], lang) if i == 0 else "", s["title"], s["text"]])
        sh.append([])
        sh.append([t("dupont", lang)])
        sh.cell(sh.max_row, 1).font = Font(bold=True)
        for y, txt in it["dupont"].items():
            if txt:
                sh.append(["", y, "", "", "", txt])
        for su in it["sources_uses"]:
            sh.append([])
            sh.append([f"{t('su', lang)} {su['from_year']}–{su['to_year']}"])
            sh.cell(sh.max_row, 1).font = Font(bold=True)
            for line in su["text"]:
                sh.append(["", "", "", "", "", line])
        wrap(sh, {"A": 30, "B": 8, "C": 16, "D": 14, "E": 24, "F": 110})

    if "sources_uses" in modules:
        for su in rep["sources_uses"]:
            sh = sheet(f"{t('su', lang)[:20]} {su['from_year']}-{su['to_year']}")
            header(sh, [t(k, lang) for k in ("account", "opening", "closing", "change", "su_type", "term", "internal", "amount", "share", "desc")])
            for r in su["rows"]:
                sh.append([r["account"], r["opening"], r["closing"], r["change"], t("source_s" if r["type"] == "source" else r["type"], lang) if r["type"] else "",
                           t(r["term"], lang), "" if r["internal"] is None else t("yes" if r["internal"] else "no", lang),
                           r["amount"], _pct(r["pct"]), r["description"]])
            sh.append([])
            for k, lab in (("total_sources", "tot_src"), ("total_uses", "tot_use"), ("golden_rule_deviation", "golden"),
                           ("internal_sources_pct", "int_src")):
                sh.append([t(lab, lang), su[k]])
            sh.column_dimensions["A"].width = 34
            sh.column_dimensions["J"].width = 50

    if "interpretation" in modules or "risks" in modules or "recommendations" in modules:
        sh = sheet(t("evaluation", lang))
        ev = rep["evaluation"]
        header(sh, [t("area", lang), t("rating", lang), t("summary", lang)])
        for a in ev["areas"]:
            sh.append([a["area"], a["rating"] + (f" ({t('provisional', lang)})" if a.get("provisional") else ""), a["summary"]])
        for key, lab in (("historical_performance", "hist"), ("strengths", "strengths"), ("weaknesses", "weaknesses"),
                         ("risks", "risks"), ("recommendations", "recs")):
            sh.append([])
            sh.append([t(lab, lang)])
            sh.cell(sh.max_row, 1).font = Font(bold=True)
            for x in ev[key]:
                sh.append(["", x])
        wrap(sh, {"A": 26, "B": 100, "C": 100})
        sh2 = sheet(t("obs", lang))
        header(sh2, [t(k, lang) for k in ("level", "type", "area", "title_c", "finding", "period", "reasoning", "hypo", "impact", "conf", "req")])
        for o in rep["observations"]:
            sh2.append([o["level"], o["type_label"], o["area"], o["title"], o["finding"], o["comparison_period"], o["reasoning"],
                        o["possible_explanation"], o["financial_impact"], o["confidence"], o["required_action"]])

    if "assumptions" in modules:
        sh = sheet(t("assumptions", lang))
        header(sh, [t(k, lang) for k in ("assumption", "value", "status", "reason", "support", "decided")])
        for a in rep["assumptions"]:
            sh.append([a["name"], a["value_label"], t(a["status"], lang), a["reason"], a["supporting_data"], a.get("decided_at")])
        sh.append([])
        sh.append([t("limits", lang)])
        for x in rep["limitations"]:
            sh.append(["", x])
        wrap(sh, {"A": 40, "B": 40, "C": 14, "D": 70, "E": 60})
    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue()


# =============================================================== PDF
def pdf(rep: dict, modules: list[str]) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    lang = rep.get("lang", "en")
    ar = lang == "ar"
    if "DejaVu" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("DejaVu", str(FONT_DIR / "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
    font, bold = ("DejaVu", "DejaVu-Bold")

    def shape(txt):
        """Arabic letters must be joined (reshaped) and laid out right-to-left before reportlab draws them."""
        txt = "" if txt is None else str(txt)
        if ar and any("؀" <= ch <= "ۿ" for ch in txt):
            import arabic_reshaper
            from bidi.algorithm import get_display
            return get_display(arabic_reshaper.reshape(txt))
        return txt

    def esc(s):
        return shape(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    align = TA_RIGHT if ar else TA_LEFT
    ss = getSampleStyleSheet()
    body = ParagraphStyle("b", parent=ss["BodyText"], fontName=font, fontSize=8.5, leading=12, alignment=align)
    small = ParagraphStyle("s", parent=body, fontSize=7.5, leading=10)
    h1 = ParagraphStyle("h1", parent=ss["Title"], fontName=bold, alignment=align if ar else 1)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName=bold, alignment=align, textColor=colors.HexColor("#1F3A5F"))
    h3 = ParagraphStyle("h3", parent=ss["Heading3"], fontName=bold, alignment=align)
    good = ParagraphStyle("g", parent=h3, textColor=colors.HexColor("#1B7A3A"))
    warn = ParagraphStyle("w", parent=h3, textColor=colors.HexColor("#8A6D00"))

    from reportlab.lib.utils import simpleSplit
    from reportlab.platypus import Flowable

    class RTLPara(Flowable):
        """Arabic paragraph: reshape, break into lines at the available width, THEN reorder each line right-to-left,
        so wrapped lines keep their reading order."""

        def __init__(self, txt, style):
            super().__init__()
            self.txt, self.style, self.p = "" if txt is None else str(txt), style, None

        def wrap(self, aw, ah):
            import arabic_reshaper
            from bidi.algorithm import get_display
            lines = []
            for part in self.txt.split("\n"):
                lines += simpleSplit(arabic_reshaper.reshape(part), self.style.fontName, self.style.fontSize, max(aw - 2, 20)) or [""]
            html = "<br/>".join(get_display(ln).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") for ln in lines)
            self.p = Paragraph(html, self.style)
            return self.p.wrap(aw, ah)

        def draw(self):
            self.p.drawOn(self.canv, 0, 0)

    def P(x, st=small):
        if ar and any("\u0600" <= ch <= "\u06ff" for ch in str(x or "")):
            return RTLPara(x, st)
        return Paragraph(esc(x), st)

    def table(data, widths=None):
        if ar:  # mirror column order so the first column is on the right
            data = [list(reversed(r)) for r in data]
            widths = list(reversed(widths)) if widths else None
        tb = Table(data, colWidths=widths, repeatRows=1)
        tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3A5F")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                                ("FONTNAME", (0, 0), (-1, -1), font), ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#BBBBBB")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("ALIGN", (0, 0), (-1, -1), "RIGHT" if ar else "LEFT")]))
        return tb

    def hdr(*keys):
        return [Paragraph(esc(t(k, lang)), ParagraphStyle("th", parent=small, textColor=colors.white, fontName=bold)) for k in keys]

    bio = BytesIO()
    doc = SimpleDocTemplate(bio, pagesize=landscape(A4), leftMargin=12 * mm, rightMargin=12 * mm, topMargin=12 * mm, bottomMargin=12 * mm,
                            title=f"{t('title', lang)} — {rep['company']['name']}")
    story = []
    years = rep["years"]
    c = rep["company"]
    story += [Paragraph(esc(f"{t('title', lang)} — {c['name']}"), h1),
              P(f"{t('industry', lang)}: {c.get('industry')} · {t('currency', lang)}: {c.get('currency')} · {t('years', lang)}: "
                f"{', '.join(map(str, years))} · {t('methodology', lang)}: {t(c.get('methodology') or '', lang)} · {t('version', lang)} {rep['governance'].get('version')} · "
                f"{t('generated', lang)} {datetime.now():%Y-%m-%d %H:%M}", body), Spacer(1, 4),
              Paragraph(esc(f"{t('approval', lang)}: {rep['approval_status_text']}"), good if rep["approval_status"] == "approved" else warn)]
    ev = rep["evaluation"]
    if "interpretation" in modules:
        story.append(Paragraph(esc(t("evaluation", lang)), h2))
        story.append(table([hdr("area", "rating", "summary")] + [[P(a["area"]), P(a["rating"] + (f" ({t('provisional', lang)})" if a.get("provisional") else "")),
                                                                  P(a["summary"])] for a in ev["areas"]], [40 * mm, 35 * mm, 190 * mm]))
        for key, lab in (("historical_performance", "hist"), ("strengths", "strengths"), ("weaknesses", "weaknesses")):
            story.append(Paragraph(esc(t(lab, lang)), h3))
            story += [P("• " + x, body) for x in ev[key]] or [P(t("none", lang), body)]
    if "risks" in modules:
        story.append(Paragraph(esc(t("risks", lang)), h3))
        story += [P("• " + x, body) for x in ev["risks"]] or [P(t("no_risk", lang), body)]
    if "recommendations" in modules:
        story.append(Paragraph(esc(t("recs", lang)), h3))
        story += [P("• " + x, body) for x in ev["recommendations"]] or [P(t("no_rec", lang), body)]
    if "horizontal" in modules or "comparison" in modules or "vertical" in modules:
        story += [PageBreak(), Paragraph(esc(t("multi", lang)), h2)]
        data = [hdr("item") + [P(str(y)) for y in years] + hdr("trend", "cagr", "common_last")]
        for k in rep["key_lines"]:
            s = k["stats"]
            data.append([P(k["label"])] + [P(f"{k['values'][y]:,.0f}" if k["values"].get(y) is not None else "—") for y in years]
                        + [P(s.get("trend")), P("n/m" if s.get("cagr") is None else f"{s['cagr'] * 100:.1f}%"),
                           P("" if k["common_size"].get(years[-1]) is None else f"{k['common_size'][years[-1]] * 100:.1f}%")])
        story.append(table(data))
    if "ratios" in modules:
        story += [PageBreak(), Paragraph(esc(t("ratios", lang)), h2)]
        data = [hdr("ratio", "formula") + [P(str(y)) for y in years] + hdr("risk", "interp")]
        for r in rep["ratios"]:
            cells = {x["year"]: x for x in r["cells"]}
            data.append([P(_rname(r, lang)), P(r["formula"])] + [P(f"{cells[y]['display']} [{t(cells[y]['status'], lang)}]") for y in years]
                        + [P(t(r["risk"], lang)), P(r["interpretation"])])
        story.append(table(data, [45 * mm, 55 * mm] + [18 * mm] * len(years) + [15 * mm, 80 * mm]))
    if "interpretation_academic" in modules and rep.get("interpretation"):
        it = rep["interpretation"]
        rmap = {r["key"]: r for r in rep["ratios"]}
        story += [PageBreak(), Paragraph(esc(t("acad", lang)), h2)]
        latest = years[-1] if years else None
        for key, per_year in it["ratios"].items():
            x = next((p for p in per_year if p["year"] == latest), None)
            if not x or len(x["steps"]) < 2:
                continue
            story.append(P(f"{_rname(rmap[key], lang)} — {latest} · {t(x['verdict'], lang)}", h3))
            story.append(P(x["heading"]))
            story += [P(f"{s['title']}: {s['text']}", body) for s in x["steps"]]
        if it["dupont"].get(latest):
            story += [Paragraph(esc(t("dupont", lang)), h3), P(it["dupont"][latest], body)]
        for su in it["sources_uses"]:
            story.append(Paragraph(esc(f"{t('su', lang)} {su['from_year']}–{su['to_year']}"), h3))
            story += [P("• " + line, body) for line in su["text"]]
    if "sources_uses" in modules and rep["sources_uses"]:
        su = rep["sources_uses"][-1]
        story += [PageBreak(), Paragraph(esc(f"{t('su', lang)} {su['from_year']}–{su['to_year']}"), h2)]
        data = [hdr("account", "opening", "closing", "change", "su_type", "share", "desc")]
        for r in su["rows"]:
            if r["type"]:
                data.append([P(r["account"]), P(f"{r['opening']:,.0f}"), P(f"{r['closing']:,.0f}"), P(f"{r['change']:,.0f}"),
                             P(t("source_s" if r["type"] == "source" else "use", lang)), P("" if r["pct"] is None else f"{r['pct'] * 100:.1f}%"),
                             P(r["description"])])
        story.append(table(data))
        story.append(P(f"{t('tot_src', lang)} {su['total_sources']:,.0f} · {t('tot_use', lang)} {su['total_uses']:,.0f} · "
                       f"{t('golden', lang)} {0 if su['golden_rule_deviation'] is None else su['golden_rule_deviation'] * 100:.1f}% · "
                       f"{t('int_src', lang)} {0 if su['internal_sources_pct'] is None else su['internal_sources_pct'] * 100:.1f}%", body))
    if "assumptions" in modules:
        story += [PageBreak(), Paragraph(esc(t("assumptions", lang)), h2)]
        story.append(table([hdr("assumption", "value", "status", "reason")] +
                           [[P(a["name"]), P(a["value_label"]), P(t(a["status"], lang)), P(a["reason"])] for a in rep["assumptions"]],
                           [60 * mm, 60 * mm, 22 * mm, 125 * mm]))
        story.append(Paragraph(esc(t("limits", lang)), h3))
        story += [P("• " + x, body) for x in rep["limitations"]]
    doc.build(story)
    return bio.getvalue()
