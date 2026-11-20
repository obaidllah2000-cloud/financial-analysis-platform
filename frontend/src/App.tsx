import { useEffect, useState } from "react";
import { useLayoutEffect } from "react";
import { api, getUser, setUser } from "./api";
import { Lang, LangCtx, useLang, useT } from "./i18n";
import { startArabic, stopArabic } from "./i18n_ui";
import Workspace from "./Workspace";
import { Chip } from "./ui";

type View = { page: "companies" } | { page: "company"; id: number } | { page: "benchmarks" } | { page: "compare" } | { page: "methodology" };

export default function App() {
  const [auth, setAuth] = useState<{ required: boolean; logged_in: boolean } | null>(null);
  const check = () => fetch("/api/auth/status").then((r) => r.json()).then(setAuth).catch(() => setAuth({ required: false, logged_in: true }));
  useEffect(() => { check(); const h = () => setAuth((a) => ({ required: true, logged_in: false, ...(a ? {} : {}) })); window.addEventListener("fap-login-required", h); return () => window.removeEventListener("fap-login-required", h); }, []);
  if (!auth) return null;
  if (auth.required && !auth.logged_in) return <Login onDone={check} />;
  return <Main showLogout={auth.required} />;
}

function Login({ onDone }: { onDone: () => void }) {
  const [pw, setPw] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async (e: any) => {
    e.preventDefault(); setBusy(true); setErr("");
    const r = await fetch("/api/auth/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ password: pw }) });
    setBusy(false);
    if (r.ok) onDone(); else setErr("كلمة المرور غير صحيحة · Wrong password");
  };
  return (
    <div style={{ minHeight: "100%", display: "grid", placeItems: "center", padding: 16 }}>
      <form className="panel" onSubmit={submit} style={{ width: "min(380px, 100%)" }}>
        <h2>منصة التحليل المالي · Financial Analysis Platform</h2>
        <p className="small muted">أدخل كلمة المرور للدخول · Enter the password to continue</p>
        <input id="fap-password" type="password" autoFocus value={pw} onChange={(e) => setPw(e.target.value)} style={{ width: "100%", marginBottom: 10 }} aria-label="Password" />
        {err && <div className="badbox">{err}</div>}
        <button className="btn pri" type="submit" disabled={busy || !pw} style={{ width: "100%" }}>{busy ? "…" : "دخول · Sign in"}</button>
      </form>
    </div>
  );
}

function Main({ showLogout }: { showLogout: boolean }) {
  const [lang, setLangState] = useState<Lang>(() => (localStorage.getItem("fap_lang") as Lang) || "en");
  // Store the choice before re-rendering so every request made by the re-mounted pages already carries it.
  const setLang = (l: Lang) => { try { localStorage.setItem("fap_lang", l); } catch { /* */ } setLangState(l); };
  useLayoutEffect(() => {
    const root = document.getElementById("root");
    if (lang === "ar" && root) startArabic(root); else stopArabic();
    return () => stopArabic();
  }, [lang]);
  const [view, setView] = useState<View>({ page: "companies" });
  const [companies, setCompanies] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [uid, setUid] = useState(getUser());
  const [meta, setMeta] = useState<any>(null);
  const reload = () => api.get("/api/companies").then(setCompanies);
  useEffect(() => { reload(); api.get("/api/users").then((u) => { setUsers(u); if (!uid && u[0]) { setUser(u[0].id); setUid(u[0].id); } }); api.get("/api/meta").then(setMeta); }, []);
  useEffect(() => { document.documentElement.dir = lang === "ar" ? "rtl" : "ltr"; document.documentElement.lang = lang; try { localStorage.setItem("fap_lang", lang); } catch { /* */ } }, [lang]);
  return (
    <LangCtx.Provider value={lang}>
      <div className="app" key={lang}>
        <Side showLogout={showLogout} view={view} setView={setView} companies={companies} lang={lang} setLang={setLang} users={users} uid={uid}
          setUid={(id: number) => { setUser(id); setUid(id); }} />
        <main className="main">
          {view.page === "companies" && <Companies companies={companies} meta={meta} reload={reload} open={(id) => setView({ page: "company", id })} />}
          {view.page === "company" && <Workspace key={view.id} id={view.id} meta={meta} onChange={reload} />}
          {view.page === "benchmarks" && <Benchmarks meta={meta} />}
          {view.page === "compare" && <Compare companies={companies} />}
          {view.page === "methodology" && <MethodologyPage />}
        </main>
      </div>
    </LangCtx.Provider>
  );
}

function Side({ view, setView, companies, lang, setLang, users, uid, setUid, showLogout }: any) {
  const t = useT();
  return (
    <aside className="side">
      <div className="logo">{t("Financial Analysis Platform")}<small>{t("AI-assisted, analyst-controlled")}</small></div>
      <button className={`navbtn ${view.page === "companies" ? "on" : ""}`} onClick={() => setView({ page: "companies" })}>{t("Companies")}</button>
      {companies.map((c: any) => (
        <button key={c.id} className={`navbtn ${view.page === "company" && view.id === c.id ? "on" : ""}`} style={{ paddingInlineStart: 20, fontSize: 13 }}
          onClick={() => setView({ page: "company", id: c.id })}>{c.name}</button>
      ))}
      <div className="navsec">Tools</div>
      <button className={`navbtn ${view.page === "compare" ? "on" : ""}`} onClick={() => setView({ page: "compare" })}>{t("Multi-company comparison")}</button>
      <button className={`navbtn ${view.page === "benchmarks" ? "on" : ""}`} onClick={() => setView({ page: "benchmarks" })}>{t("Benchmarks")}</button>
      <button className={`navbtn ${view.page === "methodology" ? "on" : ""}`} onClick={() => setView({ page: "methodology" })}>{t("Methodology")}</button>
      <div className="navsec">{t("User")}</div>
      <select value={uid} onChange={(e) => setUid(Number(e.target.value))} style={{ margin: "0 8px" }}>
        {users.map((u: any) => <option key={u.id} value={u.id}>{u.name} ({u.role})</option>)}
      </select>
      <div className="navsec">{t("Language")}</div>
      <div className="row" style={{ padding: "0 8px" }}>
        <button className={`btn sm ${lang === "en" ? "pri" : ""}`} onClick={() => setLang("en")} data-no-translate>English</button>
        <button className={`btn sm ${lang === "ar" ? "pri" : ""}`} onClick={() => setLang("ar")}>العربية</button>
      </div>
      {showLogout && <button className="navbtn" style={{ marginTop: 12 }} onClick={async () => { await fetch("/api/auth/logout", { method: "POST" }); location.reload(); }}>تسجيل الخروج · Sign out</button>}
    </aside>
  );
}

function Companies({ companies, meta, reload, open }: { companies: any[]; meta: any; reload: () => void; open: (id: number) => void }) {
  const t = useT();
  const [f, setF] = useState<any>({ name: "", industry: "Manufacturing", currency: "", country: "", fy_end: "31-Dec", reporting_type: "Standalone", methodology: "academic" });
  const [err, setErr] = useState("");
  const create = async () => {
    setErr("");
    try { const c = await api.post("/api/companies", f); await reload(); open(c.id); } catch (e: any) { setErr(e.message); }
  };
  return (
    <>
      <div className="topbar"><h1>{t("Companies")}</h1>
        <a className="btn" href="/api/template">{t("Download template")}</a>
        <a className="btn" href="/api/template?sample=true">{t("Download 5-year sample")}</a>
      </div>
      <div className="note">Workflow: Excel data entry → upload → validation → classification review → assumption confirmation → approval → multi-year analysis → interpretation → reports. Nothing is approved automatically.</div>
      <div className="panel">
        <h2>{t("New company")}</h2>
        <div className="row">
          <input type="text" placeholder={t("Name")} value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} />
          <select value={f.industry} onChange={(e) => setF({ ...f, industry: e.target.value })}>{(meta?.industries || []).map((i: string) => <option key={i}>{i}</option>)}</select>
          <input type="text" placeholder={t("Currency")} value={f.currency} style={{ width: 90 }} onChange={(e) => setF({ ...f, currency: e.target.value.toUpperCase() })} />
          <input type="text" placeholder={t("Country")} value={f.country} style={{ width: 120 }} onChange={(e) => setF({ ...f, country: e.target.value })} />
          <select value={f.reporting_type} onChange={(e) => setF({ ...f, reporting_type: e.target.value })}><option>Standalone</option><option>Consolidated</option></select>
          <select value={f.methodology} onChange={(e) => setF({ ...f, methodology: e.target.value })}>
            <option value="academic">Academic methodology (course)</option><option value="professional">Professional methodology</option>
          </select>
          <button className="btn pri" disabled={!f.name} onClick={create}>{t("Create")}</button>
        </div>
        {err && <div className="badbox" style={{ marginTop: 10 }}>{err}</div>}
      </div>
      <div className="panel">
        <table>
          <thead><tr><th>{t("Name")}</th><th>{t("Industry")}</th><th>{t("Currency")}</th><th>Methodology</th><th>Years</th><th>Classification</th><th>Pending assumptions</th><th>Data errors</th><th>{t("Status")}</th></tr></thead>
          <tbody>
            {companies.map((c) => { const g = c.governance || {}; return (
              <tr key={c.id} className="click" onClick={() => open(c.id)}>
                <td><b>{c.name}</b></td><td>{c.industry}</td><td>{c.currency}</td><td>{c.methodology}</td>
                <td>{g.has_data ? `${g.years?.[0]}–${g.years?.[g.years.length - 1]} (${g.years?.length})` : "no data"}</td>
                <td>{g.has_data ? `${Math.round((g.classification_progress || 0) * 100)}%` : "—"}</td>
                <td>{g.has_data ? g.pending_assumptions?.length : "—"}</td><td>{g.has_data ? g.issues?.error || 0 : "—"}</td>
                <td>{g.has_data ? <Chip s={g.ready_for_approval ? "verified" : "provisional"} label={g.ready_for_approval ? "ready" : "in review"} /> : <Chip s="needs_info" label="awaiting upload" />}</td>
              </tr>); })}
          </tbody>
        </table>
      </div>
    </>
  );
}

function Benchmarks({ meta }: { meta: any }) {
  const [data, setData] = useState<any>(null);
  const [ind, setInd] = useState("Manufacturing");
  const [f, setF] = useState({ ratio_key: "current_ratio", value: "", source: "User entered" });
  const [msg, setMsg] = useState("");
  const load = () => api.get(`/api/benchmarks?industry=${encodeURIComponent(ind)}`).then(setData);
  useEffect(() => { load(); }, [ind]);
  const run = async (p: Promise<any>) => { setMsg(""); try { await p; load(); } catch (e: any) { setMsg(e.message); } };
  const lang = useLang();
  const name = (k: string) => { const r = meta?.ratios.find((r: any) => r.key === k); return (lang === "ar" ? r?.name_ar : r?.name_en) || k; };
  return (
    <>
      <div className="topbar"><h1>Benchmarks</h1></div>
      <div className="note">Benchmarks are configurable per industry. If none are set, ratio risk relies on the company's own trend and the limitation is stated in reports. Presets are clearly labelled — the course figures are teaching examples, not real industry data.</div>
      <div className="panel">
        <div className="row"><b>Industry</b><select value={ind} onChange={(e) => setInd(e.target.value)}>{(meta?.industries || []).map((i: string) => <option key={i}>{i}</option>)}</select></div>
        <h3>Add / update</h3>
        <div className="row">
          <select value={f.ratio_key} onChange={(e) => setF({ ...f, ratio_key: e.target.value })}>{(meta?.ratios || []).map((r: any) => <option key={r.key} value={r.key}>{name(r.key)}</option>)}</select>
          <input type="number" placeholder="Value (ratios as decimals, e.g. 0.45 for 45%)" value={f.value} style={{ width: 280 }} onChange={(e) => setF({ ...f, value: e.target.value })} />
          <input type="text" value={f.source} onChange={(e) => setF({ ...f, source: e.target.value })} />
          <button className="btn pri" disabled={!f.value} onClick={() => run(api.post("/api/benchmarks", { industry: ind, ratio_key: f.ratio_key, value: Number(f.value), source: f.source }))}>Save</button>
        </div>
        <h3>Presets</h3>
        <div className="row">{data && Object.entries(data.presets).map(([k, p]: any) => (
          <button key={k} className="btn" onClick={() => run(api.post("/api/benchmarks/preset", { industry: ind, preset: k }))}>{p.label}</button>))}</div>
        <h3>Import (CSV / Excel: industry, ratio_key, value, source)</h3>
        <input type="file" accept=".csv,.xlsx" onChange={(e) => e.target.files?.[0] && run(api.upload("/api/benchmarks/import", e.target.files[0]))} />
        {msg && <div className="badbox" style={{ marginTop: 10 }}>{msg}</div>}
      </div>
      <div className="panel">
        <table><thead><tr><th>Ratio</th><th className="n">Value</th><th>Source</th><th /></tr></thead>
          <tbody>{data?.items.map((b: any) => (<tr key={b.id}><td>{name(b.ratio_key)}</td><td className="n">{b.value}</td><td className="small">{b.source}</td>
            <td><button className="btn sm" onClick={() => run(api.del(`/api/benchmarks/${b.id}`))}>Delete</button></td></tr>))}</tbody></table>
        {data && !data.items.length && <p className="muted">No benchmarks for {ind}.</p>}
      </div>
    </>
  );
}

function Compare({ companies }: { companies: any[] }) {
  const lang = useLang();
  const [sel, setSel] = useState<number[]>([]);
  const [res, setRes] = useState<any>(null);
  const [err, setErr] = useState("");
  const run = () => { setErr(""); api.get(`/api/compare?ids=${sel.join(",")}`).then(setRes).catch((e) => setErr(e.message)); };
  const withData = companies.filter((c) => c.governance?.has_data);
  return (
    <>
      <div className="topbar"><h1>Multi-company comparison</h1></div>
      <div className="panel">
        <div className="row">{withData.map((c) => (
          <label key={c.id} className="row" style={{ gap: 4 }}><input type="checkbox" checked={sel.includes(c.id)}
            onChange={(e) => setSel(e.target.checked ? [...sel, c.id] : sel.filter((x) => x !== c.id))} />{c.name}</label>))}
          <button className="btn pri" disabled={sel.length < 2} onClick={run}>Compare</button></div>
        {err && <div className="badbox">{err}</div>}
      </div>
      {res && (
        <div className="panel">
          {res.warnings.map((w: string, i: number) => <div key={i} className="warnbox">{w}</div>)}
          {res.compatible && <div className="okbox">Reporting currency, methodology, year-end and basis are compatible.</div>}
          <p className="small muted">Common years: {res.common_years.join(", ") || "none"}</p>
          <div className="scroll"><table>
            <thead><tr><th>Ratio</th><th>Year</th>{res.companies.map((c: any) => <th key={c.company.id} className="n">{c.company.name}</th>)}</tr></thead>
            <tbody>{Object.keys(res.ratio_meta).flatMap((k) => res.common_years.map((y: number, i: number) => (
              <tr key={k + y}><td>{i === 0 ? <b>{(lang === "ar" && res.ratio_meta[k].name_ar) || res.ratio_meta[k].name_en}</b> : ""}</td><td>{y}</td>
                {res.companies.map((c: any) => { const cell = c.ratios[k]?.[y]; return <td key={c.company.id} className="n">{cell?.display} {cell && cell.status !== "verified" && cell.status !== "approved_assumption" && <Chip s={cell.status} />}</td>; })}
              </tr>)))}</tbody></table></div>
        </div>)}
    </>
  );
}

function MethodologyPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [q, setQ] = useState("");
  useEffect(() => { api.get("/api/methodology").then(setRows); }, []);
  const f = rows.filter((r) => !q || JSON.stringify(r).toLowerCase().includes(q.toLowerCase()));
  return (
    <>
      <div className="topbar"><h1>Financial Methodology Database</h1><input type="text" placeholder="Search…" value={q} onChange={(e) => setQ(e.target.value)} /></div>
      <div className="note">Generated from the same registry the calculation engine executes. Academic = lectures & solved exams (default); Professional = additional industry practice; differences are documented and configurable through assumptions.</div>
      {f.map((r, i) => (
        <div className="card" key={i}>
          <div className="t">{r.indicator} {r.indicator_ar && <span className="muted">— {r.indicator_ar}</span>} <Chip s={r.methodology === "academic" ? "approved_assumption" : r.methodology === "both" ? "verified" : "needs_info"} label={r.methodology} /> <span className="chip c-needs_info">{r.category}</span></div>
          <dl className="kv">
            <dt>Formula</dt><dd className="mono">{r.formula}</dd><dt>Required accounts</dt><dd>{r.required_accounts}</dd>
            <dt>Classifications</dt><dd className="small mono">{r.classifications}</dd><dt>Interpretation</dt><dd>{r.interpretation}</dd>
            <dt>Assumptions</dt><dd>{r.assumptions}</dd><dt>Benchmarks</dt><dd>{r.benchmarks}</dd><dt>Source</dt><dd>{r.source}</dd><dt>Application</dt><dd>{r.application}</dd>
          </dl>
        </div>))}
    </>
  );
}
