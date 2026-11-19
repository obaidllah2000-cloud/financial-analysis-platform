"""Excel and PDF report exports. Both render the SAME report dict that the dashboard uses."""
from __future__ import annotations

from datetime import datetime
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

MODULES = ["profile", "statements", "horizontal", "vertical", "ratios", "comparison", "sources_uses", "interpretation",
           "risks", "recommendations", "assumptions"]
STATUS_FILL = {"verified": "D9F2E3", "approved_assumption": "DDEBFF", "provisional": "FFF2CC", "needs_info": "EEEEEE", "invalid": "F8D7DA"}
HEAD = PatternFill("solid", fgColor="1F3A5F")


def _pct(x):
    return None if x is None else round(x * 100, 2)


def excel(rep: dict, modules: list[str]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Profile"
    c = rep["company"]
    ws.append(["Financial Analysis Report"])
    ws["A1"].font = Font(bold=True, size=14)
    for k in ("name", "industry", "country", "currency", "fy_end", "reporting_type", "basis", "standards", "methodology"):
        ws.append([k.replace("_", " ").title(), c.get(k)])
    ws.append(["Years", ", ".join(map(str, rep["years"]))])
    ws.append(["Data version", rep["governance"].get("version")])
    ws.append(["Generated", datetime.now().strftime("%Y-%m-%d %H:%M")])
    ws.append(["Approval status", rep["approval_status"]])
    ws.append([])
    ws.append(["Status legend"])
    for k, v in rep["status_text"].items():
        ws.append([k, v])
        ws.cell(ws.max_row, 1).fill = PatternFill("solid", fgColor=STATUS_FILL[k])
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 90
    years = rep["years"]

    def header(sh, cols):
        sh.append(cols)
        for cell in sh[sh.max_row]:
            cell.fill, cell.font = HEAD, Font(bold=True, color="FFFFFF")
            cell.alignment = Alignment(wrap_text=True)

    if "statements" in modules:
        for st, title in (("BS", "Balance Sheet"), ("IS", "Income Statement"), ("CF", "Cash Flow")):
            rows = rep["statements"].get(st, [])
            if not rows:
                continue
            sh = wb.create_sheet(title)
            header(sh, ["Original account", "Approved classification", "Status"] + [f"{y} original" for y in years] + [f"{y} normalized" for y in years])
            for r in rows:
                sh.append([r["account"], r["category_label"], r["status"]] + [r["values"].get(y) for y in years] + [r["normalized"].get(y) for y in years])
            sh.column_dimensions["A"].width = 38
            sh.column_dimensions["B"].width = 40
    if "horizontal" in modules or "comparison" in modules:
        sh = wb.create_sheet("Horizontal & Trends")
        header(sh, ["Item"] + [str(y) for y in years] + [f"Δ% {y}" for y in years[1:]] + ["Trend", "Average", "Highest", "Lowest", "Cumulative %", "CAGR %", "Note"])
        for k in rep["key_lines"]:
            s = k["stats"]
            chg = {c["year"]: c for c in s["changes"]}
            note = "; ".join(sorted({rep["flag_text"].get(c["flag"], "") for c in s["changes"] if c.get("flag")} |
                                    ({rep["flag_text"].get(s.get("cagr_flag"), "")} if s.get("cagr_flag") else set())))
            sh.append([k["label"]] + [k["values"].get(y) for y in years] + [_pct(chg.get(y, {}).get("pct_change")) for y in years[1:]] +
                      [s.get("trend"), s.get("average"), (s.get("highest") or {}).get("value"), (s.get("lowest") or {}).get("value"),
                       _pct(s.get("cumulative_pct")), _pct(s.get("cagr")), note])
        sh.column_dimensions["A"].width = 36
    if "vertical" in modules:
        sh = wb.create_sheet("Vertical (common size)")
        header(sh, ["Item", "Base"] + [f"{y} %" for y in years])
        for k in rep["key_lines"]:
            if k["statement"] == "CF":
                continue
            sh.append([k["label"], "Total assets" if k["statement"] == "BS" else "Sales"] + [_pct(k["common_size"].get(y)) for y in years])
        sh.column_dimensions["A"].width = 36
    if "ratios" in modules:
        sh = wb.create_sheet("Ratios")
        header(sh, ["Category", "Ratio", "Methodology", "Formula"] + [str(y) for y in years] + [f"Status {y}" for y in years] +
               ["Benchmark", "Risk", "Risk basis", "Interpretation", "Comment", "Suggested action", "Source"])
        for r in rep["ratios"]:
            cells = {c["year"]: c for c in r["cells"]}
            row = [r["category"], r["name_en"], r["methodology"], r["formula"]] + [cells[y]["display"] for y in years] + \
                  [cells[y]["status"] for y in years] + [(r.get("benchmark") or {}).get("value"), r["risk"], r["risk_basis"],
                                                        r["interpretation"], r["comment"], r["action"], r["source"]]
            sh.append(row)
            for i, y in enumerate(years):
                sh.cell(sh.max_row, 5 + len(years) + i).fill = PatternFill("solid", fgColor=STATUS_FILL[cells[y]["status"]])
        sh.column_dimensions["B"].width = 34
        sh.column_dimensions["D"].width = 40
    if "sources_uses" in modules:
        for su in rep["sources_uses"]:
            sh = wb.create_sheet(f"S&U {su['from_year']}-{su['to_year']}"[:31])
            header(sh, ["Account", "Opening", "Closing", "Change", "Source/Use", "Term", "Internal?", "Amount", "% of total", "Description"])
            for r in su["rows"]:
                sh.append([r["account"], r["opening"], r["closing"], r["change"], r["type"], r["term"], r["internal"], r["amount"], _pct(r["pct"]), r["description"]])
            sh.append([])
            for k in ("total_sources", "total_uses", "difference", "reconciled", "short_term_sources_pct", "short_term_uses_pct",
                      "long_term_sources_pct", "long_term_uses_pct", "internal_sources_pct", "external_sources_pct", "golden_rule_deviation"):
                sh.append([k, su[k]])
            sh.column_dimensions["A"].width = 34
            sh.column_dimensions["J"].width = 50
    if "interpretation" in modules or "risks" in modules or "recommendations" in modules:
        sh = wb.create_sheet("Evaluation")
        ev = rep["evaluation"]
        header(sh, ["Area", "Rating", "Summary"])
        for a in ev["areas"]:
            sh.append([a["area"], a["rating"] + (" (provisional)" if a.get("provisional") else ""), a["summary"]])
        for title, key in (("Historical performance", "historical_performance"), ("Strengths", "strengths"), ("Weaknesses", "weaknesses"),
                           ("Risks", "risks"), ("Recommendations", "recommendations")):
            sh.append([])
            sh.append([title])
            sh.cell(sh.max_row, 1).font = Font(bold=True)
            for x in ev[key]:
                sh.append(["", x])
        sh.column_dimensions["A"].width = 24
        sh.column_dimensions["B"].width = 100
        sh.column_dimensions["C"].width = 100
        sh2 = wb.create_sheet("AI Observations")
        header(sh2, ["Level", "Type", "Area", "Title", "Finding", "Period", "Reasoning", "Possible explanation (hypothesis)", "Impact", "Confidence", "Required action"])
        for o in rep["observations"]:
            sh2.append([o["level"], o["type_label"], o["area"], o["title"], o["finding"], o["comparison_period"], o["reasoning"],
                        o["possible_explanation"], o["financial_impact"], o["confidence"], o["required_action"]])
    if "assumptions" in modules:
        sh = wb.create_sheet("Assumptions & Limitations")
        header(sh, ["Assumption", "Value", "Status", "Reason", "Supporting data", "Decided at"])
        for a in rep["assumptions"]:
            sh.append([a["name"], a["value_label"], a["status"], a["reason"], a["supporting_data"], a.get("decided_at")])
        sh.append([])
        sh.append(["Limitations"])
        for x in rep["limitations"]:
            sh.append(["", x])
        sh.column_dimensions["A"].width = 40
        sh.column_dimensions["D"].width = 70
    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue()


def pdf(rep: dict, modules: list[str]) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    bio = BytesIO()
    doc = SimpleDocTemplate(bio, pagesize=landscape(A4), leftMargin=12 * mm, rightMargin=12 * mm, topMargin=12 * mm, bottomMargin=12 * mm,
                            title=f"Financial analysis — {rep['company']['name']}")
    ss = getSampleStyleSheet()
    small = ParagraphStyle("small", parent=ss["BodyText"], fontSize=8, leading=10)
    story = []
    years = rep["years"]
    c = rep["company"]

    def P(t, st=small):
        return Paragraph(str(t if t is not None else "").replace("&", "&amp;").replace("<", "&lt;"), st)

    def table(data, widths=None, status_cols=None):
        t = Table(data, colWidths=widths, repeatRows=1)
        style = [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3A5F")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                 ("FONTSIZE", (0, 0), (-1, -1), 7.5), ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#BBBBBB")),
                 ("VALIGN", (0, 0), (-1, -1), "TOP")]
        t.setStyle(TableStyle(style))
        return t

    story += [Paragraph(f"Financial Analysis Report — {c['name']}", ss["Title"]),
              P(f"Industry: {c.get('industry')} · Currency: {c.get('currency')} · Years: {', '.join(map(str, years))} · "
                f"Methodology: {c.get('methodology')} · Data version {rep['governance'].get('version')} · Generated {datetime.now():%Y-%m-%d %H:%M}"),
              Spacer(1, 4)]
    status_style = ParagraphStyle("st", parent=ss["Heading3"], textColor=colors.HexColor("#8A6D00") if rep["approval_status"] != "approved" else colors.HexColor("#1B7A3A"))
    story.append(Paragraph(f"Approval status: {rep['approval_status_text']}", status_style))
    ev = rep["evaluation"]
    if "interpretation" in modules:
        story.append(Paragraph("Executive evaluation", ss["Heading2"]))
        story.append(table([["Area", "Rating", "Summary"]] + [[P(a["area"]), P(a["rating"] + (" (provisional)" if a.get("provisional") else "")), P(a["summary"])]
                                                            for a in ev["areas"]], [40 * mm, 35 * mm, 190 * mm]))
        for title, key in (("Historical performance", "historical_performance"), ("Strengths", "strengths"), ("Weaknesses", "weaknesses")):
            story.append(Paragraph(title, ss["Heading3"]))
            story += [P("• " + x) for x in ev[key]] or [P("None identified.")]
    if "risks" in modules:
        story.append(Paragraph("Risk assessment", ss["Heading3"]))
        story += [P("• " + x) for x in ev["risks"]] or [P("No material risks flagged by the rules.")]
    if "recommendations" in modules:
        story.append(Paragraph("Management recommendations", ss["Heading3"]))
        story += [P("• " + x) for x in ev["recommendations"]] or [P("No specific recommendations.")]
    if "horizontal" in modules or "comparison" in modules or "vertical" in modules:
        story += [PageBreak(), Paragraph("Multi-year comparison (horizontal & vertical)", ss["Heading2"])]
        data = [["Item"] + [str(y) for y in years] + ["Trend", "CAGR", "Common size (last)"]]
        for k in rep["key_lines"]:
            s = k["stats"]
            data.append([P(k["label"])] + [f"{k['values'][y]:,.0f}" if k["values"].get(y) is not None else "n/a" for y in years] +
                        [s.get("trend"), "n/m" if s.get("cagr") is None else f"{s['cagr'] * 100:.1f}%",
                         "" if k["common_size"].get(years[-1]) is None else f"{k['common_size'][years[-1]] * 100:.1f}%"])
        story.append(table(data))
    if "ratios" in modules:
        story += [PageBreak(), Paragraph("Financial ratios", ss["Heading2"])]
        data = [["Ratio", "Formula"] + [str(y) for y in years] + ["Risk", "Interpretation"]]
        for r in rep["ratios"]:
            cells = {x["year"]: x for x in r["cells"]}
            data.append([P(r["name_en"]), P(r["formula"])] + [P(f"{cells[y]['display']}\n[{cells[y]['status']}]") for y in years] +
                        [r["risk"], P(r["interpretation"])])
        w = [45 * mm, 55 * mm] + [18 * mm] * len(years) + [15 * mm, 80 * mm]
        story.append(table(data, w))
    if "sources_uses" in modules and rep["sources_uses"]:
        su = rep["sources_uses"][-1]
        story += [PageBreak(), Paragraph(f"Sources & uses of money {su['from_year']}–{su['to_year']}", ss["Heading2"])]
        data = [["Account", "Opening", "Closing", "Change", "Source / Use", "%", "Description"]]
        for r in su["rows"]:
            if r["type"]:
                data.append([P(r["account"]), f"{r['opening']:,.0f}", f"{r['closing']:,.0f}", f"{r['change']:,.0f}", r["type"],
                             "" if r["pct"] is None else f"{r['pct'] * 100:.1f}%", P(r["description"])])
        story.append(table(data))
        story.append(P(f"Total sources {su['total_sources']:,.0f} · total uses {su['total_uses']:,.0f} · reconciled: {su['reconciled']} · "
                       f"golden-rule deviation {0 if su['golden_rule_deviation'] is None else su['golden_rule_deviation'] * 100:.1f}% · "
                       f"internal sources {0 if su['internal_sources_pct'] is None else su['internal_sources_pct'] * 100:.1f}%"))
    if "assumptions" in modules:
        story += [PageBreak(), Paragraph("Assumptions and limitations", ss["Heading2"])]
        story.append(table([["Assumption", "Value", "Status", "Reason"]] +
                           [[P(a["name"]), P(a["value_label"]), a["status"], P(a["reason"])] for a in rep["assumptions"]],
                           [60 * mm, 60 * mm, 22 * mm, 125 * mm]))
        story.append(Paragraph("Limitations", ss["Heading3"]))
        story += [P("• " + x) for x in rep["limitations"]]
    doc.build(story)
    return bio.getvalue()
