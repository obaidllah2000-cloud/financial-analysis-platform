import { useEffect, useMemo, useState } from "react";
import { api, fmtNum } from "./api";
import { useLang, useT } from "./i18n";
import { Comparison, Ratios, SourcesUses, Statements } from "./Analysis";
import { AIAnalyst, Audit, Evaluation } from "./Insight";
import Forecasting from "./Forecasting";
import { Chip } from "./ui";

const TABS = ["Overview", "Upload & Data Review", "Classification", "Assumptions", "Statements", "Ratios", "Year comparison",
  "Sources & Uses", "Forecasting & Planning", "AI Analyst", "Evaluation & Reports", "Audit trail"];

export default function Workspace({ id, meta, onChange }: { id: number; meta: any; onChange: () => void }) {
  const t = useT();
  const [tab, setTab] = useState("Overview");
  const [co, setCo] = useState<any>(null);
  const [rev, setRev] = useState(0);
  const bump = () => { setRev((r) => r + 1); onChange(); };
  useEffect(() => { api.get(`/api/companies/${id}`).then(setCo); }, [id, rev]);
  if (!co) return <p>Loading…</p>;
  const g = co.governance;
  const needsData = !g.has_data && !["Overview", "Upload & Data Review", "Audit trail"].includes(tab);
  return (
    <>
      <div className="topbar">
        <h1>{co.name}</h1>
        <span className="chip c-needs_info">{co.industry}</span><span className="chip c-needs_info">{co.currency || "currency ?"}</span>
        <span className="chip c-approved_assumption">{co.methodology} methodology</span>
        {g.has_data && <Chip s={g.ready_for_approval ? "verified" : "provisional"} label={g.ready_for_approval ? "reviews complete" : "review in progress"} />}
      </div>
      <div className="tabs">{TABS.map((x) => <button key={x} className={`tab ${tab === x ? "on" : ""}`} onClick={() => setTab(x)}>{t(x)}</button>)}</div>
      {needsData ? <div className="warnbox">Upload financial statements first (Upload & Data Review tab).</div> : <>
        {tab === "Overview" && <Overview co={co} go={setTab} bump={bump} />}
        {tab === "Upload & Data Review" && <UploadReview co={co} bump={bump} />}
        {tab === "Classification" && <ClassificationReview co={co} meta={meta} bump={bump} />}
        {tab === "Assumptions" && <AssumptionsReview co={co} bump={bump} />}
        {tab === "Statements" && <Statements co={co} />}
        {tab === "Ratios" && <Ratios co={co} />}
        {tab === "Year comparison" && <Comparison co={co} />}
        {tab === "Sources & Uses" && <SourcesUses co={co} />}
        {tab === "Forecasting & Planning" && <Forecasting co={co} />}
        {tab === "AI Analyst" && <AIAnalyst co={co} meta={meta} go={setTab} />}
        {tab === "Evaluation & Reports" && <Evaluation co={co} meta={meta} bump={bump} />}
        {tab === "Audit trail" && <Audit co={co} rev={rev} />}
      </>}
    </>
  );
}

function Overview({ co, go, bump }: any) {
  const g = co.governance;
  const [m, setM] = useState(co.methodology);
  if (!g.has_data) return <div className="panel"><h2>No data yet</h2><p>Download the Excel template, enter the statements for each year, then upload it.</p>
    <div className="row"><a className="btn" href="/api/template">Download template</a><a className="btn" href="/api/template?sample=true">Download 5-year sample</a>
      <button className="btn pri" onClick={() => go("Upload & Data Review")}>Go to upload</button></div></div>;
  const cls = g.classifications || {};
  const steps = [
    { l: "Data validation", ok: !g.issues?.error, d: `${g.issues?.error || 0} errors · ${g.issues?.warning || 0} warnings`, tab: "Upload & Data Review" },
    { l: "Classification approval", ok: g.critical_pending_classifications === 0, d: `${g.classification_decided}/${g.classification_total} decided`, tab: "Classification", p: g.classification_progress },
    { l: "Assumptions confirmed", ok: !g.pending_assumptions.length, d: `${g.pending_assumptions.length} pending`, tab: "Assumptions" },
    { l: "Analysis approval", ok: g.ready_for_approval, d: g.ready_for_approval ? "ready to approve" : "blocked by pending reviews", tab: "Evaluation & Reports" },
  ];
  return (
    <>
      <div className="grid g4">
        <div className="kpi"><div className="l">Reporting period</div><div className="v">{g.years[0]}–{g.years[g.years.length - 1]}</div><div className="s">{g.years.length} financial years · data v{g.version}</div></div>
        <div className="kpi"><div className="l">Classification approval</div><div className="v">{Math.round(g.classification_progress * 100)}%</div>
          <div className="s">{cls.approved || 0} approved · {cls.modified || 0} modified · {cls.rejected || 0} rejected · {(cls.pending || 0) + (cls.info_requested || 0)} pending</div>
          <div className="bar"><i style={{ width: `${g.classification_progress * 100}%` }} /></div></div>
        <div className="kpi"><div className="l">Pending assumptions</div><div className="v">{g.pending_assumptions.length}</div><div className="s">{g.pending_assumptions.slice(0, 3).join(", ")}{g.pending_assumptions.length > 3 ? "…" : ""}</div></div>
        <div className="kpi"><div className="l">Data validation</div><div className="v">{g.issues?.error ? <span className="neg">{g.issues.error} errors</span> : "No errors"}</div><div className="s">{g.issues?.warning || 0} open warnings · {g.issues?.info || 0} info</div></div>
      </div>
      <div className="panel" style={{ marginTop: 16 }}>
        <h2>Review workflow — Upload → Review → Confirm → Analyze → Interpret → Report</h2>
        <table><tbody>{steps.map((s) => (
          <tr key={s.l} className="click" onClick={() => go(s.tab)}><td style={{ width: 30 }}>{s.ok ? "✅" : "⏳"}</td><td><b>{s.l}</b></td><td className="muted">{s.d}</td><td><Chip s={s.ok ? "verified" : "provisional"} label={s.ok ? "done" : "action needed"} /></td></tr>))}</tbody></table>
      </div>
      <div className="panel">
        <h2>Company profile</h2>
        <dl className="kv">{["industry", "country", "currency", "fy_end", "reporting_type", "basis", "standards"].map((k) => <><dt key={k}>{k.replace("_", " ")}</dt><dd key={k + "v"}>{co[k] || "—"}</dd></>)}
          <dt>Source file</dt><dd>{g.filename} (uploaded {new Date(g.uploaded_at).toLocaleString()})</dd>
          <dt>Methodology</dt><dd><div className="row">
            <select value={m} onChange={(e) => setM(e.target.value)}><option value="academic">Academic (lectures & solved exams)</option><option value="professional">Professional</option></select>
            <button className="btn sm" disabled={m === co.methodology} onClick={async () => { await api.patch(`/api/companies/${co.id}`, { methodology: m }); bump(); }}>Apply</button>
            <span className="small muted">Changing methodology re-proposes pending assumptions; approved decisions are kept.</span></div></dd></dl>
      </div>
    </>
  );
}

function UploadReview({ co, bump }: any) {
  const [data, setData] = useState<any>(null);
  const [versions, setVersions] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<any>(null);
  const [filter, setFilter] = useState("all");
  const [q, setQ] = useState("");
  const load = () => { api.get(`/api/companies/${co.id}/review`).then(setData); api.get(`/api/companies/${co.id}/uploads`).then(setVersions); };
  useEffect(load, [co.id]);
  const upload = async (f: File) => {
    setBusy(true); setMsg(null);
    try { const r = await api.upload(`/api/companies/${co.id}/upload`, f); setMsg({ ok: true, t: `Uploaded as version ${r.version}: years ${r.summary.years.join(", ")}, ${r.summary.new_accounts} new accounts, issues ${JSON.stringify(r.summary.issues)}` }); load(); bump(); }
    catch (e: any) { setMsg({ ok: false, t: e.message }); } finally { setBusy(false); }
  };
  const rows = (data?.rows || []).filter((r: any) => (filter === "all" || r.validation === filter || r.decision === filter) &&
    (!q || `${r.account} ${r.code}`.toLowerCase().includes(q.toLowerCase())));
  return (
    <>
      <div className="panel">
        <h2>Upload Excel</h2>
        <div className="row"><input type="file" accept=".xlsx,.xlsm" disabled={busy} onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])} />
          <a className="btn sm" href="/api/template">Template</a><a className="btn sm" href="/api/template?sample=true">5-year sample</a>
          {busy && <span className="muted">Processing…</span>}</div>
        {msg && <div className={msg.ok ? "okbox" : "badbox"} style={{ marginTop: 10 }}>{msg.t}</div>}
        <p className="small muted">Re-uploading a revised file creates a new version. Original values are stored verbatim and are never modified; analyst decisions carry over to accounts with the same name.</p>
        {versions.length > 0 && <><h3>Data versions</h3><table><thead><tr><th>Version</th><th>File</th><th>Uploaded</th><th>Years</th><th>SHA-256</th><th /></tr></thead>
          <tbody>{versions.map((v) => <tr key={v.id}><td>v{v.version} {v.active && <Chip s="verified" label="active" />}</td><td>{v.filename}</td><td>{new Date(v.uploaded_at).toLocaleString()}</td>
            <td>{v.summary?.years?.join(", ")}</td><td className="mono small">{v.sha256.slice(0, 12)}…</td>
            <td>{!v.active && <button className="btn sm" onClick={async () => { await api.post(`/api/uploads/${v.id}/activate`); load(); bump(); }}>Activate</button>}</td></tr>)}</tbody></table></>}
      </div>
      {data && <>
        <div className="panel">
          <h2>Validation issues ({data.issues.length})</h2>
          {data.issues.length === 0 && <p className="muted">No issues.</p>}
          <div className="scroll" style={{ maxHeight: 300 }}><table><thead><tr><th>Severity</th><th>Code</th><th>Message</th><th>Location</th><th /></tr></thead>
            <tbody>{data.issues.map((i: any) => <tr key={i.id} style={{ opacity: i.acknowledged ? 0.5 : 1 }}><td><Chip s={i.severity} /></td><td className="mono small">{i.code}</td><td>{i.message}</td>
              <td className="small">{i.sheet}{i.row_no ? ` row ${i.row_no}` : ""}</td>
              <td>{i.severity !== "error" && !i.acknowledged && <button className="btn sm" onClick={async () => { await api.post(`/api/issues/${i.id}/acknowledge`); load(); bump(); }}>Acknowledge</button>}
                {i.acknowledged && <span className="small muted">acknowledged</span>}</td></tr>)}</tbody></table></div>
          {data.checks.length > 0 && <><h3>Reconciliation checks (depend on current classifications)</h3>
            {data.checks.map((c: any, i: number) => <div key={i} className={c.severity === "error" ? "badbox" : c.severity === "warning" ? "warnbox" : "note"}>{c.message}</div>)}</>}
        </div>
        <div className="panel">
          <h2>Data Review Center — extracted items (v{data.version})</h2>
          <div className="row" style={{ marginBottom: 8 }}>
            <input type="text" placeholder="Search account…" value={q} onChange={(e) => setQ(e.target.value)} />
            <select value={filter} onChange={(e) => setFilter(e.target.value)}>{["all", "valid", "warning", "error", "info", "pending", "approved", "modified", "rejected"].map((x) => <option key={x}>{x}</option>)}</select>
            <span className="small muted">{rows.length} rows</span></div>
          <div className="scroll"><table>
            <thead><tr><th>Sheet / row</th><th>Original account</th><th className="n">Original value</th><th>Year</th><th>Suggested category</th><th>Group</th><th className="n">Confidence</th><th>Validation</th><th>Analyst decision</th></tr></thead>
            <tbody>{rows.map((r: any) => (
              <tr key={r.raw_id}><td className="small muted">{r.sheet} {r.row_no}</td><td>{r.account}{r.messages.length > 0 && <div className="small neg">{r.messages.join("; ")}</div>}</td>
                <td className="n">{r.value}</td><td>{r.year}{r.kind === "opening" && <span className="small muted"> (opening)</span>}</td>
                <td className="small">{r.category_label || "—"}</td><td className="small">{r.group || "—"}</td>
                <td className="n">{r.confidence != null ? `${Math.round(r.confidence * 100)}%` : "—"}</td>
                <td><Chip s={r.validation} /></td><td>{r.decision ? <Chip s={r.decision} /> : "—"}</td></tr>))}</tbody></table></div>
        </div>
      </>}
    </>
  );
}

function ClassificationReview({ co, meta, bump }: any) {
  const t = useT();
  const lang = useLang();
  const [rows, setRows] = useState<any[]>([]);
  const [filter, setFilter] = useState("pending");
  const [st, setSt] = useState("all");
  const [impact, setImpact] = useState<any>(null);
  const [err, setErr] = useState("");
  const load = () => api.get(`/api/companies/${co.id}/classifications`).then(setRows);
  useEffect(() => { load(); }, [co.id]);
  const cats = useMemo(() => (meta?.categories || []), [meta]);
  const decide = async (r: any, action: string, category?: string, apply_similar = false) => {
    setErr("");
    const note = action === "reject" || action === "request_info" ? window.prompt("Note / reason (logged in the audit trail):") || undefined : undefined;
    try { const res = await api.post(`/api/classifications/${r.account_id}/decide`, { action, category, note, apply_similar }); setImpact({ account: r.account, action, ...res }); await load(); bump(); }
    catch (e: any) { setErr(e.message); }
  };
  const view = rows.filter((r) => (filter === "all" || (filter === "pending" ? ["pending", "info_requested"].includes(r.status) : filter === "questions" ? r.needs_more_info : r.status === filter)) && (st === "all" || r.statement === st));
  const counts = rows.reduce((a: any, r) => ({ ...a, [r.status]: (a[r.status] || 0) + 1 }), {});
  return (
    <>
      <div className="note">The engine suggests a category with its reasoning and confidence. Only approved/modified classifications are final; pending ones are used provisionally and every dependent result is labelled “provisional”. Rejected accounts are excluded from all calculations.</div>
      {err && <div className="badbox">{err}</div>}
      {impact && <div className="okbox"><b>{impact.account}</b>: {impact.action} recorded{impact.changed.length > 1 ? ` (and applied to ${impact.changed.length - 1} similar accounts)` : ""}. {impact.impact.length ? `Recalculated dependent indicators (${impact.year}): ` + impact.impact.map((i: any) => `${i.ratio} ${i.before} → ${i.after}`).join(" · ") : "No dependent indicator changed."}</div>}
      <div className="panel">
        <div className="row" style={{ marginBottom: 10 }}>
          {[["pending", `Pending (${(counts.pending || 0) + (counts.info_requested || 0)})`], ["questions", "Needs answer"], ["approved", `Approved (${counts.approved || 0})`], ["modified", `Modified (${counts.modified || 0})`], ["rejected", `Rejected (${counts.rejected || 0})`], ["all", `All (${rows.length})`]].map(([k, l]) =>
            <button key={k} className={`btn sm ${filter === k ? "pri" : ""}`} onClick={() => setFilter(k)}>{l}</button>)}
          <select value={st} onChange={(e) => setSt(e.target.value)}><option value="all">All statements</option><option value="BS">Balance sheet</option><option value="IS">Income statement</option><option value="CF">Cash flow</option></select>
          <button className="btn sm" onClick={async () => { for (const r of view.filter((x) => x.status === "pending" && x.confidence >= 0.85 && !x.question)) await api.post(`/api/classifications/${r.account_id}/decide`, { action: "approve" }); load(); bump(); }}>
            Approve all high-confidence (≥85%, no open question) in view</button>
        </div>
        {view.length === 0 && <p className="muted">Nothing in this view.</p>}
        {view.map((r) => (
          <div key={r.account_id} className="card">
            <div className="row" style={{ justifyContent: "space-between" }}>
              <div><b>{r.account}</b> <span className="small muted">{r.code} · {r.statement}{r.hint ? ` · Excel hint: ${r.hint}` : ""}</span></div>
              <div className="row"><Chip s={r.status} />{r.carried_over && <span className="chip c-info">carried over from previous version</span>}</div>
            </div>
            <dl className="kv">
              <dt>Suggestion</dt><dd><b>{lang === "ar" ? r.suggested_label_ar : r.suggested_label}</b> · {r.suggested_element} · {r.suggested_group} · confidence <b>{Math.round(r.confidence * 100)}%</b></dd>
              <dt>{t("Why")}</dt><dd>{r.reason}</dd>
              {r.status !== "pending" && <><dt>Approved classification</dt><dd>{lang === "ar" ? r.effective_label_ar : r.effective_label}{r.analyst_note && <span className="muted"> — “{r.analyst_note}”</span>}</dd></>}
              <dt>Used in</dt><dd className="small">{r.subtotal ? "Reconciliation only (subtotal — never added to aggregates)" : r.used_in_ratios.length ? r.used_in_ratios.join(", ") : "No ratio directly"}</dd>
            </dl>
            {r.question && ["pending", "info_requested"].includes(r.status) && (
              <div className="warnbox"><b>{t("Question")}:</b> {r.question}
                <div className="row" style={{ marginTop: 6 }}>{r.options.map((o: any) => <button key={o.category} className="btn sm" onClick={() => decide(r, o.category === r.suggested_category ? "approve" : "modify", o.category)}>{o.label}</button>)}</div></div>)}
            <div className="row">
              {r.status !== "approved" && <button className="btn sm pri" onClick={() => decide(r, "approve")}>{t("Approve")}</button>}
              <select defaultValue="" onChange={(e) => e.target.value && decide(r, "modify", e.target.value)}>
                <option value="">{t("Modify")}…</option>
                {cats.filter((c: any) => c.statement === r.statement || c.key === "unclassified").map((c: any) => <option key={c.key} value={c.key}>{lang === "ar" ? c.label_ar : c.label_en}</option>)}
              </select>
              {r.status !== "rejected" && <button className="btn sm" onClick={() => decide(r, "reject")}>{t("Reject")}</button>}
              {r.status === "pending" && <button className="btn sm" onClick={() => decide(r, "request_info")}>{t("Request info")}</button>}
              {r.status === "pending" && <button className="btn sm" onClick={() => decide(r, "approve", undefined, true)}>{t("Approve")} + {t("Apply to similar")}</button>}
              {r.status !== "pending" && <button className="btn sm" onClick={() => decide(r, "reopen")}>{t("Reopen")}</button>}
            </div>
          </div>))}
      </div>
    </>
  );
}

function AssumptionsReview({ co, bump }: any) {
  const lang = useLang();
  const [rows, setRows] = useState<any[]>([]);
  const [showAll, setShowAll] = useState(false);
  const load = () => api.get(`/api/companies/${co.id}/assumptions`).then(setRows);
  useEffect(() => { load(); }, [co.id]);
  const act = async (a: any, action: string, value?: string) => {
    const note = action === "reject" ? window.prompt("Reason for rejecting (dependent ratios will show 'requires information'):") || undefined : undefined;
    await api.post(`/api/companies/${co.id}/assumptions/${a.key}`, { action, value, note }); load(); bump();
  };
  const view = rows.filter((r) => showAll || r.relevant);
  return (
    <>
      <div className="note">Every assumption is explicit: proposed value, reason, supporting data, alternatives, and the numerical impact of each alternative on the latest year. Results that use an unconfirmed assumption are labelled provisional.</div>
      <label className="row small" style={{ marginBottom: 10 }}><input type="checkbox" checked={showAll} onChange={(e) => setShowAll(e.target.checked)} />Show assumptions not relevant to this data set</label>
      {view.map((a) => (
        <div key={a.key} className="card">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div><b>{lang === "ar" ? a.name_ar : a.name}</b> {a.critical && <span className="chip c-needs_info">critical</span>} {!a.relevant && <span className="chip c-needs_info">not needed for this data</span>}</div>
            <div className="row"><Chip s={a.status} /></div></div>
          <dl className="kv">
            <dt>Proposed value</dt><dd>{a.options.find((o: any) => o.value === a.proposed_value)?.label}</dd>
            {a.value !== a.proposed_value && <><dt>Current value</dt><dd><b>{a.options.find((o: any) => o.value === a.value)?.label}</b></dd></>}
            <dt>Reason</dt><dd>{a.reason}</dd><dt>Supporting data</dt><dd>{a.supporting_data}</dd>
            {a.analyst_note && <><dt>Analyst note</dt><dd>{a.analyst_note}</dd></>}
            {a.decided_at && <><dt>Decided</dt><dd>{new Date(a.decided_at).toLocaleString()}</dd></>}
          </dl>
          <table><thead><tr><th>Alternative</th><th>Effect</th><th>Impact on {a.impact[0]?.year}</th><th /></tr></thead>
            <tbody>{a.options.map((o: any) => { const imp = a.impact.find((i: any) => i.option === o.value); return (
              <tr key={o.value} style={{ background: o.value === a.value ? "var(--info-bg)" : undefined }}><td><b>{o.label}</b></td><td className="small">{o.impact}</td>
                <td className="small mono">{imp?.ratios.slice(0, 6).map((r: any) => `${r.name}: ${r.display}`).join(" · ") || "—"}</td>
                <td>{(a.status === "pending" || o.value !== a.value) && <button className="btn sm" onClick={() => act(a, "modify", o.value)}>Use this</button>}</td></tr>); })}</tbody></table>
          <div className="row" style={{ marginTop: 8 }}>
            {a.status === "pending" && <button className="btn sm pri" onClick={() => act(a, "accept")}>Accept proposed</button>}
            {a.status !== "rejected" && <button className="btn sm" onClick={() => act(a, "reject")}>Reject</button>}
            {a.status !== "pending" && <button className="btn sm" onClick={() => act(a, "reopen")}>Reopen</button>}
            <span className="small muted">Affects: {a.dependent_ratios.join(", ")}</span>
          </div>
        </div>))}
      <div className="row"><span className="muted small">Values shown use {fmtNum(view.length)} assumptions.</span></div>
    </>
  );
}
