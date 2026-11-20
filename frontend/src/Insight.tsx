import { useEffect, useState } from "react";
import { api, getLang } from "./api";
import { useT } from "./i18n";
import { Chip } from "./ui";

const TYPE_STYLE: Record<string, string> = { math_error: "invalid", accounting_inconsistency: "error", unusual_trend: "provisional",
  potential_risk: "High", hypothesis: "approved_assumption" };

function ObsCard({ o, onAsk }: { o: any; onAsk?: (q: string) => void }) {
  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div className="t">{o.title}</div>
        <div className="row"><span className="chip c-needs_info">Level {o.level}</span><Chip s={TYPE_STYLE[o.type]} label={o.type_label} /><span className="chip c-needs_info">confidence: {o.confidence}</span></div>
      </div>
      <p style={{ margin: "4px 0 8px" }}>{o.finding}</p>
      <dl className="kv">
        <dt>Comparison period</dt><dd>{o.comparison_period}</dd>
        <dt>Supporting data</dt><dd className="mono small">{JSON.stringify(o.supporting_data)}</dd>
        <dt>Reasoning</dt><dd>{o.reasoning}</dd>
        <dt>Possible explanation</dt><dd><i>{o.possible_explanation}</i> <span className="small muted">(unverified)</span></dd>
        <dt>Financial impact</dt><dd>{o.financial_impact}</dd>
        <dt>Required action</dt><dd><b>{o.required_action}</b></dd>
      </dl>
      {o.question && onAsk && <button className="btn sm" onClick={() => onAsk(o.question)}>💬 {o.question}</button>}
    </div>
  );
}

export function AIAnalyst({ co, meta, go }: any) {
  const t = useT();
  const [obs, setObs] = useState<any[]>([]);
  const [lvl, setLvl] = useState(0);
  const [msgs, setMsgs] = useState<any[]>([]);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => { api.get(`/api/companies/${co.id}/observations`).then(setObs); }, [co.id]);
  const ask = async (question: string) => {
    if (!question.trim()) return;
    setMsgs((m) => [...m, { u: question }]); setQ(""); setBusy(true);
    try { const r = await api.post(`/api/companies/${co.id}/chat`, { question, lang: getLang() }); setMsgs((m) => [...m, { a: r }]); }
    catch (e: any) { setMsgs((m) => [...m, { a: { ok: false, reason: e.message } }]); } finally { setBusy(false); }
  };
  const view = obs.filter((o) => !lvl || o.level === lvl);
  const byType = obs.reduce((a: any, o) => ({ ...a, [o.type_label]: (a[o.type_label] || 0) + 1 }), {});
  return (
    <div className="grid g2" style={{ alignItems: "start" }}>
      <div>
        <div className="note">The analyst reviews the uploaded company's actual data at three levels. All numbers come from the deterministic engine; explanations are labelled as hypotheses until confirmed.</div>
        <div className="row" style={{ marginBottom: 10 }}>
          {[[0, `All (${obs.length})`], [1, "Level 1 — accounts"], [2, "Level 2 — relationships"], [3, "Level 3 — overall"]].map(([k, l]: any) =>
            <button key={k} className={`btn sm ${lvl === k ? "pri" : ""}`} onClick={() => setLvl(k)}>{l}</button>)}
        </div>
        <p className="small muted">{Object.entries(byType).map(([k, v]) => `${k}: ${v}`).join(" · ")}</p>
        {view.map((o) => <ObsCard key={o.key} o={o} onAsk={o.level === 1 && o.area === "classification" ? () => go("Classification") : ask} />)}
        {!view.length && <p className="muted">No observations at this level.</p>}
      </div>
      <div className="panel" style={{ position: "sticky", top: 12 }}>
        <h2>Ask the financial analyst</h2>
        <p className="small muted">{meta?.claude_available ? "Answers are written by Claude from the verified results only." : "Claude is not configured (set ANTHROPIC_API_KEY on the server). Answers fall back to the matching deterministic findings."}</p>
        <div className="chat" style={{ maxHeight: "55vh", overflow: "auto", marginBottom: 10 }}>
          {msgs.map((m, i) => m.u ? <div key={i} className="msg u">{m.u}</div> :
            <div key={i} className="msg a">{m.a.ok ? m.a.answer : <>{m.a.reason}{m.a.fallback?.map((o: any) => <div key={o.key} style={{ marginTop: 8 }}><b>{o.title}</b><div className="small">{o.finding}</div><div className="small muted">→ {o.required_action}</div></div>)}</>}</div>)}
          {busy && <div className="msg a muted">Thinking…</div>}
        </div>
        <div className="row"><input type="text" style={{ flex: 1 }} value={q} placeholder="e.g. Why did liquidity weaken in the last year?" onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && ask(q)} />
          <button className="btn pri" disabled={busy} onClick={() => ask(q)}>{t("Ask")}</button></div>
      </div>
    </div>
  );
}

export function Evaluation({ co, meta, bump }: any) {
  const t = useT();
  const [d, setD] = useState<any>(null);
  const [msg, setMsg] = useState<any>(null);
  const [mods, setMods] = useState<string[]>(meta?.modules || []);
  const [years, setYears] = useState<number[]>([]);
  const [rlang, setRlang] = useState<string>(getLang());
  const load = () => api.get(`/api/companies/${co.id}/evaluation`).then((x) => { setD(x); if (!years.length) setYears(x.years); });
  useEffect(() => { load(); }, [co.id]);
  if (!d) return <p>Loading…</p>;
  const ev = d.evaluation;
  const approve = async () => { setMsg(null); try { await api.post(`/api/companies/${co.id}/approve`); setMsg({ ok: true, t: "Analysis approved and frozen as a snapshot." }); load(); bump(); } catch (e: any) { setMsg({ ok: false, t: e.message }); } };
  const qs = `?years=${years.join(",")}&modules=${mods.join(",")}&lang=${rlang}`;
  return (
    <>
      <div className={d.approval_status === "approved" ? "okbox" : d.approval_status === "ready_for_approval" ? "note" : "warnbox"}>
        <b>{d.approval_status_text}</b>{d.approval_status !== "approved" && " — results below are not final until approved."}</div>
      <div className="panel">
        <h2>Approval & export</h2>
        <div className="row"><button className="btn pri" disabled={d.approval_status !== "ready_for_approval"} onClick={approve}>{t("Approve analysis")}</button>
          {d.approval_status === "provisional" && <span className="small muted">{`Blocked: ${d.governance.critical_pending_classifications} pending classifications, ${d.governance.pending_assumptions.length} pending assumptions, ${d.governance.issues?.error || 0} data errors.`}</span>}</div>
        {msg && <div className={msg.ok ? "okbox" : "badbox"} style={{ marginTop: 8 }}>{msg.t}</div>}
        <h3>Report content</h3>
        <div className="row small">Years: {d.years.map((y: number) => <label key={y} className="row" style={{ gap: 3 }}><input type="checkbox" checked={years.includes(y)} onChange={(e) => setYears(e.target.checked ? [...years, y].sort() : years.filter((x) => x !== y))} />{y}</label>)}</div>
        <div className="row small" style={{ marginTop: 6 }}>Modules: {(meta?.modules || []).map((m: string) => <label key={m} className="row" style={{ gap: 3 }}><input type="checkbox" checked={mods.includes(m)} onChange={(e) => setMods(e.target.checked ? [...mods, m] : mods.filter((x) => x !== m))} />{m.replace(/_/g, " ")}</label>)}</div>
        <div className="row small" style={{ marginTop: 6 }}><span>Report language</span>
          <label className="row" style={{ gap: 3 }}><input type="radio" checked={rlang === "ar"} onChange={() => setRlang("ar")} /><span data-no-translate>العربية</span></label>
          <label className="row" style={{ gap: 3 }}><input type="radio" checked={rlang === "en"} onChange={() => setRlang("en")} /><span data-no-translate>English</span></label></div>
        <p className="small muted">The report always reflects the current approved data, classifications and assumptions; it is regenerated on every download.</p>
        <div className="row" style={{ marginTop: 10 }}><a className="btn" href={`/api/companies/${co.id}/report.xlsx${qs}`}>{t("Export Excel")}</a><a className="btn" href={`/api/companies/${co.id}/report.pdf${qs}`}>{t("Export PDF")}</a></div>
      </div>
      <div className="panel">
        <h2>Final financial evaluation</h2>
        <table><thead><tr><th>Area</th><th>Rating</th><th>Key indicators (latest)</th></tr></thead>
          <tbody>{ev.areas.map((a: any) => <tr key={a.area}><td><b>{a.area}</b></td><td><Chip s={a.rating.split(" ")[0]} label={a.rating} />{a.provisional && <> <Chip s="provisional" /></>}</td><td className="small">{a.summary}</td></tr>)}</tbody></table>
      </div>
      <div className="grid g2">
        {[["Historical performance", ev.historical_performance], [t("Strengths"), ev.strengths], [t("Weaknesses"), ev.weaknesses], [t("Risks"), ev.risks], [t("Recommendations"), ev.recommendations], [t("Limitations"), d.limitations]].map(([h, list]: any) => (
          <div className="panel" key={h}><h2>{h}</h2>{list.length ? <ul style={{ margin: 0, paddingInlineStart: 18 }}>{list.map((x: string, i: number) => <li key={i} style={{ marginBottom: 4 }}>{x}</li>)}</ul> : <p className="muted">None identified.</p>}</div>))}
      </div>
    </>
  );
}

export function Audit({ co, rev }: any) {
  const [rows, setRows] = useState<any[]>([]);
  useEffect(() => { api.get(`/api/companies/${co.id}/audit`).then(setRows); }, [co.id, rev]);
  return (
    <div className="panel"><h2>Audit trail ({rows.length})</h2><div className="scroll"><table>
      <thead><tr><th>Time</th><th>User</th><th>Action</th><th>Entity</th><th>Before</th><th>After</th><th>Detail</th></tr></thead>
      <tbody>{rows.map((r) => <tr key={r.id}><td className="small">{new Date(r.ts).toLocaleString()}</td><td>{r.user}</td><td className="mono small">{r.action}</td><td className="small">{r.entity} #{r.entity_id}</td>
        <td className="mono small">{r.before ? JSON.stringify(r.before) : ""}</td><td className="mono small">{r.after ? JSON.stringify(r.after) : ""}</td><td className="small">{r.detail}</td></tr>)}</tbody></table></div></div>
  );
}
