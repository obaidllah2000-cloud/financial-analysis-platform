"""HTTP API for the Financial Analysis Platform."""
from __future__ import annotations

import asyncio
import csv
from contextlib import asynccontextmanager
import io
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from openpyxl import load_workbook
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import assumptions as asm
from . import auth
from . import interpret, localize
from . import excel_template, forecasting, llm, methodology, observations, reports, services, taxonomy
from .engine import forecast as fc_engine
from .db import get_db, init_db
from .engine.ratios import RATIOS
from .models import (Account, AccountValue, AnalysisSnapshot, Assumption, AuditLog, Benchmark, Classification, Company, RawItem,
                     Upload, User, ValidationIssue)

MAX_UPLOAD = 15 * 1024 * 1024


@asynccontextmanager
async def lifespan(_app):
    init_db()
    yield


app = FastAPI(title="AI-Powered Corporate Financial Analysis Platform", version="1.0", lifespan=lifespan)


# ------------------------------------------------------------------ password gate (active only when FAP_PASSWORD is set)
@app.middleware("http")
async def password_gate(request: Request, call_next):
    path = request.url.path
    if auth.password() and path.startswith("/api/") and not path.startswith("/api/auth/"):
        if not auth.valid(request.cookies.get(auth.COOKIE)):
            return JSONResponse({"detail": "login_required"}, status_code=401)
    return await call_next(request)


class LoginIn(BaseModel):
    password: str


@app.get("/api/auth/status")
def auth_status(request: Request):
    return {"required": bool(auth.password()), "logged_in": auth.valid(request.cookies.get(auth.COOKIE))}


@app.post("/api/auth/login")
async def login(body: LoginIn, request: Request):
    if not auth.password():
        return {"ok": True}
    if not auth.check_password(body.password):
        await asyncio.sleep(1)  # slows down guessing
        raise HTTPException(401, "Wrong password.")
    resp = JSONResponse({"ok": True})
    secure = request.headers.get("x-forwarded-proto", request.url.scheme) == "https"
    resp.set_cookie(auth.COOKIE, auth.make_token(), max_age=auth.MAX_AGE, httponly=True, samesite="lax", secure=secure)
    return resp


@app.post("/api/auth/logout")
def logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(auth.COOKIE)
    return resp


# ------------------------------------------------------------------ auth (header-based identity + roles)
def current_user(x_user_id: int | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    u = db.get(User, x_user_id) if x_user_id else None
    if u is None:
        u = db.scalars(select(User).order_by(User.id)).first()
    return u


def require(*roles):
    def dep(u: User = Depends(current_user)):
        if u.role not in roles:
            raise HTTPException(403, f"Role '{u.role}' is not allowed to perform this action.")
        return u
    return dep


WRITE = require("admin", "analyst", "reviewer")
ANALYST = require("admin", "analyst")


def company_or_404(db: Session, cid: int) -> Company:
    c = db.get(Company, cid)
    if c is None:
        raise HTTPException(404, "Company not found")
    return c


def company_dict(c: Company) -> dict:
    return {k: getattr(c, k) for k in ("id", "name", "industry", "country", "currency", "fy_end", "reporting_type", "basis",
                                       "standards", "methodology")} | {"created_at": c.created_at.isoformat()}


# ------------------------------------------------------------------ meta
@app.get("/api/users")
def users(db: Session = Depends(get_db)):
    return [{"id": u.id, "name": u.name, "role": u.role} for u in db.scalars(select(User))]


@app.get("/api/meta")
def meta():
    return {"categories": taxonomy.as_dicts(), "industries": excel_template.INDUSTRIES,
            "assumptions": [{"key": d.key, "name": d.name, "name_ar": d.name_ar, "options": d.options} for d in asm.DEFS],
            "ratios": [{"key": r.key, "name_en": r.name_en, "name_ar": r.name_ar, "category": r.category, "methodology": r.methodology,
                        "formula": r.formula, "unit": r.unit} for r in RATIOS],
            "claude_available": llm.available(), "modules": reports.MODULES}


@app.get("/api/methodology")
def methodology_db():
    return methodology.build()


@app.get("/api/template")
def template(sample: bool = False):
    data = excel_template.build(sample=sample)
    name = "financial_analysis_sample_5_years.xlsx" if sample else "financial_analysis_template.xlsx"
    return Response(data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="{name}"'})


# ------------------------------------------------------------------ companies
class CompanyIn(BaseModel):
    name: str
    industry: str = "Other"
    country: str | None = None
    currency: str | None = None
    fy_end: str | None = None
    reporting_type: str | None = None
    basis: str | None = None
    standards: str | None = None
    methodology: str = "academic"


@app.get("/api/companies")
def companies(db: Session = Depends(get_db)):
    out = []
    for c in db.scalars(select(Company).order_by(Company.id)):
        g = services.governance(db, c)
        out.append(company_dict(c) | {"governance": g})
    return out


@app.post("/api/companies")
def create_company(body: CompanyIn, db: Session = Depends(get_db), u: User = Depends(ANALYST)):
    c = Company(**body.model_dump())
    db.add(c)
    db.flush()
    services.audit(db, u.id, c.id, "company", c.id, "create", after=body.model_dump())
    db.commit()
    return company_dict(c)


@app.get("/api/companies/{cid}")
def get_company(cid: int, db: Session = Depends(get_db)):
    c = company_or_404(db, cid)
    return company_dict(c) | {"governance": services.governance(db, c)}


@app.patch("/api/companies/{cid}")
def update_company(cid: int, body: dict, db: Session = Depends(get_db), u: User = Depends(ANALYST)):
    c = company_or_404(db, cid)
    before = company_dict(c)
    for k, v in body.items():
        if k in CompanyIn.model_fields:
            setattr(c, k, v)
    if "methodology" in body and body["methodology"] != before["methodology"]:
        services.refresh_assumptions(db, c, u.id)
    services.audit(db, u.id, c.id, "company", c.id, "update", before=before, after=company_dict(c))
    db.commit()
    return company_dict(c)


# ------------------------------------------------------------------ upload & data review
@app.post("/api/companies/{cid}/upload")
async def upload(cid: int, file: UploadFile = File(...), db: Session = Depends(get_db), u: User = Depends(ANALYST)):
    c = company_or_404(db, cid)
    name = Path(file.filename or "upload.xlsx").name
    if not name.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(400, "Only .xlsx / .xlsm Excel files are accepted.")
    content = await file.read()
    if len(content) > MAX_UPLOAD:
        raise HTTPException(413, "File too large (max 15 MB).")
    if not content.startswith(b"PK"):
        raise HTTPException(400, "The file is not a valid Excel (OOXML) workbook.")
    up = services.process_upload(db, c, name, content, u.id)
    db.commit()
    return {"upload_id": up.id, "version": up.version, "summary": up.summary}


@app.get("/api/companies/{cid}/uploads")
def uploads(cid: int, db: Session = Depends(get_db)):
    return [{"id": x.id, "version": x.version, "filename": x.filename, "uploaded_at": x.uploaded_at.isoformat(), "active": x.is_active,
             "sha256": x.sha256, "summary": x.summary}
            for x in db.scalars(select(Upload).where(Upload.company_id == cid).order_by(Upload.version.desc()))]


@app.post("/api/uploads/{uid}/activate")
def activate(uid: int, db: Session = Depends(get_db), u: User = Depends(ANALYST)):
    up = db.get(Upload, uid)
    if up is None:
        raise HTTPException(404)
    for x in db.scalars(select(Upload).where(Upload.company_id == up.company_id)):
        x.is_active = x.id == uid
    services.audit(db, u.id, up.company_id, "upload", uid, "activate_version", after={"version": up.version})
    db.commit()
    return {"ok": True}


@app.get("/api/companies/{cid}/review")
def data_review(cid: int, lang: str = "en", db: Session = Depends(get_db)):
    c = company_or_404(db, cid)
    up = services.active_upload(db, cid)
    if up is None:
        return {"rows": [], "issues": []}
    issues = list(db.scalars(select(ValidationIssue).where(ValidationIssue.upload_id == up.id)))
    by_row = {}
    for i in issues:
        if i.row_no is not None:
            by_row.setdefault((i.sheet, i.row_no), []).append(i)
    vals = {v.raw_item_id: v for v in db.scalars(select(AccountValue).where(AccountValue.upload_id == up.id))}
    accs = {a.id: a for a in db.scalars(select(Account).where(Account.company_id == cid))}
    rows = []
    for r in db.scalars(select(RawItem).where(RawItem.upload_id == up.id).order_by(RawItem.id)):
        v = vals.get(r.id)
        acc = accs.get(v.account_id) if v else None
        cls = acc.classification if acc else None
        cat = taxonomy.get(services.effective_category(cls)) if cls else None
        iss = by_row.get((r.sheet, r.row_no), [])
        sev = "error" if any(i.severity == "error" for i in iss) else "warning" if any(i.severity == "warning" for i in iss) else (
            "info" if iss else "valid")
        rows.append({"raw_id": r.id, "sheet": r.sheet, "row_no": r.row_no, "code": r.account_code, "account": r.account_name,
                     "year": r.year_raw, "value": r.value_raw, "parsed_value": float(v.value) if v else None, "kind": v.kind if v else None,
                     "hint": r.class_hint, "account_id": acc.id if acc else None,
                     "suggested": cls.suggested_category if cls else None, "category_label": (cat.label_ar if lang == "ar" else cat.label_en) if cat else None,
                     "group": cat.group if cat else None, "confidence": cls.confidence if cls else None,
                     "decision": cls.status if cls else None, "validation": sev, "messages": [localize.tr(i.message, lang) for i in iss]})
    return {"version": up.version, "filename": up.filename, "rows": rows,
            "issues": [{"id": i.id, "severity": i.severity, "code": i.code, "message": localize.tr(i.message, lang), "sheet": i.sheet, "row_no": i.row_no,
                        "account": i.account, "year": i.year, "acknowledged": i.acknowledged} for i in issues],
            "checks": localize.checks(services.build_analysis(db, c).checks() if services.build_analysis(db, c) else [], lang)}


@app.post("/api/issues/{iid}/acknowledge")
def ack_issue(iid: int, db: Session = Depends(get_db), u: User = Depends(WRITE)):
    i = db.get(ValidationIssue, iid)
    if i is None:
        raise HTTPException(404)
    if i.severity == "error":
        raise HTTPException(400, "Errors cannot be acknowledged — correct the Excel file and re-upload.")
    i.acknowledged, i.acknowledged_by = True, u.id
    up = db.get(Upload, i.upload_id)
    services.audit(db, u.id, up.company_id, "validation_issue", iid, "acknowledge", after={"message": i.message})
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------------ classification review
def cls_dict(acc: Account, cls: Classification, an=None) -> dict:
    s = taxonomy.get(cls.suggested_category)
    eff = taxonomy.get(services.effective_category(cls))
    deps = an.dependents_of_category(eff.key) if an else []
    return {"account_id": acc.id, "account": acc.name, "code": acc.code, "statement": acc.statement, "description": acc.description,
            "hint": acc.class_hint, "suggested_category": cls.suggested_category, "suggested_label": s.label_en,
            "suggested_label_ar": s.label_ar, "suggested_element": s.element, "suggested_group": s.group,
            "confidence": cls.confidence, "reason": cls.reason, "question": cls.question, "options": cls.options,
            "hint_conflict": cls.hint_conflict, "status": cls.status, "approved_category": cls.approved_category,
            "effective_category": eff.key, "effective_label": eff.label_en, "effective_label_ar": eff.label_ar,
            "element": eff.element, "group": eff.group, "subtotal": eff.subtotal, "analyst_note": cls.analyst_note,
            "decided_at": cls.decided_at.isoformat() if cls.decided_at else None, "carried_over": cls.carried_over,
            "used_in_ratios": deps, "needs_more_info": bool(cls.question) and cls.status in ("pending", "info_requested")}


@app.get("/api/companies/{cid}/classifications")
def classifications(cid: int, lang: str = "en", db: Session = Depends(get_db)):
    c = company_or_404(db, cid)
    an = services.build_analysis(db, c)
    up = services.active_upload(db, cid)
    active_ids = set(db.scalars(select(AccountValue.account_id).where(AccountValue.upload_id == up.id))) if up else set()
    out = []
    for acc, cls in db.execute(select(Account, Classification).join(Classification).where(Account.company_id == cid).order_by(Account.sort_order)):
        if acc.id in active_ids:
            out.append(localize.classification(cls_dict(acc, cls, an), lang))
    return out


class Decision(BaseModel):
    action: str  # approve | modify | reject | request_info | reopen
    category: str | None = None
    note: str | None = None
    apply_similar: bool = False


def _snapshot_latest(an, keys):
    if an is None or not an.years:
        return {}
    y = an.years[-1]
    return {k: an.ratio_cell(k, y) for k in keys}


@app.post("/api/classifications/{account_id}/decide")
def decide(account_id: int, d: Decision, db: Session = Depends(get_db), u: User = Depends(WRITE)):
    acc = db.get(Account, account_id)
    if acc is None:
        raise HTTPException(404)
    company = db.get(Company, acc.company_id)
    if d.category and d.category not in taxonomy.BY_KEY:
        raise HTTPException(400, "Unknown category")
    targets = [acc]
    if d.apply_similar:
        base = acc.classification.suggested_category
        for a2, c2 in db.execute(select(Account, Classification).join(Classification).where(
                Account.company_id == acc.company_id, Account.statement == acc.statement, Account.id != acc.id,
                Classification.suggested_category == base, Classification.status == "pending")):
            targets.append(a2)
    before_an = services.build_analysis(db, company)
    old_cat = services.effective_category(acc.classification)
    new_cat = d.category or old_cat
    affected = sorted(set((before_an.dependents_of_category(old_cat) if before_an else []) +
                          (before_an.dependents_of_category(new_cat) if before_an else [])))
    before_vals = _snapshot_latest(before_an, affected)
    changed = []
    for a in targets:
        cls = a.classification
        prev = {"status": cls.status, "approved_category": cls.approved_category, "suggested": cls.suggested_category}
        if d.action == "approve":
            cls.status = "approved" if not d.category or d.category == cls.suggested_category else "modified"
            cls.approved_category = d.category or cls.suggested_category
        elif d.action == "modify":
            if not d.category:
                raise HTTPException(400, "A category is required to modify a classification.")
            cls.status, cls.approved_category = "modified", d.category
        elif d.action == "reject":
            cls.status, cls.approved_category = "rejected", None
        elif d.action == "request_info":
            cls.status = "info_requested"
        elif d.action == "reopen":
            cls.status, cls.approved_category = "pending", None
        else:
            raise HTTPException(400, "Unknown action")
        cls.analyst_note = d.note or cls.analyst_note
        cls.decided_by, cls.decided_at = u.id, datetime.now(timezone.utc)
        cls.carried_over = False
        services.audit(db, u.id, a.company_id, "classification", a.id, f"classification_{d.action}", before=prev,
                       after={"status": cls.status, "approved_category": cls.approved_category}, detail=f"{a.name}: {d.note or ''}")
        changed.append(a.id)
    db.flush()
    after_an = services.build_analysis(db, company)
    after_vals = _snapshot_latest(after_an, affected)
    impact = [{"ratio": k, "before": before_vals.get(k, {}).get("display"), "after": after_vals.get(k, {}).get("display"),
               "status_before": before_vals.get(k, {}).get("status"), "status_after": after_vals.get(k, {}).get("status")}
              for k in affected if before_vals.get(k, {}).get("display") != after_vals.get(k, {}).get("display")
              or before_vals.get(k, {}).get("status") != after_vals.get(k, {}).get("status")]
    db.commit()
    return {"changed": changed, "impact": impact, "year": after_an.years[-1] if after_an and after_an.years else None}


# ------------------------------------------------------------------ assumptions
@app.get("/api/companies/{cid}/assumptions")
def get_assumptions(cid: int, lang: str = "en", db: Session = Depends(get_db)):
    c = company_or_404(db, cid)
    an = services.build_analysis(db, c)
    facts = services.data_facts(db, c)
    relevant = {d["key"]: d["relevant"] for d in asm.detect(c.methodology, facts)}
    out = []
    for a in db.scalars(select(Assumption).where(Assumption.company_id == cid)):
        d = asm.BY_KEY.get(a.key)
        if d is None:
            continue
        impact = an.assumption_impact(a.key, [o["value"] for o in d.options]) if an else []
        deps = [r.key for r in RATIOS if a.key in r.assumptions]
        out.append({"key": a.key, "name": d.name, "name_ar": d.name_ar, "proposed_value": a.proposed_value, "value": a.value,
                    "reason": a.reason, "supporting_data": a.supporting_data, "options": d.options, "status": a.status,
                    "critical": d.critical, "relevant": relevant.get(a.key, True), "analyst_note": a.analyst_note,
                    "decided_at": a.decided_at.isoformat() if a.decided_at else None, "impact": impact, "dependent_ratios": deps})
    return [localize.assumption(x, lang) for x in out]


class AssumptionDecision(BaseModel):
    action: str  # accept | modify | reject | reopen
    value: str | None = None
    note: str | None = None


@app.post("/api/companies/{cid}/assumptions/{key}")
def decide_assumption(cid: int, key: str, d: AssumptionDecision, db: Session = Depends(get_db), u: User = Depends(WRITE)):
    a = db.scalars(select(Assumption).where(Assumption.company_id == cid, Assumption.key == key)).first()
    if a is None:
        raise HTTPException(404)
    prev = {"status": a.status, "value": a.value}
    valid = {o["value"] for o in asm.BY_KEY[key].options}
    if d.action == "accept":
        a.status, a.value = "accepted", a.proposed_value
    elif d.action == "modify":
        if d.value not in valid:
            raise HTTPException(400, f"Value must be one of {sorted(valid)}")
        a.status, a.value = ("accepted" if d.value == a.proposed_value else "modified"), d.value
    elif d.action == "reject":
        a.status = "rejected"
    elif d.action == "reopen":
        a.status, a.value = "pending", a.proposed_value
    else:
        raise HTTPException(400, "Unknown action")
    a.analyst_note = d.note or a.analyst_note
    a.decided_by, a.decided_at = u.id, datetime.now(timezone.utc)
    services.audit(db, u.id, cid, "assumption", a.id, f"assumption_{d.action}", before=prev, after={"status": a.status, "value": a.value},
                   detail=f"{key}: {d.note or ''}")
    db.commit()
    return {"ok": True, "status": a.status, "value": a.value}


# ------------------------------------------------------------------ analysis
def _years(years: str | None):
    return [int(y) for y in years.split(",") if y.strip()] if years else None


def _analysis(db, cid, years=None, methodology_=None):
    c = company_or_404(db, cid)
    an = services.build_analysis(db, c, _years(years), methodology_)
    if an is None:
        raise HTTPException(409, "No financial data uploaded yet.")
    return c, an


@app.get("/api/companies/{cid}/analysis")
def analysis(cid: int, years: str | None = None, methodology: str | None = None, lang: str = "en", db: Session = Depends(get_db)):
    c, an = _analysis(db, cid, years, methodology)
    full = an.full()
    full["ratios"] = localize.ratios(full["ratios"], lang)
    full["key_lines"] = localize.key_lines(full["key_lines"], lang)
    full["checks"] = localize.checks(full["checks"], lang)
    full["sources_uses"] = localize.sources_uses(full["sources_uses"], lang)
    if lang == "ar":
        full["status_text"] = {k: localize.tr(v, lang) for k, v in full["status_text"].items()}
        full["flag_text"] = {k: localize.tr(v, lang) for k, v in full["flag_text"].items()}
    return full | {"all_years": services.load_inputs(db, c, services.active_upload(db, cid))[1]}


@app.get("/api/companies/{cid}/interpretation")
def interpretation(cid: int, lang: str = "en", years: str | None = None, db: Session = Depends(get_db)):
    """Academic (professor's method) 7-step interpretation for every ratio and year, plus DuPont and sources & uses."""
    c, an = _analysis(db, cid, years)
    rs = localize.ratios(an.ratios(), lang)
    sus = an.sources_uses()
    return {"years": an.years, "ratios": interpret.interpret_all(rs, lang, c.currency or ""),
            "dupont": {y: interpret.interpret_dupont(rs, y, lang) for y in an.years},
            "sources_uses": [{"from_year": x["from_year"], "to_year": x["to_year"], "text": interpret.interpret_sources_uses(x, lang)}
                             for x in sus]}


@app.get("/api/companies/{cid}/statements/{st}")
def statements(cid: int, st: str, years: str | None = None, lang: str = "en", db: Session = Depends(get_db)):
    c, an = _analysis(db, cid, years)
    obs = observations.review(an)
    notes = {}
    for o in obs:
        for r in o["related"]:
            notes.setdefault(r, []).append(o["title"])
    rows = an.statement_rows(st.upper())
    for r in rows:
        r["observations"] = notes.get(r["account"], [])
    return {"years": an.years, "rows": localize.statement_rows(rows, lang),
            "key_lines": localize.key_lines([k for k in an.key_lines() if k["statement"] == st.upper()], lang)}


@app.get("/api/companies/{cid}/trace/{ratio}/{year}")
def trace(cid: int, ratio: str, year: int, lang: str = "en", db: Session = Depends(get_db)):
    c, an = _analysis(db, cid)
    if ratio not in {r.key for r in RATIOS} or year not in an.years:
        raise HTTPException(404)
    t = an.ratio_trace(ratio, year)
    if lang == "ar":
        t["cell"] = dict(t["cell"], reasons=[localize.tr(x, lang) for x in t["cell"]["reasons"]],
                         notes=[localize.tr(x, lang) for x in t["cell"]["notes"]])
        t["status_text"] = localize.tr(t["status_text"], lang)
        t["ratio"] = dict(t["ratio"], formula=interpret.formula_text(t["ratio"]["formula"], lang))
        t["inputs"] = [dict(i, label=localize.label(i["key"], i["label"], lang)) for i in t["inputs"]]
    return t


@app.get("/api/companies/{cid}/aggregate/{key}/{year}")
def aggregate(cid: int, key: str, year: int, db: Session = Depends(get_db)):
    c, an = _analysis(db, cid)
    d = an.aggregate_detail(key, year)
    if d is None:
        raise HTTPException(404)
    return d


@app.get("/api/companies/{cid}/observations")
def get_observations(cid: int, lang: str = "en", db: Session = Depends(get_db)):
    c, an = _analysis(db, cid)
    return localize.observations(observations.review(an, services.pending_questions(db, c)), lang)


class Chat(BaseModel):
    question: str
    lang: str = "en"


@app.post("/api/companies/{cid}/chat")
def chat(cid: int, body: Chat, db: Session = Depends(get_db)):
    c, an = _analysis(db, cid)
    obs = observations.review(an, services.pending_questions(db, c))
    ratios = an.ratios()
    ctx = {"company": company_dict(c), "years": an.years, "governance": services.governance(db, c),
           "ratios": [{"key": r["key"], "name": r["name_en"], "formula": r["formula"],
                       "values": {x["year"]: {"value": x["display"], "status": x["status"]} for x in r["cells"]},
                       "risk": r["risk"], "benchmark": r["benchmark"]} for r in ratios],
           "key_lines": [{"label": k["label"], "values": k["values"]} for k in an.key_lines()],
           "observations": obs, "assumptions": an.assumptions}
    res = llm.ask(body.question, ctx)
    if not res["ok"]:
        q = body.question.lower()
        rel = [o for o in obs if any(w in (o["title"] + o["area"] + o["finding"]).lower() for w in q.split() if len(w) > 3)] or obs[:5]
        res["fallback"] = localize.observations(rel[:6], body.lang)
        if body.lang == "ar":
            res["reason"] = "Claude غير مفعّل على الخادم (لم يُضبط ANTHROPIC_API_KEY). هذه هي الملاحظات المطابقة من محرك التحليل:"
    return res


def build_report(db: Session, c: Company, years=None, methodology_=None, lang: str = "en") -> dict:
    an = services.build_analysis(db, c, years, methodology_)
    if an is None:
        raise HTTPException(409, "No financial data uploaded yet.")
    gov = services.governance(db, c)
    obs = localize.observations(observations.review(an, services.pending_questions(db, c)), lang)
    ratios = localize.ratios(an.ratios(), lang)
    ev = observations.evaluation(an, ratios, obs, lang)
    ass = []
    for a in db.scalars(select(Assumption).where(Assumption.company_id == c.id)):
        d = asm.BY_KEY.get(a.key)
        if d is None:
            continue
        label = next((o["label"] for o in d.options if o["value"] == a.value), a.value)
        ass.append({"key": a.key, "name": d.name_ar if lang == "ar" else d.name, "value": a.value,
                    "value_label": localize.tr(label, lang), "status": a.status, "reason": localize.tr(a.reason, lang),
                    "supporting_data": localize.tr(a.supporting_data, lang), "decided_at": a.decided_at.isoformat() if a.decided_at else None})
    limitations = []
    if gov.get("critical_pending_classifications"):
        limitations.append(f"{gov['critical_pending_classifications']} account classification(s) are not yet approved — dependent results are provisional.")
    if gov.get("pending_assumptions"):
        limitations.append("Assumptions awaiting analyst confirmation: " + ", ".join(gov["pending_assumptions"]) + ".")
    if gov.get("issues", {}).get("error"):
        limitations.append(f"{gov['issues']['error']} unresolved data error(s) — affected results are invalid.")
    if not services.benchmarks_for(db, c):
        limitations.append(f"No benchmarks configured for '{c.industry}'. Risk levels rely on historical trends and absolute thresholds only.")
    nb = sum(1 for r in ratios for x in r["cells"] if x["status"] == "needs_info")
    if nb:
        limitations.append(f"{nb} ratio-year result(s) require additional information (e.g. share data, credit purchases, cost behaviour).")
    limitations.append("Interpretations are rule-based explanations of verified calculations; possible causes are hypotheses to be confirmed with management.")
    snap = db.scalars(select(AnalysisSnapshot).where(AnalysisSnapshot.company_id == c.id).order_by(AnalysisSnapshot.id.desc())).first()
    last_change = db.scalars(select(AuditLog.ts).where(AuditLog.company_id == c.id, AuditLog.action != "approve_analysis")
                             .order_by(AuditLog.ts.desc())).first()
    up = services.active_upload(db, c.id)
    approved = bool(snap and up and snap.upload_id == up.id and (last_change is None or _aware(snap.approved_at) >= _aware(last_change)))
    status = "approved" if approved else ("ready_for_approval" if gov.get("ready_for_approval") else "provisional")
    limitations = [localize.tr(x, lang) for x in limitations]
    status_text = {"approved": f"Approved by analyst on {snap.approved_at:%Y-%m-%d %H:%M}" if approved else "",
                   "ready_for_approval": "Draft — all reviews complete, awaiting analyst approval",
                   "provisional": "PROVISIONAL — pending classifications, assumptions or data errors remain"}[status]
    sus = an.sources_uses()
    yrs = an.years
    return {"company": company_dict(c), "years": yrs, "lang": lang, "governance": gov,
            "key_lines": localize.key_lines(an.key_lines(), lang), "ratios": ratios,
            "statements": {st: localize.statement_rows(an.statement_rows(st), lang) for st in ("BS", "IS", "CF")},
            "sources_uses": localize.sources_uses(sus, lang),
            "interpretation": {"ratios": interpret.interpret_all(ratios, lang, c.currency or ""),
                               "dupont": {y: interpret.interpret_dupont(ratios, y, lang) for y in yrs},
                               "sources_uses": [{"from_year": x["from_year"], "to_year": x["to_year"],
                                                 "text": interpret.interpret_sources_uses(x, lang)} for x in sus]},
            "observations": obs, "evaluation": ev, "assumptions": ass, "limitations": limitations, "approval_status": status,
            "approval_status_text": localize.tr(status_text, lang),
            "status_text": {k: localize.tr(v, lang) for k, v in an.full()["status_text"].items()}, "flag_text": an.full()["flag_text"],
            "checks": localize.checks(an.checks(), lang)}


def _aware(d):
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


@app.get("/api/companies/{cid}/evaluation")
def evaluation(cid: int, years: str | None = None, lang: str = "en", db: Session = Depends(get_db)):
    c = company_or_404(db, cid)
    r = build_report(db, c, _years(years), lang=lang)
    return {k: r[k] for k in ("evaluation", "limitations", "approval_status", "approval_status_text", "governance", "observations", "years")}


@app.post("/api/companies/{cid}/approve")
def approve(cid: int, db: Session = Depends(get_db), u: User = Depends(ANALYST)):
    c = company_or_404(db, cid)
    gov = services.governance(db, c)
    if not gov.get("ready_for_approval"):
        raise HTTPException(409, {"message": "Analysis cannot be approved yet.", "governance": gov})
    rep = build_report(db, c)
    up = services.active_upload(db, cid)
    snap = AnalysisSnapshot(company_id=cid, upload_id=up.id, approved_by=u.id, status="approved",
                            results={"ratios": [{"key": r["key"], "cells": r["cells"]} for r in rep["ratios"]],
                                     "evaluation": rep["evaluation"], "assumptions": rep["assumptions"]})
    db.add(snap)
    db.flush()
    services.audit(db, u.id, cid, "analysis", snap.id, "approve_analysis", after={"upload_version": up.version})
    db.commit()
    return {"ok": True, "snapshot_id": snap.id}


@app.get("/api/companies/{cid}/report.{fmt}")
def report(cid: int, fmt: str, years: str | None = None, modules: str | None = None, lang: str = "en",
           db: Session = Depends(get_db)):
    c = company_or_404(db, cid)
    rep = build_report(db, c, _years(years), lang=lang)
    mods = modules.split(",") if modules else reports.MODULES
    safe = "".join(ch for ch in c.name if ch.isalnum() or ch in " -_").strip().replace(" ", "_") or "company"
    if fmt == "xlsx":
        return Response(reports.excel(rep, mods), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={"Content-Disposition": f'attachment; filename="{safe}_financial_analysis_{lang}.xlsx"'})
    if fmt == "pdf":
        return Response(reports.pdf(rep, mods), media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="{safe}_financial_analysis_{lang}.pdf"'})
    raise HTTPException(404)


@app.get("/api/companies/{cid}/report")
def report_json(cid: int, years: str | None = None, lang: str = "en", db: Session = Depends(get_db)):
    return build_report(db, company_or_404(db, cid), _years(years), lang=lang)


@app.get("/api/companies/{cid}/audit")
def audit_log(cid: int, db: Session = Depends(get_db)):
    users_ = {u.id: u.name for u in db.scalars(select(User))}
    return [{"id": a.id, "ts": a.ts.isoformat(), "user": users_.get(a.user_id), "entity": a.entity, "entity_id": a.entity_id,
             "action": a.action, "before": a.before, "after": a.after, "detail": a.detail}
            for a in db.scalars(select(AuditLog).where(AuditLog.company_id == cid).order_by(AuditLog.id.desc()).limit(500))]


# ------------------------------------------------------------------ forecasting & planning (scenarios — never approved data)
@app.get("/api/companies/{cid}/forecast/base")
def forecast_base(cid: int, db: Session = Depends(get_db)):
    c, an = _analysis(db, cid)
    return forecasting.base(an, services.benchmarks_for(db, c))


def _scenario(fn, body):
    try:
        return fn(body)
    except (ValueError, KeyError, ArithmeticError) as e:
        raise HTTPException(400, f"Invalid scenario input: {e}")


@app.post("/api/companies/{cid}/forecast/position")
def forecast_position(cid: int, body: dict, db: Session = Depends(get_db)):
    company_or_404(db, cid)
    return _scenario(forecasting.run_position, body)


@app.post("/api/companies/{cid}/forecast/percent-of-sales")
def forecast_percent(cid: int, body: dict, db: Session = Depends(get_db)):
    company_or_404(db, cid)
    return _scenario(forecasting.run_percent, body)


@app.post("/api/forecast/breakeven")
def forecast_breakeven(body: dict):
    D = forecasting.D
    opt = lambda k: D(body[k]) if body.get(k) not in (None, "") else None  # noqa: E731
    return _scenario(lambda b: fc_engine.breakeven(D(b["fc"]), opt("price"), opt("avc"), opt("sales"), opt("vc"), opt("units")), body)


@app.post("/api/forecast/cash-budget")
def forecast_cash_budget(body: dict):
    D = forecasting.D

    def run(b):
        n = len(b["months"])
        pad = lambda xs: [D(x) for x in (xs + [0] * n)[:n]]  # noqa: E731
        return fc_engine.cash_budget(b["months"], pad(b["sales"]), D(b["cash_pct"]), [D(x) for x in b["lags"]], pad(b.get("other_receipts", [])),
                                     {k: pad(v) for k, v in b["payments"].items()}, D(b["opening"]), D(b["min_cash"]), int(b.get("show_from", 0)))
    return _scenario(run, body)


# ------------------------------------------------------------------ benchmarks
PRESETS = {
    "generic": ("Generic textbook rule of thumb — not industry data",
                {"current_ratio": 2.0, "quick_ratio": 1.0, "debt_ratio": 0.5, "interest_coverage": 3.0}),
    "course_assignment": ("Course assignment (Lecture 9) industry averages — teaching example",
                          {"quick_ratio": 2.0, "debt_ratio": 0.6, "tato": 7.14, "fato": 6.15, "cato": 15.2, "inventory_turnover": 12,
                           "ar_turnover": 12, "cash_ratio": 0.8}),
    "course_q1": ("Final exam model B, Q1 industry ratios — teaching example",
                  {"tato": 3.0, "fato": 4.0, "cash_turnover": 80, "acp": 40, "asp": 45}),
}


class BenchIn(BaseModel):
    industry: str
    ratio_key: str
    value: float
    source: str = "User entered"


@app.get("/api/benchmarks")
def get_benchmarks(industry: str | None = None, db: Session = Depends(get_db)):
    q = select(Benchmark)
    if industry:
        q = q.where(Benchmark.industry == industry)
    return {"items": [{"id": b.id, "industry": b.industry, "ratio_key": b.ratio_key, "value": b.value, "source": b.source}
                      for b in db.scalars(q.order_by(Benchmark.industry, Benchmark.ratio_key))],
            "presets": {k: {"label": v[0], "values": v[1]} for k, v in PRESETS.items()}}


def _upsert_bench(db, industry, key, value, source):
    if key not in {r.key for r in RATIOS}:
        raise HTTPException(400, f"Unknown ratio key '{key}'")
    b = db.scalars(select(Benchmark).where(Benchmark.industry == industry, Benchmark.ratio_key == key)).first()
    if b:
        b.value, b.source = value, source
    else:
        db.add(Benchmark(industry=industry, ratio_key=key, value=value, source=source))


@app.post("/api/benchmarks")
def add_benchmark(b: BenchIn, db: Session = Depends(get_db), u: User = Depends(WRITE)):
    _upsert_bench(db, b.industry, b.ratio_key, b.value, b.source)
    services.audit(db, u.id, None, "benchmark", None, "upsert", after=b.model_dump())
    db.commit()
    return {"ok": True}


@app.delete("/api/benchmarks/{bid}")
def del_benchmark(bid: int, db: Session = Depends(get_db), u: User = Depends(WRITE)):
    b = db.get(Benchmark, bid)
    if b:
        services.audit(db, u.id, None, "benchmark", bid, "delete", before={"industry": b.industry, "ratio": b.ratio_key, "value": b.value})
        db.delete(b)
        db.commit()
    return {"ok": True}


@app.post("/api/benchmarks/preset")
def apply_preset(body: dict, db: Session = Depends(get_db), u: User = Depends(WRITE)):
    label, vals = PRESETS[body["preset"]]
    for k, v in vals.items():
        _upsert_bench(db, body["industry"], k, v, label)
    services.audit(db, u.id, None, "benchmark", None, "apply_preset", after=body)
    db.commit()
    return {"ok": True}


@app.post("/api/benchmarks/import")
async def import_benchmarks(file: UploadFile = File(...), db: Session = Depends(get_db), u: User = Depends(WRITE)):
    content = await file.read()
    rows = []
    if (file.filename or "").lower().endswith(".csv"):
        rows = list(csv.reader(io.StringIO(content.decode("utf-8-sig"))))
    else:
        wb = load_workbook(io.BytesIO(content), data_only=True)
        rows = [list(r) for r in wb.active.iter_rows(values_only=True)]
    n = 0
    for r in rows[1:]:
        if not r or not r[0]:
            continue
        _upsert_bench(db, str(r[0]).strip(), str(r[1]).strip(), float(r[2]), str(r[3]) if len(r) > 3 and r[3] else "Imported")
        n += 1
    services.audit(db, u.id, None, "benchmark", None, "import", detail=f"{n} rows from {file.filename}")
    db.commit()
    return {"imported": n}


# ------------------------------------------------------------------ multi-company comparison
@app.get("/api/compare")
def compare(ids: str, ratios: str | None = None, db: Session = Depends(get_db)):
    cos = [company_or_404(db, int(i)) for i in ids.split(",") if i.strip()]
    keys = ratios.split(",") if ratios else ["current_ratio", "quick_ratio", "debt_ratio", "interest_coverage", "tato", "inventory_turnover",
                                             "acp", "gpm", "oim", "nim", "roi", "roe", "robf"]
    out, warnings = [], []
    ccy = {c.currency for c in cos}
    meth = {c.methodology for c in cos}
    fye = {c.fy_end for c in cos}
    basis = {c.basis for c in cos}
    if len(ccy) > 1:
        warnings.append(f"Different reporting currencies {sorted(map(str, ccy))}: absolute amounts are NOT comparable; only ratios are shown.")
    if len(meth) > 1:
        warnings.append("Companies use different methodologies (academic vs professional) — ratio definitions differ. Align them before comparing.")
    if len(fye) > 1:
        warnings.append(f"Different financial year ends {sorted(map(str, fye))} — periods are not fully aligned.")
    if len(basis) > 1:
        warnings.append("Different financial-statement bases — comparisons should be read with care.")
    year_sets = []
    for c in cos:
        an = services.build_analysis(db, c)
        if an is None:
            warnings.append(f"{c.name} has no data.")
            continue
        year_sets.append(set(an.years))
        rows = {}
        for k in keys:
            rows[k] = {y: an.ratio_cell(k, y) for y in an.years}
        out.append({"company": company_dict(c), "years": an.years, "ratios": rows,
                    "governance": services.governance(db, c)})
        if any(x["status"] == "provisional" for r in rows.values() for x in r.values()):
            warnings.append(f"{c.name}: some results are provisional (pending reviews).")
    common = sorted(set.intersection(*year_sets)) if year_sets else []
    if year_sets and not common:
        warnings.append("No common financial years between the selected companies.")
    meta = {r.key: {"name_en": r.name_en, "name_ar": r.name_ar, "unit": r.unit, "higher_is_better": r.higher_is_better} for r in RATIOS if r.key in keys}
    return {"companies": out, "common_years": common, "warnings": warnings, "ratio_meta": meta, "compatible": len(warnings) == 0}


# ------------------------------------------------------------------ frontend
FRONT = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if FRONT.exists():
    app.mount("/assets", StaticFiles(directory=FRONT / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(404)
        f = FRONT / path
        return FileResponse(f if path and f.is_file() else FRONT / "index.html")
