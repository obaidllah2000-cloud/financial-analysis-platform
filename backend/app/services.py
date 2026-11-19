"""Glue between the database and the pure calculation engine."""
from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import assumptions as asm
from . import classify, ingest, taxonomy
from .engine.aggregate import AccountInput
from .engine.analysis import Analysis
from .models import (AccountValue, AdditionalValue, Account, Assumption, AuditLog, Benchmark, Classification, Company, RawItem,
                     Upload, ValidationIssue)

STATEMENT_OF = {"BS": "BS", "IS": "IS", "CF": "CF"}


def audit(db: Session, user_id, company_id, entity, entity_id, action, before=None, after=None, detail=None):
    db.add(AuditLog(user_id=user_id, company_id=company_id, entity=entity, entity_id=entity_id, action=action,
                    before=before, after=after, detail=detail))


def active_upload(db: Session, company_id: int) -> Upload | None:
    return db.scalars(select(Upload).where(Upload.company_id == company_id, Upload.is_active.is_(True))
                      .order_by(Upload.version.desc())).first()


def effective_category(c: Classification) -> str:
    if c.status in ("approved", "modified") and c.approved_category:
        return c.approved_category
    return c.suggested_category


# ------------------------------------------------------------------------------------------- upload
def process_upload(db: Session, company: Company, filename: str, content: bytes, user_id: int | None) -> Upload:
    parsed = ingest.parse(content)
    version = (db.scalar(select(func.max(Upload.version)).where(Upload.company_id == company.id)) or 0) + 1
    for u in db.scalars(select(Upload).where(Upload.company_id == company.id, Upload.is_active.is_(True))):
        u.is_active = False
    up = Upload(company_id=company.id, version=version, filename=filename, sha256=hashlib.sha256(content).hexdigest(),
                uploaded_by=user_id, company_info=parsed.company_info)
    db.add(up)
    db.flush()

    # Company profile: fill blanks from the file; record conflicts instead of overwriting silently
    for k, v in parsed.company_info.items():
        cur = getattr(company, k, None)
        if not cur:
            setattr(company, k, v)
        elif str(cur).strip().lower() != str(v).strip().lower():
            parsed.issue("warning", "PROFILE_CONFLICT", f"Company_Info '{k}' in the file ('{v}') differs from the profile ('{cur}'). "
                         "The profile was not changed.")

    existing = {(a.statement, a.name_key): a for a in db.scalars(select(Account).where(Account.company_id == company.id))}
    new_accounts, order = [], 0
    suggestions_input = []
    for sk in ("BS", "IS", "CF"):
        for r in parsed.rows[sk]:
            raw = RawItem(upload_id=up.id, sheet=r.sheet, row_no=r.row_no, account_code=r.code, account_name=r.name,
                          description=r.description, section=r.section, year_raw=r.year_raw, value_raw=r.value_raw,
                          class_hint=r.hint, currency=r.currency, notes=r.notes)
            db.add(raw)
            db.flush()
            if not (r.name or r.code) or r.year is None or r.value is None:
                continue
            nk = classify.norm(r.name or r.code)
            if sk == "CF" and r.section:
                nk = f"{nk}|{r.section.lower()}"
            acc = existing.get((sk, nk))
            if acc is None:
                order += 1
                acc = Account(company_id=company.id, statement=sk, code=r.code, name=r.name or r.code, name_key=nk,
                              description=r.description, section=r.section, class_hint=r.hint, sort_order=order)
                db.add(acc)
                db.flush()
                existing[(sk, nk)] = acc
                new_accounts.append(acc)
            else:
                if acc.sort_order == 0:
                    order += 1
                    acc.sort_order = order
                acc.class_hint = r.hint or acc.class_hint
            db.add(AccountValue(account_id=acc.id, upload_id=up.id, raw_item_id=raw.id, year=r.year, kind="closing", value=r.value))

    # opening balances → match by code first, then name
    by_code = {a.code: a for a in existing.values() if a.code and a.statement == "BS"}
    by_name = {a.name_key: a for a in existing.values() if a.statement == "BS"}
    for r in parsed.rows["opening"]:
        raw = RawItem(upload_id=up.id, sheet=r.sheet, row_no=r.row_no, account_code=r.code, account_name=r.name,
                      year_raw=r.year_raw, value_raw=r.value_raw, notes=r.notes)
        db.add(raw)
        db.flush()
        acc = by_code.get(r.code) or by_name.get(classify.norm(r.name or ""))
        if acc is None:
            parsed.issue("warning", "OPENING_UNMATCHED", f"Opening balance '{r.name or r.code}' does not match any balance-sheet account.",
                         r.sheet, r.row_no, r.name)
            continue
        if r.year is None or r.value is None:
            continue
        db.add(AccountValue(account_id=acc.id, upload_id=up.id, raw_item_id=raw.id, year=r.year, kind="opening", value=r.value))
    for r in parsed.rows["additional"]:
        raw = RawItem(upload_id=up.id, sheet=r.sheet, row_no=r.row_no, account_name=r.name, year_raw=r.year_raw,
                      value_raw=r.value_raw, notes=r.notes)
        db.add(raw)
        db.flush()
        if r.name:
            db.add(AdditionalValue(upload_id=up.id, raw_item_id=raw.id, key=r.name.strip(), year=r.year, value=r.value,
                                   text=r.value_raw if r.value is None else r.notes))

    # classifications for new accounts (existing decisions are carried over and flagged)
    all_accs = list(existing.values())
    sugg = []
    for a in all_accs:
        if a.classification is None:
            s = classify.suggest(a.name, a.statement, a.class_hint, a.section, a.description)
            sugg.append({"name": a.name, "statement": a.statement, "suggestion": s, "acc": a})
    classify.post_pass(sugg + [{"name": a.name, "statement": a.statement,
                                "suggestion": classify.Suggestion(effective_category(a.classification), 1, "")}
                               for a in all_accs if a.classification is not None])
    for item in sugg:
        s, a = item["suggestion"], item["acc"]
        db.add(Classification(account_id=a.id, suggested_category=s.category, confidence=s.confidence, reason=s.reason,
                              question=s.question, options=s.options, hint_conflict=s.hint_conflict, status="pending"))
    for a in all_accs:
        if a.classification is not None and a not in new_accounts and a.classification.status != "pending":
            a.classification.carried_over = True

    for i in parsed.issues:
        db.add(ValidationIssue(upload_id=up.id, **i))
    db.flush()
    up.summary = {"years": parsed.years, "rows": {k: len(v) for k, v in parsed.rows.items()},
                  "new_accounts": len(new_accounts), "issues": _count(parsed.issues)}
    audit(db, user_id, company.id, "upload", up.id, "upload", after={"version": version, "filename": filename, "sha256": up.sha256},
          detail=f"{len(new_accounts)} new accounts; years {parsed.years}")
    refresh_assumptions(db, company, user_id)
    return up


def _count(issues):
    c = defaultdict(int)
    for i in issues:
        c[i["severity"]] += 1
    return dict(c)


# ------------------------------------------------------------------------------------------- assumptions
def data_facts(db: Session, company: Company) -> dict:
    up = active_upload(db, company.id)
    if up is None:
        return {}
    accs, years, add = load_inputs(db, company, up)
    first = years[0] if years else None
    missing_open = []
    for label, cats in (("inventory", ["bs.ca.inventory"]), ("receivables", ["bs.ca.receivables", "bs.ca.notes_receivable"]),
                        ("payables", ["bs.cl.payables"]), ("total assets / equity", None)):
        rel = [a for a in accs if (cats is None and a.statement == "BS" and not taxonomy.get(a.category).subtotal) or (cats and a.category in cats)]
        if rel and any(a.opening.get(first) is None for a in rel):
            missing_open.append(label)
    cats = {a.category for a in accs}
    return {"has_credit_sales": "credit_sales" in add, "has_cash_sales": "cash_sales" in add,
            "has_credit_purchases": "credit_purchases" in add, "has_finance_income": "is.finance_income" in cats,
            "missing_opening": missing_open, "first_year": first, "years": years}


def refresh_assumptions(db: Session, company: Company, user_id=None):
    facts = data_facts(db, company)
    props = asm.detect(company.methodology, facts)
    cur = {a.key: a for a in db.scalars(select(Assumption).where(Assumption.company_id == company.id))}
    for p in props:
        a = cur.get(p["key"])
        if a is None:
            db.add(Assumption(company_id=company.id, key=p["key"], proposed_value=p["proposed_value"], value=p["proposed_value"],
                              reason=p["reason"], supporting_data=p["supporting_data"], status="pending"))
        else:
            a.supporting_data = p["supporting_data"]
            if a.status == "pending":
                a.proposed_value = a.value = p["proposed_value"]
                a.reason = p["reason"]
    db.flush()


# ------------------------------------------------------------------------------------------- analysis
def load_inputs(db: Session, company: Company, up: Upload):
    rows = db.execute(select(Account, Classification, AccountValue).join(Classification, Classification.account_id == Account.id)
                      .join(AccountValue, AccountValue.account_id == Account.id)
                      .where(AccountValue.upload_id == up.id)).all()
    accs: dict[int, AccountInput] = {}
    for acc, cls, val in rows:
        ai = accs.get(acc.id)
        if ai is None:
            status = cls.status
            ai = AccountInput(acc.id, acc.name, acc.statement, effective_category(cls), status, {}, {}, acc.code)
            ai._order = acc.sort_order  # type: ignore[attr-defined]
            accs[acc.id] = ai
        if val.kind == "opening":
            ai.opening[val.year] = Decimal(str(val.value))
        else:
            ai.values[val.year] = Decimal(str(val.value))
    lst = sorted(accs.values(), key=lambda a: a._order)  # type: ignore[attr-defined]
    years = sorted({y for a in lst for y in a.values})
    add: dict[str, dict] = defaultdict(dict)
    for av in db.scalars(select(AdditionalValue).where(AdditionalValue.upload_id == up.id)):
        if av.value is not None and av.year is not None:
            add[av.key][av.year] = Decimal(str(av.value))
    return lst, years, dict(add)


def benchmarks_for(db: Session, company: Company) -> dict:
    out = {}
    for b in db.scalars(select(Benchmark).where(Benchmark.industry == company.industry)):
        out[b.ratio_key] = {"value": b.value, "source": b.source}
    for b in db.scalars(select(Benchmark).where(Benchmark.industry == f"company:{company.id}")):
        out[b.ratio_key] = {"value": b.value, "source": b.source}  # company-specific overrides industry
    return out


def build_analysis(db: Session, company: Company, years: list[int] | None = None,
                   methodology: str | None = None) -> Analysis | None:
    up = active_upload(db, company.id)
    if up is None:
        return None
    accs, all_years, add = load_inputs(db, company, up)
    assumptions = {a.key: a.value for a in db.scalars(select(Assumption).where(Assumption.company_id == company.id))}
    status = {a.key: a.status for a in db.scalars(select(Assumption).where(Assumption.company_id == company.id))}
    base = asm.defaults(company.methodology)
    base.update(assumptions)
    blocking = defaultdict(list)
    for i in db.scalars(select(ValidationIssue).where(ValidationIssue.upload_id == up.id, ValidationIssue.severity == "error",
                                                      ValidationIssue.acknowledged.is_(False))):
        for y in ([i.year] if i.year else all_years):
            blocking[y].append(f"Unresolved data error: {i.message}")
    ys = [y for y in all_years if not years or y in years]
    return Analysis(accs, ys, add, base, status, benchmarks_for(db, company), methodology or company.methodology,
                    company.currency or "", dict(blocking))


def pending_questions(db: Session, company: Company) -> list[dict]:
    out = []
    for acc, cls in db.execute(select(Account, Classification).join(Classification).where(Account.company_id == company.id)):
        if cls.status in ("pending", "info_requested") and cls.question:
            out.append({"account_id": acc.id, "account": acc.name, "question": cls.question, "reason": cls.reason,
                        "suggested": cls.suggested_category, "confidence": cls.confidence})
    return out


def governance(db: Session, company: Company) -> dict:
    up = active_upload(db, company.id)
    if up is None:
        return {"has_data": False}
    cls = db.execute(select(Classification.status, func.count()).join(Account).where(Account.company_id == company.id)
                     .group_by(Classification.status)).all()
    cmap = dict(cls)
    ass = db.execute(select(Assumption.status, func.count()).where(Assumption.company_id == company.id).group_by(Assumption.status)).all()
    amap = dict(ass)
    issues = db.execute(select(ValidationIssue.severity, func.count()).where(ValidationIssue.upload_id == up.id,
                                                                             ValidationIssue.acknowledged.is_(False))
                        .group_by(ValidationIssue.severity)).all()
    imap = dict(issues)
    total_cls = sum(cmap.values())
    decided = cmap.get("approved", 0) + cmap.get("modified", 0) + cmap.get("rejected", 0)
    crit_pending = 0
    for acc, c in db.execute(select(Account, Classification).join(Classification).where(Account.company_id == company.id)):
        if c.status in ("pending", "info_requested") and not taxonomy.get(effective_category(c)).subtotal:
            crit_pending += 1
    relevant_keys = {d["key"] for d in asm.detect(company.methodology, data_facts(db, company)) if d["relevant"]}
    pend_ass = [a.key for a in db.scalars(select(Assumption).where(Assumption.company_id == company.id, Assumption.status == "pending"))
                if a.key in relevant_keys]
    return {"has_data": True, "version": up.version, "uploaded_at": up.uploaded_at.isoformat(), "filename": up.filename,
            "years": up.summary.get("years", []), "classifications": cmap, "classification_total": total_cls,
            "classification_decided": decided, "classification_progress": (decided / total_cls) if total_cls else 0,
            "critical_pending_classifications": crit_pending, "assumptions": amap, "pending_assumptions": pend_ass,
            "issues": imap, "ready_for_approval": crit_pending == 0 and not pend_ass and imap.get("error", 0) == 0}
