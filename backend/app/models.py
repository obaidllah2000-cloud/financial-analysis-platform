"""Relational model. Three data layers are kept strictly apart:

  ORIGINAL   raw_items          — exactly what was in the uploaded Excel (immutable, per upload/version)
  NORMALIZED account_values     — parsed numeric value per account/year linked to its raw item
  APPROVED   classifications    — analyst decision (suggested vs approved category kept side by side)

Results are recomputed deterministically from these layers; approved analysis snapshots are stored.
Works on SQLite (default) or PostgreSQL via DATABASE_URL.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (JSON, Boolean, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20), default="analyst")  # admin | analyst | reviewer | viewer


class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    industry: Mapped[str] = mapped_column(Text, default="Other")
    country: Mapped[str | None] = mapped_column(Text, nullable=True)
    currency: Mapped[str | None] = mapped_column(Text, nullable=True)
    fy_end: Mapped[str | None] = mapped_column(Text, nullable=True)
    reporting_type: Mapped[str | None] = mapped_column(Text, nullable=True)  # Standalone | Consolidated
    basis: Mapped[str | None] = mapped_column(Text, nullable=True)
    standards: Mapped[str | None] = mapped_column(Text, nullable=True)
    methodology: Mapped[str] = mapped_column(String(20), default="academic")  # academic | professional
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    uploads: Mapped[list["Upload"]] = relationship(back_populates="company", cascade="all, delete-orphan")


class Upload(Base):
    """One uploaded Excel file = one data version."""
    __tablename__ = "uploads"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    version: Mapped[int] = mapped_column(Integer)
    filename: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    company_info: Mapped[dict] = mapped_column(JSON, default=dict)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    company: Mapped[Company] = relationship(back_populates="uploads")


class RawItem(Base):
    """ORIGINAL layer: one cell-row from the Excel file, stored verbatim."""
    __tablename__ = "raw_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    upload_id: Mapped[int] = mapped_column(ForeignKey("uploads.id"), index=True)
    sheet: Mapped[str] = mapped_column(Text)
    row_no: Mapped[int] = mapped_column(Integer)
    account_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    account_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    section: Mapped[str | None] = mapped_column(Text, nullable=True)
    year_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    class_hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    currency: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (UniqueConstraint("company_id", "statement", "name_key"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    statement: Mapped[str] = mapped_column(String(4))  # BS | IS | CF
    code: Mapped[str | None] = mapped_column(Text, nullable=True)
    name: Mapped[str] = mapped_column(Text)
    name_key: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    section: Mapped[str | None] = mapped_column(Text, nullable=True)
    class_hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    classification: Mapped["Classification"] = relationship(back_populates="account", uselist=False, cascade="all, delete-orphan")


class AccountValue(Base):
    """NORMALIZED layer: parsed value for an account/year in one upload, linked to its raw item."""
    __tablename__ = "account_values"
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    upload_id: Mapped[int] = mapped_column(ForeignKey("uploads.id"), index=True)
    raw_item_id: Mapped[int] = mapped_column(ForeignKey("raw_items.id"))
    year: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(10), default="closing")  # closing | opening
    value: Mapped[float] = mapped_column(Numeric(24, 6))


class AdditionalValue(Base):
    __tablename__ = "additional_values"
    id: Mapped[int] = mapped_column(primary_key=True)
    upload_id: Mapped[int] = mapped_column(ForeignKey("uploads.id"), index=True)
    raw_item_id: Mapped[int] = mapped_column(ForeignKey("raw_items.id"))
    key: Mapped[str] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    value: Mapped[float | None] = mapped_column(Numeric(24, 6), nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)


class Classification(Base):
    """APPROVED layer: suggested and approved classification kept side by side."""
    __tablename__ = "classifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), unique=True)
    suggested_category: Mapped[str] = mapped_column(String(60))
    confidence: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(Text)
    question: Mapped[str | None] = mapped_column(Text, nullable=True)
    options: Mapped[list] = mapped_column(JSON, default=list)
    hint_conflict: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|approved|modified|rejected|info_requested
    approved_category: Mapped[str | None] = mapped_column(String(60), nullable=True)
    analyst_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    carried_over: Mapped[bool] = mapped_column(Boolean, default=False)
    account: Mapped[Account] = relationship(back_populates="classification")


class ValidationIssue(Base):
    __tablename__ = "validation_issues"
    id: Mapped[int] = mapped_column(primary_key=True)
    upload_id: Mapped[int] = mapped_column(ForeignKey("uploads.id"), index=True)
    severity: Mapped[str] = mapped_column(String(10))  # error | warning | info
    code: Mapped[str] = mapped_column(String(40))
    message: Mapped[str] = mapped_column(Text)
    sheet: Mapped[str | None] = mapped_column(Text, nullable=True)
    row_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    account: Mapped[str | None] = mapped_column(Text, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class Assumption(Base):
    __tablename__ = "assumptions"
    __table_args__ = (UniqueConstraint("company_id", "key"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    key: Mapped[str] = mapped_column(String(60))
    proposed_value: Mapped[str] = mapped_column(String(60))
    value: Mapped[str] = mapped_column(String(60))
    reason: Mapped[str] = mapped_column(Text)
    supporting_data: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|accepted|modified|rejected
    analyst_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Benchmark(Base):
    __tablename__ = "benchmarks"
    id: Mapped[int] = mapped_column(primary_key=True)
    industry: Mapped[str] = mapped_column(Text, index=True)  # industry name, or 'company:<id>' for company-specific
    ratio_key: Mapped[str] = mapped_column(String(60))
    value: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(Text, default="User entered")


class Observation(Base):
    __tablename__ = "observations"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    upload_id: Mapped[int] = mapped_column(ForeignKey("uploads.id"))
    level: Mapped[int] = mapped_column(Integer)
    obs_type: Mapped[str] = mapped_column(String(40))
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="open")  # open | investigating | resolved | dismissed
    analyst_note: Mapped[str | None] = mapped_column(Text, nullable=True)


class AnalysisSnapshot(Base):
    """Approved analysis: frozen results, linked to the data version and assumption set used."""
    __tablename__ = "analysis_snapshots"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    upload_id: Mapped[int] = mapped_column(ForeignKey("uploads.id"))
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    status: Mapped[str] = mapped_column(String(20))  # approved | approved_with_limitations
    results: Mapped[dict] = mapped_column(JSON)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True)
    entity: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(60))
    before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
