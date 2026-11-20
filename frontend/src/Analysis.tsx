import { Fragment, useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, fmtNum, fmtPct } from "./api";
import { useLang } from "./i18n";
import { Chip, Modal, TraceModal } from "./ui";

export const PALETTE = ["#2f6fb0", "#0f9d8a", "#d97b29", "#8b5cc7", "#c4435a", "#6b7a8c"];
const FLAG: Record<string, string> = { base_zero: "n/m", sign_change: "±", negative_base: "−base", missing: "" };

function useAnalysis(co: any, years?: number[]) {
  const [d, setD] = useState<any>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    setD(null);
    api.get(`/api/companies/${co.id}/analysis${years && years.length ? `?years=${years.join(",")}` : ""}`).then(setD).catch((e) => setErr(e.message));
  }, [co.id, (years || []).join(",")]);
  return { d, err };
}

function useInterpretation(co: any) {
  const [d, setD] = useState<any>(null);
  useEffect(() => { api.get(`/api/companies/${co.id}/interpretation`).then(setD).catch(() => setD({ ratios: {}, dupont: {}, sources_uses: [] })); }, [co.id, co.data_version]);
  return d;
}

const VERDICT_CHIP: Record<string, string> = { favorable: "verified", unfavorable: "invalid", mixed: "provisional", neutral: "pending", "n/a": "needs_info" };

/** The professor's 7 steps: result, comparison, increase/decrease, meaning, favorable or not, impact, conclusion & recommendation. */
export function SevenSteps({ items, years }: { items: any[]; years: number[] }) {
  const usable = (items || []).filter((x) => x.steps?.length);
  const [y, setY] = useState<number | null>(null);
  if (!usable.length) return <p className="small muted">n/a</p>;
  const cur = usable.find((x) => x.year === y) || usable[usable.length - 1];
  return (
    <div className="panel" style={{ margin: "8px 0", background: "var(--card, #fff)" }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <b>Academic interpretation (professor's method)</b>
        <div className="row">{years.filter((yy) => usable.some((x) => x.year === yy)).map((yy) =>
          <button key={yy} className={`btn sm ${cur.year === yy ? "pri" : ""}`} onClick={() => setY(yy)}>{yy}</button>)}</div>
      </div>
      <div className="row small" style={{ margin: "6px 0" }}><Chip s={VERDICT_CHIP[cur.verdict] || "pending"} label={cur.verdict} />
        <Chip s={cur.basis === "academic" ? "verified" : "pending"} label={cur.basis} /><Chip s={cur.status} /></div>
      <ol style={{ margin: 0, paddingInlineStart: 22 }}>{cur.steps.map((st: any, i: number) =>
        <li key={i} style={{ marginBottom: 6 }}><b>{st.title}</b><div className="small" style={{ whiteSpace: "pre-wrap" }}>{st.text}</div></li>)}</ol>
    </div>
  );
}

function YearPicker({ all, sel, setSel }: { all: number[]; sel: number[]; setSel: (y: number[]) => void }) {
  return <div className="row small">Years:{all.map((y) => <label key={y} className="row" style={{ gap: 3 }}><input type="checkbox" checked={sel.includes(y)}
    onChange={(e) => setSel(e.target.checked ? [...sel, y].sort() : sel.filter((x) => x !== y))} />{y}</label>)}</div>;
}

function Change({ c }: { c: any }) {
  if (!c) return <span className="muted">—</span>;
  if (c.pct_change == null) return <span className="muted" title={c.flag}>{FLAG[c.flag] ?? "—"}</span>;
  return <span className={c.pct_change >= 0 ? "pos" : "neg"} title={c.flag || ""}>{fmtPct(c.pct_change)}{c.flag === "sign_change" ? " ±" : ""}</span>;
}

export function Statements({ co }: any) {
  const lang = useLang();
  const [st, setSt] = useState("BS");
  const [d, setD] = useState<any>(null);
  const [mode, setMode] = useState("values");
  const [drill, setDrill] = useState<any>(null);
  const [q, setQ] = useState("");
  useEffect(() => { setD(null); api.get(`/api/companies/${co.id}/statements/${st}`).then(setD); }, [co.id, st]);
  if (!d) return <p>Loading…</p>;
  const ys: number[] = d.years;
  const rows = d.rows.filter((r: any) => !q || r.account.toLowerCase().includes(q.toLowerCase()));
  return (
    <>
      <div className="row" style={{ marginBottom: 12 }}>
        {[["BS", "Balance Sheet"], ["IS", "Income Statement"], ["CF", "Cash Flow"]].map(([k, l]) => <button key={k} className={`btn ${st === k ? "pri" : ""}`} onClick={() => setSt(k)}>{l}</button>)}
        <span style={{ width: 20 }} />
        {[["values", "Values"], ["change", "% change (YoY)"], ["common", st === "BS" ? "% of total assets" : st === "IS" ? "% of sales" : "—"]].map(([k, l]) =>
          (st !== "CF" || k !== "common") && <button key={k} className={`btn sm ${mode === k ? "pri" : ""}`} onClick={() => setMode(k)}>{l}</button>)}
        <input type="text" placeholder="Filter accounts…" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      <div className="panel">
        <h2>Accounts as uploaded (original names) — click a row to drill down</h2>
        <div className="scroll"><table>
          <thead><tr><th>Account</th><th>Classification</th><th>Status</th>{ys.map((y) => <th key={y} className="n">{y}</th>)}<th>Trend</th><th className="n">CAGR</th><th>AI notes</th></tr></thead>
          <tbody>{rows.map((r: any) => (
            <tr key={r.account_id} className={`click ${r.subtotal ? "sub" : ""}`} onClick={() => setDrill(r)}>
              <td>{r.account}</td><td className="small">{lang === "ar" ? r.category_label_ar : r.category_label}</td><td><Chip s={r.status} /></td>
              {ys.map((y, i) => <td key={y} className="n">{mode === "values" ? fmtNum(r.values[y]) : mode === "common" ? fmtPct(r.common_size[y]) : i === 0 ? "—" : <Change c={r.stats.changes[i - 1]} />}</td>)}
              <td className="small">{r.stats.trend}</td><td className="n">{r.stats.cagr == null ? <span className="muted">n/m</span> : fmtPct(r.stats.cagr)}</td>
              <td className="small">{r.observations.length ? `⚠ ${r.observations.length}` : ""}</td>
            </tr>))}</tbody></table></div>
        <p className="small muted">Subtotals are shown in italics; they are used to reconcile, never added. “n/m” = not meaningful (zero base or non-positive values); “±” = sign change.</p>
      </div>
      <div className="panel">
        <h2>Standardised lines (computed from approved classifications)</h2>
        <table><thead><tr><th>Line</th>{ys.map((y) => <th key={y} className="n">{y}</th>)}<th>Source</th></tr></thead>
          <tbody>{d.key_lines.map((k: any) => <tr key={k.key}><td>{k.label} {k.provisional && <Chip s="provisional" />}</td>
            {ys.map((y) => <td key={y} className="n">{fmtNum(k.values[y])}</td>)}<td className="small muted">{[...new Set(Object.values(k.sources))].join(", ")}</td></tr>)}</tbody></table>
      </div>
      {drill && <Modal onClose={() => setDrill(null)}>
        <h2>{drill.account}</h2>
        <dl className="kv"><dt>Code</dt><dd>{drill.code || "—"}</dd><dt>Classification</dt><dd>{drill.category_label} ({drill.element}, {drill.group}) <Chip s={drill.status} /></dd>
          <dt>Used in calculations</dt><dd>{drill.used_in_calculations ? "Yes" : "No"}</dd>
          {drill.normalization_notes.length > 0 && <><dt>Normalization</dt><dd>{drill.normalization_notes.map((n: string, i: number) => <div key={i} className="small">{n}</div>)}</dd></>}
          {drill.observations.length > 0 && <><dt>AI observations</dt><dd>{drill.observations.join(" · ")}</dd></>}</dl>
        <table><thead><tr><th>Year</th><th className="n">Original</th><th className="n">Normalized</th><th className="n">Common size</th><th className="n">Δ</th><th className="n">Δ%</th></tr></thead>
          <tbody>{ys.map((y, i) => { const c = drill.stats.changes[i - 1]; return <tr key={y}><td>{y}</td><td className="n">{fmtNum(drill.values[y], 2)}</td><td className="n">{fmtNum(drill.normalized[y], 2)}</td>
            <td className="n">{fmtPct(drill.common_size[y])}</td><td className="n">{i ? fmtNum(c?.abs_change) : "—"}</td><td className="n">{i ? <Change c={c} /> : "—"}</td></tr>; })}</tbody></table>
        <dl className="kv" style={{ marginTop: 10 }}><dt>Highest</dt><dd>{drill.stats.highest?.year}: {fmtNum(drill.stats.highest?.value)}</dd><dt>Lowest</dt><dd>{drill.stats.lowest?.year}: {fmtNum(drill.stats.lowest?.value)}</dd>
          <dt>Average</dt><dd>{fmtNum(drill.stats.average)}</dd><dt>Cumulative change</dt><dd>{fmtNum(drill.stats.cumulative_change)} ({fmtPct(drill.stats.cumulative_pct)})</dd>
          <dt>CAGR</dt><dd>{drill.stats.cagr == null ? `not meaningful${drill.stats.cagr_flag ? ` (${drill.stats.cagr_flag})` : ""}` : fmtPct(drill.stats.cagr)}</dd></dl>
        <div style={{ height: 200 }}><ResponsiveContainer><LineChart data={ys.map((y) => ({ year: y, v: drill.normalized[y] }))}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.3} /><XAxis dataKey="year" /><YAxis /><Tooltip /><Line dataKey="v" stroke={PALETTE[0]} strokeWidth={2} /></LineChart></ResponsiveContainer></div>
      </Modal>}
    </>
  );
}

const CAT_ORDER = ["liquidity", "activity", "profitability", "dupont", "debt", "cashflow", "market", "breakeven"];
const CAT_LABEL: Record<string, string> = { liquidity: "Liquidity", activity: "Activity & efficiency", profitability: "Profitability", dupont: "DuPont",
  debt: "Solvency & financial structure", cashflow: "Cash flow", market: "Modern techniques & market", breakeven: "Break-even & operating leverage" };

export function Ratios({ co }: any) {
  const lang = useLang();
  const { d, err } = useAnalysis(co);
  const [trace, setTrace] = useState<any>(null);
  const [open, setOpen] = useState<string | null>(null);
  const [cat, setCat] = useState("all");
  const interp = useInterpretation(co);
  if (err) return <div className="badbox">{err}</div>;
  if (!d) return <p>Loading…</p>;
  const ys: number[] = d.years;
  const groups = CAT_ORDER.map((c) => [c, d.ratios.filter((r: any) => r.category === c)] as const).filter(([c, rs]) => rs.length && (cat === "all" || cat === c));
  return (
    <>
      <div className="row" style={{ marginBottom: 10 }}>
        <button className={`btn sm ${cat === "all" ? "pri" : ""}`} onClick={() => setCat("all")}>All</button>
        {CAT_ORDER.map((c) => <button key={c} className={`btn sm ${cat === c ? "pri" : ""}`} onClick={() => setCat(c)}>{CAT_LABEL[c]}</button>)}
      </div>
      <div className="note">Click any value to see the formula, inputs, original accounts, assumptions and status. Status legend: <Chip s="verified" /> <Chip s="approved_assumption" /> <Chip s="provisional" /> <Chip s="needs_info" /> <Chip s="invalid" /></div>
      {groups.map(([c, rs]) => (
        <div key={c} className="panel">
          <h2>{CAT_LABEL[c]}</h2>
          <div className="scroll" style={{ maxHeight: "none" }}><table>
            <thead><tr><th>Ratio</th><th>Method</th>{ys.map((y) => <th key={y} className="n">{y}</th>)}<th className="n">YoY</th><th className="n">Benchmark</th><th>Risk</th></tr></thead>
            <tbody>{rs.map((r: any) => { const last = r.stats.changes?.[r.stats.changes.length - 1]; return (
              <Fragment key={r.key}>
                <tr><td><button className="btn sm" style={{ border: 0, padding: 0, background: "none", textAlign: "start", fontWeight: 600 }} onClick={() => setOpen(open === r.key ? null : r.key)}>{open === r.key ? "▾" : "▸"} {lang === "ar" ? r.name_ar : r.name_en}</button></td>
                  <td className="small muted">{r.methodology}</td>
                  {r.cells.map((x: any) => <td key={x.year} className="n" style={{ cursor: "pointer" }} onClick={() => setTrace({ ratio: r.key, year: x.year })} title={x.reasons.join("; ")}>
                    {x.display}<div><Chip s={x.status} /></div></td>)}
                  <td className="n">{r.unit === "text" ? "" : <Change c={last} />}</td>
                  <td className="n">{r.benchmark ? r.benchmark.value : <span className="muted">—</span>}</td><td><Chip s={r.risk} /></td></tr>
                {open === r.key && <tr><td colSpan={ys.length + 5} style={{ background: "var(--gray-bg)" }}>
                  <dl className="kv"><dt>Formula</dt><dd className="mono">{r.formula}</dd><dt>Interpretation</dt><dd>{r.interpretation}</dd>
                    <dt>Assessment</dt><dd>{r.comment}</dd><dt>Risk basis</dt><dd>{r.risk_basis}</dd>
                    {r.action && <><dt>Suggested action</dt><dd>{r.action}</dd></>}<dt>Source</dt><dd>{r.source}</dd>
                    {r.assumptions.length > 0 && <><dt>Assumptions</dt><dd className="mono small">{r.assumptions.join(", ")}</dd></>}</dl>
                  {interp ? <SevenSteps items={interp.ratios[r.key]} years={ys} /> : <p className="small muted">Loading…</p>}
                  {r.key === "roi" && interp?.dupont && <DupontBox d={interp.dupont} years={ys} />}
                  {r.unit !== "text" && <div style={{ height: 160 }}><ResponsiveContainer><LineChart data={r.cells.map((x: any) => ({ year: x.year, v: x.value, b: r.benchmark?.value }))}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} /><XAxis dataKey="year" /><YAxis /><Tooltip /><Line dataKey="v" name={lang === "ar" ? r.name_ar : r.name_en} stroke={PALETTE[0]} strokeWidth={2} />
                    {r.benchmark && <Line dataKey="b" name="Benchmark" stroke={PALETTE[2]} strokeDasharray="5 4" dot={false} />}</LineChart></ResponsiveContainer></div>}
                </td></tr>}
              </Fragment>); })}</tbody></table></div>
        </div>))}
      {trace && <TraceModal cid={co.id} ratio={trace.ratio} year={trace.year} onClose={() => setTrace(null)} />}
    </>
  );
}

const CHART_SETS: Record<string, string[]> = {
  "Revenue & profit": ["sales", "gp", "ebit", "np"], "Financial structure": ["ca", "fa", "cl", "ncl", "equity"],
  "Cash flow": ["ocf", "icf", "fincf", "fcf"], "Working capital items": ["cash", "ar", "inventory", "cl"],
};
const RATIO_SETS: Record<string, string[]> = {
  Liquidity: ["current_ratio", "quick_ratio", "cash_ratio"], Profitability: ["gpm", "oim", "nim", "roi", "roe"],
  Efficiency: ["tato", "fato", "inventory_turnover", "ar_turnover"], Leverage: ["debt_ratio", "debt_equity", "capital_structure_ratio"],
  "Days": ["acp", "asp", "liquidity_of_inventory"],
};

export function Comparison({ co }: any) {
  const lang = useLang();
  const [all, setAll] = useState<number[]>([]);
  const [sel, setSel] = useState<number[]>([]);
  const { d } = useAnalysis(co, sel);
  useEffect(() => { if (d && !all.length) { setAll(d.all_years); setSel(d.all_years); } }, [d]);
  const [cs, setCs] = useState("Revenue & profit");
  const [rs, setRs] = useState("Profitability");
  const lines = useMemo(() => Object.fromEntries((d?.key_lines || []).map((k: any) => [k.key, k])), [d]);
  const ratios = useMemo(() => Object.fromEntries((d?.ratios || []).map((r: any) => [r.key, r])), [d]);
  if (!d) return <p>Loading…</p>;
  const ys: number[] = d.years;
  const dataA = ys.map((y) => Object.fromEntries([["year", y], ...CHART_SETS[cs].filter((k) => lines[k]).map((k) => [lines[k].label, lines[k].values[y]])]));
  const dataR = ys.map((y) => Object.fromEntries([["year", y], ...RATIO_SETS[rs].filter((k) => ratios[k]).map((k) => [lang === "ar" ? ratios[k].name_ar : ratios[k].name_en, ratios[k].cells.find((c: any) => c.year === y)?.value])]));
  return (
    <>
      <div className="panel"><YearPicker all={all} sel={sel} setSel={(y) => y.length >= 1 && setSel(y)} /></div>
      <div className="grid g2">
        <div className="panel"><div className="row" style={{ justifyContent: "space-between" }}><h2>Trend</h2>
          <select value={cs} onChange={(e) => setCs(e.target.value)}>{Object.keys(CHART_SETS).map((k) => <option key={k}>{k}</option>)}</select></div>
          <div style={{ height: 280 }}><ResponsiveContainer><BarChart data={dataA}><CartesianGrid strokeDasharray="3 3" opacity={0.3} /><XAxis dataKey="year" /><YAxis /><Tooltip /><Legend />
            {CHART_SETS[cs].filter((k) => lines[k]).map((k, i) => <Bar key={k} dataKey={lines[k].label} fill={PALETTE[i]} />)}</BarChart></ResponsiveContainer></div></div>
        <div className="panel"><div className="row" style={{ justifyContent: "space-between" }}><h2>Ratios</h2>
          <select value={rs} onChange={(e) => setRs(e.target.value)}>{Object.keys(RATIO_SETS).map((k) => <option key={k}>{k}</option>)}</select></div>
          <div style={{ height: 280 }}><ResponsiveContainer><LineChart data={dataR}><CartesianGrid strokeDasharray="3 3" opacity={0.3} /><XAxis dataKey="year" /><YAxis /><Tooltip /><Legend />
            {RATIO_SETS[rs].filter((k) => ratios[k]).map((k, i) => <Line key={k} dataKey={lang === "ar" ? ratios[k].name_ar : ratios[k].name_en} stroke={PALETTE[i]} strokeWidth={2} />)}</LineChart></ResponsiveContainer></div></div>
      </div>
      <div className="panel">
        <h2>Multi-year comparison — horizontal analysis</h2>
        <div className="scroll"><table>
          <thead><tr><th>Item</th>{ys.map((y) => <th key={y} className="n">{y}</th>)}{ys.slice(1).map((y) => <th key={"c" + y} className="n">Δ% {y}</th>)}
            <th>Trend</th><th className="n">Highest</th><th className="n">Lowest</th><th className="n">Average</th><th className="n">Cumulative</th><th className="n">CAGR</th></tr></thead>
          <tbody>{d.key_lines.map((k: any) => (
            <tr key={k.key}><td>{k.label} {k.provisional && <Chip s="provisional" />}</td>{ys.map((y) => <td key={y} className="n">{fmtNum(k.values[y])}</td>)}
              {k.stats.changes.map((c: any) => <td key={c.year} className="n"><Change c={c} /></td>)}
              <td className="small">{k.stats.trend}</td><td className="n">{k.stats.highest ? `${fmtNum(k.stats.highest.value)} (${k.stats.highest.year})` : "—"}</td>
              <td className="n">{k.stats.lowest ? `${fmtNum(k.stats.lowest.value)} (${k.stats.lowest.year})` : "—"}</td><td className="n">{fmtNum(k.stats.average)}</td>
              <td className="n">{k.stats.cumulative_pct == null ? "n/m" : fmtPct(k.stats.cumulative_pct)}</td>
              <td className="n" title={k.stats.cagr_flag ? d.flag_text[k.stats.cagr_flag] : ""}>{k.stats.cagr == null ? <span className="muted">n/m</span> : fmtPct(k.stats.cagr)}</td></tr>))}</tbody></table></div>
        <p className="small muted">Percentage change = (current − previous) / |previous|. CAGR is shown only when the first and last values are positive. Gaps and sign changes are flagged rather than shown as misleading growth.</p>
      </div>
      <div className="panel">
        <h2>Vertical analysis — financial structure</h2>
        <table><thead><tr><th>Item</th><th>Base</th>{ys.map((y) => <th key={y} className="n">{y}</th>)}</tr></thead>
          <tbody>{d.key_lines.filter((k: any) => k.statement !== "CF").map((k: any) => <tr key={k.key}><td>{k.label}</td><td className="small muted">{k.statement === "BS" ? "% of total assets" : "% of sales"}</td>
            {ys.map((y) => <td key={y} className="n">{fmtPct(k.common_size[y])}</td>)}</tr>)}</tbody></table>
      </div>
    </>
  );
}

function DupontBox({ d, years }: { d: any; years: number[] }) {
  const y = [...years].reverse().find((yy) => d[yy]?.length || (d[yy] && typeof d[yy] === "string"));
  if (y === undefined) return null;
  const v = d[y];
  return <div className="note small"><b>{`DuPont ${y}`}</b><div style={{ whiteSpace: "pre-wrap" }}>{Array.isArray(v) ? v.join(" ") : typeof v === "string" ? v : v?.text || JSON.stringify(v)}</div></div>;
}

export function SourcesUses({ co }: any) {
  const { d } = useAnalysis(co);
  const interp = useInterpretation(co);
  const [i, setI] = useState(-1);
  if (!d) return <p>Loading…</p>;
  if (!d.sources_uses.length) return <div className="warnbox">At least two years of balance sheets are needed.</div>;
  const su = d.sources_uses[i < 0 ? d.sources_uses.length - 1 : i];
  const src = su.rows.filter((r: any) => r.type === "source").sort((a: any, b: any) => b.amount - a.amount);
  const use = su.rows.filter((r: any) => r.type === "use").sort((a: any, b: any) => b.amount - a.amount);
  return (
    <>
      <div className="row" style={{ marginBottom: 12 }}>{d.sources_uses.map((s: any, k: number) => <button key={k} className={`btn sm ${su === s ? "pri" : ""}`} onClick={() => setI(k)}>{s.from_year} → {s.to_year}</button>)}</div>
      <div className={su.reconciled ? "okbox" : "badbox"}>{su.reconciled ? `Total sources ${fmtNum(su.total_sources)} = total uses ${fmtNum(su.total_uses)} — reconciled.`
        : `Total sources ${fmtNum(su.total_sources)} ≠ total uses ${fmtNum(su.total_uses)} (difference ${fmtNum(su.difference)}) — check classifications.`}</div>
      <div className="grid g4">
        <div className="kpi"><div className="l">Short-term sources / uses</div><div className="v">{fmtPct(su.short_term_sources_pct)} / {fmtPct(su.short_term_uses_pct)}</div></div>
        <div className="kpi"><div className="l">Long-term sources / uses</div><div className="v">{fmtPct(su.long_term_sources_pct)} / {fmtPct(su.long_term_uses_pct)}</div></div>
        <div className="kpi"><div className="l">Golden-rule deviation</div><div className="v">{fmtPct(su.golden_rule_deviation)}</div><div className="s">|ST sources% − ST uses%|</div></div>
        <div className="kpi"><div className="l">Internal / external finance</div><div className="v">{fmtPct(su.internal_sources_pct)} / {fmtPct(su.external_sources_pct)}</div></div>
      </div>
      <div className="grid g2" style={{ marginTop: 16 }}>
        {[["Sources", src], ["Uses", use]].map(([t, list]: any) => (
          <div key={t} className="panel"><h2>{t}</h2><table><thead><tr><th>Movement</th><th>Term</th><th className="n">Amount</th><th className="n">%</th></tr></thead>
            <tbody>{list.map((r: any) => <tr key={r.account_id}><td>{r.description}{r.internal != null && <span className="small muted"> · {r.internal ? "internal" : "external"}</span>}</td><td className="small">{r.term}</td>
              <td className="n">{fmtNum(r.amount)}</td><td className="n">{fmtPct(r.pct)}</td></tr>)}</tbody></table></div>))}
      </div>
      {(() => { const t = interp?.sources_uses?.find((x: any) => x.from_year === su.from_year && x.to_year === su.to_year)?.text; return t ? (
        <div className="panel"><h2>Analysis (professor's method)</h2>
          {(Array.isArray(t) ? t : [t]).map((p: any, k: number) => <p key={k} style={{ whiteSpace: "pre-wrap" }}>{typeof p === "string" ? p : p.text || JSON.stringify(p)}</p>)}</div>) : null; })()}
      <div className="panel"><h2>Full movement table</h2><div className="scroll"><table>
        <thead><tr><th>Account</th><th className="n">Opening ({su.from_year})</th><th className="n">Closing ({su.to_year})</th><th className="n">Change</th><th>Source / use</th><th>Status</th></tr></thead>
        <tbody>{su.rows.map((r: any) => <tr key={r.account_id}><td>{r.account}</td><td className="n">{fmtNum(r.opening)}</td><td className="n">{fmtNum(r.closing)}</td><td className="n">{fmtNum(r.change)}</td>
          <td>{r.type || <span className="muted">no change</span>}</td><td><Chip s={r.status} /></td></tr>)}</tbody></table></div>
        <p className="small muted">Rules (Lecture 2, Q3): asset increase = use, asset decrease = source; liability/equity increase = source, decrease = use; accumulated depreciation increase = source.</p></div>
    </>
  );
}
