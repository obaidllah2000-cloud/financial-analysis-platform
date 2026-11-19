import { useEffect, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, fmtNum, fmtPct } from "./api";
import { PALETTE } from "./Analysis";

const ROLE_LABEL: Record<string, string> = { "": "—", st_debt: "Short-term debt (financing target)", lt_debt: "Long-term debt (financing target)",
  common: "Common shares (financing target)", re: "Retained earnings" };
const TARGET_LABEL: Record<string, string> = { st_debt: "Short-term debt / N/P", lt_debt: "Long-term bonds / loans", common: "Common shares" };

function Num({ v, set, step = "any", w = 110, pct = false }: { v: any; set: (x: any) => void; step?: string; w?: number; pct?: boolean }) {
  const shown = v === null || v === undefined || v === "" ? "" : pct ? +(v * 100).toFixed(6) : v;
  return <input type="number" step={step} style={{ width: w }} value={shown} onChange={(e) => set(e.target.value === "" ? "" : pct ? Number(e.target.value) / 100 : Number(e.target.value))} />;
}

export default function Forecasting({ co }: any) {
  const [tool, setTool] = useState("position");
  const [base, setBase] = useState<any>(null);
  const [err, setErr] = useState("");
  useEffect(() => { api.get(`/api/companies/${co.id}/forecast/base`).then(setBase).catch((e) => setErr(e.message)); }, [co.id]);
  if (err) return <div className="badbox">{err}</div>;
  if (!base) return <p>Loading…</p>;
  return (
    <>
      <div className="row" style={{ marginBottom: 12 }}>
        {[["position", "Forecasted financial position"], ["pos", "% of sales (AFN)"], ["be", "Break-even & operating leverage"], ["cash", "Cash budget"]].map(([k, l]) =>
          <button key={k} className={`btn ${tool === k ? "pri" : ""}`} onClick={() => setTool(k)}>{l}</button>)}
      </div>
      <div className="note">Scenarios are planning tools: they start from the {base.year} figures but never change the uploaded or approved data.
        {base.provisional && " Some starting accounts are not yet approved, so the starting point itself is provisional."}</div>
      {tool === "position" && <Position co={co} base={base} />}
      {tool === "pos" && <PercentOfSales co={co} base={base} />}
      {tool === "be" && <BreakEven base={base} />}
      {tool === "cash" && <CashBudget />}
    </>
  );
}

function LinesEditor({ lines, setLines, mode }: { lines: any[]; setLines: (l: any[]) => void; mode: "bs" | "is" }) {
  const upd = (i: number, k: string, v: any) => setLines(lines.map((l, j) => (j === i ? { ...l, [k]: v } : l)));
  return (
    <div className="scroll" style={{ maxHeight: 340 }}><table>
      <thead><tr><th>Line ({mode === "bs" ? "balance sheet" : "income statement"})</th><th className="n">Latest value</th>
        {mode === "bs" ? <><th>Side</th><th>Grows with sales</th><th>Role</th></> : <><th>Type</th><th>Grows with sales</th></>}</tr></thead>
      <tbody>{lines.map((l, i) => (
        <tr key={i}><td>{l.name}</td><td className="n"><Num v={l.value} set={(v) => upd(i, "value", v)} /></td>
          {mode === "bs" ? <>
            <td className="small">{{ A: "Asset", L: "Liability", E: "Equity" }[l.side as string]}</td>
            <td><input type="checkbox" checked={!!l.spontaneous} disabled={l.role === "re"} onChange={(e) => upd(i, "spontaneous", e.target.checked)} /></td>
            <td><select value={l.role || ""} onChange={(e) => upd(i, "role", e.target.value || null)}>{Object.entries(ROLE_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></td>
          </> : <>
            <td className="small">{l.kind}</td><td><input type="checkbox" checked={!!l.grows} onChange={(e) => upd(i, "grows", e.target.checked)} /></td>
          </>}
        </tr>))}</tbody></table></div>
  );
}

function Position({ co, base }: any) {
  const [p, setP] = useState<any>(() => ({
    growth: 0.1, dps_growth: 0.05, tax_rate: base.tax_rate, interest: base.interest, pref_div: base.pref_div, common_div: base.common_div,
    shares: base.shares, dps: base.dps, share_price: base.share_price, course_rounding: false, eva_rate: 0.1,
    hierarchy: [{ target: "st_debt", pct: 0.25, rate: 0.08 }, { target: "lt_debt", pct: 0.25, rate: 0.10 }, { target: "common", pct: 0.5, rate: 0 }],
    bs_lines: base.bs_lines, is_lines: base.is_lines }));
  const [res, setRes] = useState<any>(null);
  const [err, setErr] = useState("");
  const set = (k: string) => (v: any) => setP({ ...p, [k]: v });
  const total = p.hierarchy.reduce((a: number, h: any) => a + Number(h.pct || 0), 0);
  const run = async () => { setErr(""); try { setRes(await api.post(`/api/companies/${co.id}/forecast/position`, p)); } catch (e: any) { setErr(e.message); setRes(null); } };
  const ccy = base.currency;
  return (
    <>
      <div className="panel">
        <h2>Forecasted financial position method (Lecture 5, Q4)</h2>
        <p className="small muted">Stage 1 grows the sales-related lines; the gap between assets and liabilities + equity is financed by the hierarchy;
          the new interest and dividends are fed back, and stages repeat until the gap is about zero.</p>
        <div className="grid g4">
          <label>Sales growth %<br /><Num v={p.growth} set={set("growth")} pct /></label>
          <label>Tax rate %<br /><Num v={p.tax_rate} set={set("tax_rate")} pct /></label>
          <label>Current interest ({ccy})<br /><Num v={p.interest} set={set("interest")} /></label>
          <label>Preferred dividends<br /><Num v={p.pref_div} set={set("pref_div")} /></label>
          <label>Common shares outstanding<br /><Num v={p.shares} set={set("shares")} /></label>
          <label>Last dividend per share<br /><Num v={p.dps} set={set("dps")} /></label>
          <label>Promised DPS growth %<br /><Num v={p.dps_growth} set={set("dps_growth")} pct /></label>
          <label>Share price for new issue<br /><Num v={p.share_price} set={set("share_price")} /></label>
          <label>EVA opportunity rate on R/E %<br /><Num v={p.eva_rate} set={set("eva_rate")} pct /></label>
        </div>
        <h3>Financial hierarchy</h3>
        <table style={{ maxWidth: 640 }}><thead><tr><th>Source</th><th className="n">Share %</th><th className="n">Annual interest %</th></tr></thead>
          <tbody>{p.hierarchy.map((h: any, i: number) => (
            <tr key={h.target}><td>{TARGET_LABEL[h.target]}</td>
              <td className="n"><Num v={h.pct} pct w={80} set={(v) => setP({ ...p, hierarchy: p.hierarchy.map((x: any, j: number) => (j === i ? { ...x, pct: v } : x)) })} /></td>
              <td className="n">{h.target === "common" ? "—" : <Num v={h.rate} pct w={80} set={(v) => setP({ ...p, hierarchy: p.hierarchy.map((x: any, j: number) => (j === i ? { ...x, rate: v } : x)) })} />}</td></tr>))}
            <tr><td><b>Total</b></td><td className={`n ${Math.abs(total - 1) > 1e-6 ? "neg" : ""}`}>{fmtPct(total)}</td><td className="small muted">Semi-annual rates: enter twice the rate (Q4: 4.5% twice yearly = 9%).</td></tr></tbody></table>
        <details style={{ marginTop: 10 }}><summary>Starting lines from {base.year} (edit growth rules, roles or values)</summary>
          <div className="grid g2" style={{ marginTop: 8 }}>
            <LinesEditor lines={p.is_lines} setLines={set("is_lines")} mode="is" />
            <LinesEditor lines={p.bs_lines} setLines={set("bs_lines")} mode="bs" />
          </div></details>
        <div className="row" style={{ marginTop: 10 }}>
          <label className="row small"><input type="checkbox" checked={p.course_rounding} onChange={(e) => set("course_rounding")(e.target.checked)} />Round every line to whole units at each stage (like the hand-worked solutions)</label>
          <button className="btn pri" disabled={Math.abs(total - 1) > 1e-6} onClick={run}>Run forecast</button>
        </div>
        {err && <div className="badbox" style={{ marginTop: 8 }}>{err}</div>}
      </div>
      {res && <PositionResult res={res} ccy={ccy} />}
    </>
  );
}

function PositionResult({ res, ccy }: any) {
  const st = res.stages;
  const lastS = st[st.length - 1];
  const sumRows: [string, string][] = [["ebit", "EBIT"], ["interest", "Interest"], ["ebt", "EBT"], ["tax", "Taxes"], ["np", "Net profit"],
    ["pref_div", "P.S. dividends"], ["ndp", "Net distributable profit"], ["common_div", "C.S. dividends"], ["re_addition", "Retained earnings for the year"], ["eva", "EVA"]];
  return (
    <>
      <div className={res.converged ? "okbox" : "warnbox"}>{res.converged ? `Balanced after ${st.length} stage(s): total assets ${fmtNum(lastS.total_assets, 1)} = liabilities + equity ${fmtNum(lastS.total_claims, 1)}.` : "Did not converge."}
        {" "}New financing: {Object.entries(res.total_new_financing).map(([k, v]: any) => `${TARGET_LABEL[k]} ${fmtNum(v, 1)}`).join(" · ")} {ccy}.</div>
      {res.notes.map((n: string, i: number) => <div key={i} className="warnbox">{n}</div>)}
      <div className="grid g4">
        <div className="kpi"><div className="l">First-stage financing need</div><div className="v">{fmtNum(st[0].financing_need, 1)}</div></div>
        <div className="kpi"><div className="l">Net profit: actual → forecast</div><div className="v">{fmtNum(res.actual.np, 1)} → {fmtNum(lastS.is_summary.np, 1)}</div></div>
        <div className="kpi"><div className="l">EVA: before → after</div><div className="v">{fmtNum(res.actual.eva, 1)} → {fmtNum(lastS.is_summary.eva, 1)}</div>
          <div className="s">{lastS.is_summary.eva > res.actual.eva ? "EVA increases — the expansion adds value" : "EVA decreases — the expansion destroys value"}</div></div>
        <div className="kpi"><div className="l">New shares issued</div><div className="v">{fmtNum(lastS.is_summary.new_shares, 3)}</div><div className="s">new DPS {fmtNum(lastS.is_summary.new_dps, 4)}</div></div>
      </div>
      <div className="panel" style={{ marginTop: 16 }}>
        <h2>Income statement by stage</h2>
        <div className="scroll"><table>
          <thead><tr><th>Item</th><th className="n">Actual</th><th>Rule</th>{st.map((s: any) => <th key={s.stage} className="n">Stage {s.stage}</th>)}</tr></thead>
          <tbody>
            {st[0].income_statement.map((r: any, i: number) => <tr key={r.name}><td>{r.name}</td><td className="n">{fmtNum(r.actual, 1)}</td><td className="small muted">{r.rule}</td>
              {st.map((s: any) => <td key={s.stage} className="n">{fmtNum(s.income_statement[i].value, 1)}</td>)}</tr>)}
            {sumRows.map(([k, l]) => <tr key={k}><td><b>{l}</b></td><td className="n">{k in res.actual ? fmtNum(res.actual[k], 1) : ""}</td>
              <td className="small muted">{k === "interest" ? "+ interest on new debt" : k === "common_div" ? "shares × new DPS" : ""}</td>
              {st.map((s: any) => <td key={s.stage} className="n">{fmtNum(s.is_summary[k], 1)}</td>)}</tr>)}
          </tbody></table></div>
        <p className="small muted">Dividend rule: {lastS.is_summary.dividend_rule}. EVA = NP − (interest + P.S. div + C.S. div + {fmtPct(res.actual.eva_rate, 0)} × R/E), as in the Q3/Q4 solutions.</p>
      </div>
      <div className="panel">
        <h2>Financial position by stage</h2>
        <div className="scroll"><table>
          <thead><tr><th>Item</th><th className="n">Actual</th>{st.map((s: any) => <th key={s.stage} className="n">Stage {s.stage}</th>)}<th>Rule (last stage)</th></tr></thead>
          <tbody>
            {lastS.balance_sheet.map((r: any) => <tr key={r.name}><td>{r.name}</td><td className="n">{fmtNum(r.actual, 1)}</td>
              {st.map((s: any) => { const x = s.balance_sheet.find((b: any) => b.name === r.name); return <td key={s.stage} className="n">{x ? fmtNum(x.value, 1) : "—"}</td>; })}
              <td className="small muted">{r.rule}</td></tr>)}
            <tr><td><b>Total assets</b></td><td />{st.map((s: any) => <td key={s.stage} className="n"><b>{fmtNum(s.total_assets, 1)}</b></td>)}<td /></tr>
            <tr><td><b>Total liabilities & equity</b></td><td />{st.map((s: any) => <td key={s.stage} className="n"><b>{fmtNum(s.total_claims, 1)}</b></td>)}<td /></tr>
            <tr><td><b>Financing need</b></td><td />{st.map((s: any) => <td key={s.stage} className={`n ${Math.abs(s.financing_need) > 0.5 ? "neg" : "pos"}`}><b>{fmtNum(s.financing_need, 2)}</b></td>)}<td /></tr>
          </tbody></table></div>
        <h3>How each stage's need is financed</h3>
        <table><thead><tr><th>Stage</th>{st[0].next_split.map((x: any) => <th key={x.target} className="n">{TARGET_LABEL[x.target]}</th>)}<th className="n">New interest</th><th className="n">New shares</th></tr></thead>
          <tbody>{st.filter((s: any) => Math.abs(s.financing_need) > 0.5).map((s: any) => <tr key={s.stage}><td>After stage {s.stage}</td>
            {s.next_split.map((x: any) => <td key={x.target} className="n">{fmtNum(x.amount, 2)}</td>)}
            <td className="n">{fmtNum(s.next_split.reduce((a: number, x: any) => a + (x.annual_interest || 0), 0), 2)}</td>
            <td className="n">{fmtNum(s.next_split.find((x: any) => x.target === "common")?.new_shares, 3)}</td></tr>)}</tbody></table>
      </div>
    </>
  );
}

function PercentOfSales({ co, base }: any) {
  const [p, setP] = useState<any>(() => ({ s1: base.sales, s2: base.sales ? Math.round(base.sales * 1.2) : 0, profit_margin: base.profit_margin ?? 0.1,
    payout: base.payout ?? 0, afn_target: "st_debt", bs_lines: base.bs_lines }));
  const [res, setRes] = useState<any>(null);
  const [err, setErr] = useState("");
  const set = (k: string) => (v: any) => setP({ ...p, [k]: v });
  const run = async () => { setErr(""); try { setRes(await api.post(`/api/companies/${co.id}/forecast/percent-of-sales`, p)); } catch (e: any) { setErr(e.message); } };
  const b = base.benchmarks;
  return (
    <>
      <div className="panel">
        <h2>Percentage of sales method (Lecture 6)</h2>
        <p className="small muted">Lines marked “grows with sales” keep their % of sales; retained earnings grow by margin × new sales × (1 − payout); everything else is unchanged.
          AFN = A/S1·ΔS − L/S1·ΔS − P·S2·(1 − D).</p>
        <div className="grid g4">
          <label>Actual sales S1<br /><Num v={p.s1} set={set("s1")} /></label>
          <label>Proposed sales S2<br /><Num v={p.s2} set={set("s2")} /></label>
          <label>Net profit margin %<br /><Num v={p.profit_margin} set={set("profit_margin")} pct /></label>
          <label>Dividend payout %<br /><Num v={p.payout} set={set("payout")} pct /></label>
          <label>AFN financed by<br /><select value={p.afn_target} onChange={(e) => set("afn_target")(e.target.value)}>
            <option value="st_debt">Short-term debt</option><option value="lt_debt">Long-term debt</option><option value="equity">Equity</option></select></label>
        </div>
        <details style={{ marginTop: 10 }}><summary>Balance-sheet lines from {base.year}</summary><LinesEditor lines={p.bs_lines} setLines={set("bs_lines")} mode="bs" /></details>
        <div className="row" style={{ marginTop: 10 }}><button className="btn pri" onClick={run}>Calculate</button></div>
        {err && <div className="badbox" style={{ marginTop: 8 }}>{err}</div>}
      </div>
      {res && <>
        <div className="grid g4">
          <div className="kpi"><div className="l">Financial sources needed (AFN)</div><div className="v">{fmtNum(res.afn, 1)}</div><div className="s">formula check: {fmtNum(res.afn_formula, 1)}</div></div>
          <div className="kpi"><div className="l">Sales with no external finance (AFN = 0)</div><div className="v">{res.sustainable_sales == null ? "n/m" : fmtNum(res.sustainable_sales, 1)}</div></div>
          <div className="kpi"><div className="l">Current ratio before → after</div><div className="v">{fmtNum(res.ratios.current_ratio_before, 2)} → {fmtNum(res.ratios.current_ratio_after, 2)}</div>
            <div className="s">{b.current_ratio ? `benchmark ${b.current_ratio.value} (${b.current_ratio.source})` : "no benchmark set"}</div></div>
          <div className="kpi"><div className="l">Debt ratio before → after</div><div className="v">{fmtPct(res.ratios.debt_ratio_before)} → {fmtPct(res.ratios.debt_ratio_after)}</div>
            <div className="s">{b.debt_ratio ? `benchmark ${fmtPct(b.debt_ratio.value)} (${b.debt_ratio.source})` : "no benchmark set"}</div></div>
        </div>
        <div className="panel" style={{ marginTop: 16 }}>
          <p className="small mono">{res.formula_text} = {fmtNum(res.afn_formula, 2)}</p>
          <table><thead><tr><th>Line</th><th className="n">Actual</th><th className="n">% of S1</th><th className="n">Projected</th></tr></thead>
            <tbody>{res.rows.map((r: any) => <tr key={r.name}><td>{r.name}{r.spontaneous ? " *" : ""}</td><td className="n">{fmtNum(r.actual, 1)}</td>
              <td className="n">{r.pct_of_sales == null ? "—" : fmtPct(r.pct_of_sales)}</td><td className="n">{fmtNum(r.projected, 1)}</td></tr>)}
              <tr><td><b>Total assets</b></td><td className="n">{fmtNum(res.total_assets_actual, 1)}</td><td /><td className="n"><b>{fmtNum(res.total_assets_projected, 1)}</b></td></tr>
              <tr><td><b>Liabilities & equity before new finance</b></td><td /><td /><td className="n"><b>{fmtNum(res.claims_projected, 1)}</b></td></tr></tbody></table>
          <p className="small muted">* grows with sales. Decision (Lecture 6): compare the ratios after financing with the industry average before accepting the growth plan.</p>
        </div>
      </>}
    </>
  );
}

function BreakEven({ base }: any) {
  const [mode, setMode] = useState(base.fixed_costs != null ? "value" : "units");
  const [p, setP] = useState<any>({ fc: base.fixed_costs ?? 100000, sales: base.sales, vc: base.variable_costs, price: 2, avc: 1.5, units: 350000 });
  const [res, setRes] = useState<any>(null);
  const [err, setErr] = useState("");
  const set = (k: string) => (v: any) => setP({ ...p, [k]: v });
  const run = async () => {
    setErr("");
    const body = mode === "units" ? { fc: p.fc, price: p.price, avc: p.avc, units: p.units } : { fc: p.fc, sales: p.sales, vc: p.vc };
    try { setRes(await api.post("/api/forecast/breakeven", body)); } catch (e: any) { setErr(e.message); }
  };
  useEffect(() => { run(); }, [mode]);
  return (
    <>
      <div className="panel">
        <h2>Break-even & operating leverage (Lecture 8)</h2>
        <div className="row" style={{ marginBottom: 8 }}>
          <button className={`btn sm ${mode === "units" ? "pri" : ""}`} onClick={() => setMode("units")}>Units: Q = FC / (P − AVC)</button>
          <button className={`btn sm ${mode === "value" ? "pri" : ""}`} onClick={() => setMode("value")}>Value: TFC / (1 − VC / Sales)</button>
        </div>
        <div className="grid g4">
          <label>Total fixed costs<br /><Num v={p.fc} set={set("fc")} /></label>
          {mode === "units" ? <>
            <label>Selling price per unit<br /><Num v={p.price} set={set("price")} /></label>
            <label>Average variable cost per unit<br /><Num v={p.avc} set={set("avc")} /></label>
            <label>Current units produced<br /><Num v={p.units} set={set("units")} /></label>
          </> : <>
            <label>Sales<br /><Num v={p.sales} set={set("sales")} /></label>
            <label>Total variable costs<br /><Num v={p.vc} set={set("vc")} /></label>
          </>}
        </div>
        {mode === "value" && base.fixed_costs != null && <p className="small muted">Pre-filled from Additional_Info ({base.year}).</p>}
        <div className="row" style={{ marginTop: 10 }}><button className="btn pri" onClick={run}>Calculate</button></div>
        {err && <div className="badbox" style={{ marginTop: 8 }}>{err}</div>}
      </div>
      {res && <>
        <div className="grid g4">
          {res.bep_units != null && <div className="kpi"><div className="l">Break-even units</div><div className="v">{fmtNum(res.bep_units)}</div><div className="s">value {fmtNum(res.bep_value)}</div></div>}
          {res.bep_sales != null && <div className="kpi"><div className="l">Break-even sales</div><div className="v">{fmtNum(res.bep_sales)}</div><div className="s">contribution margin {fmtPct(res.cm_ratio)}</div></div>}
          {res.operating_profit != null && <div className="kpi"><div className="l">Operating profit at current level</div><div className={`v ${res.operating_profit < 0 ? "neg" : ""}`}>{fmtNum(res.operating_profit)}</div></div>}
          {res.margin_of_safety != null && <div className="kpi"><div className="l">Margin of safety</div><div className="v">{fmtPct(res.margin_of_safety)}</div></div>}
          {res.dol != null && <div className="kpi"><div className="l">Degree of operating leverage</div><div className="v">{fmtNum(res.dol, 2)}×</div>
            <div className="s">1% more sales → {fmtNum(res.dol, 2)}% more operating profit</div></div>}
        </div>
        <div className="panel" style={{ marginTop: 16 }}><h2>Break-even chart</h2>
          <div style={{ height: 300 }}><ResponsiveContainer><LineChart data={res.chart}><CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis dataKey="q" tickFormatter={(x) => fmtNum(x)} /><YAxis tickFormatter={(x) => fmtNum(x)} /><Tooltip formatter={(x: any) => fmtNum(x)} /><Legend />
            <Line dataKey="tr" name="Total revenue" stroke={PALETTE[0]} strokeWidth={2} dot={false} />
            <Line dataKey="tc" name="Total cost" stroke={PALETTE[4]} strokeWidth={2} dot={false} />
            <Line dataKey="fc" name="Fixed cost" stroke={PALETTE[5]} strokeDasharray="5 4" dot={false} />
            {(res.bep_units ?? res.bep_sales) != null && <ReferenceLine x={res.bep_units ?? res.bep_sales} stroke={PALETTE[2]} label="BEP" />}
          </LineChart></ResponsiveContainer></div>
          <p className="small muted">High fixed costs relative to total costs mean high operating leverage: a small change in sales causes a large change in operating profit.</p></div>
      </>}
    </>
  );
}

const LECTURE7 = {
  months: ["Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun"], sales: [300, 350, 250, 200, 250, 300, 350, 380], other: [0, 0, 0, 40, 0, 0, 0, 0],
  payments: { Purchases: [0, 0, 100, 80, 100, 120, 140, 150], Salaries: [0, 0, 80, 80, 90, 90, 95, 100], Overheads: [0, 0, 50, 50, 50, 50, 50, 50],
    "Capital investment": [0, 0, 0, 150, 20, 0, 0, 20], Dividends: [0, 0, 0, 0, 50, 0, 0, 0], Taxes: [0, 0, 30, 0, 0, 30, 0, 0] } as Record<string, number[]>,
};

function CashBudget() {
  const [p, setP] = useState<any>({ ...LECTURE7, cash_pct: 0.1, lags: [0.9, 0.1], opening: 100, min_cash: 75, show_from: 2 });
  const [res, setRes] = useState<any>(null);
  const [err, setErr] = useState("");
  const run = async (q = p) => {
    setErr("");
    try { setRes(await api.post("/api/forecast/cash-budget", { months: q.months, sales: q.sales, cash_pct: q.cash_pct, lags: q.lags, other_receipts: q.other, payments: q.payments, opening: q.opening, min_cash: q.min_cash, show_from: q.show_from })); }
    catch (e: any) { setErr(e.message); }
  };
  useEffect(() => { run(); }, []);
  const cell = (arr: number[], i: number, f: (a: number[]) => void) => <Num w={70} v={arr[i]} set={(v) => { const a = [...arr]; a[i] = Number(v || 0); f(a); }} />;
  return (
    <>
      <div className="panel">
        <h2>Cash-flow forecast / master budget (Lecture 7)</h2>
        <p className="small muted">Pre-filled with the lecture example. The first {p.show_from} month(s) are history used only for collections. Receipts = cash sales + collections of earlier credit sales + other receipts.</p>
        <div className="row" style={{ marginBottom: 8 }}>
          <label>Cash sales % <Num w={70} v={p.cash_pct} pct set={(v) => setP({ ...p, cash_pct: v })} /></label>
          <label>Credit collected after 1 month % <Num w={70} v={p.lags[0]} pct set={(v) => setP({ ...p, lags: [v, p.lags[1]] })} /></label>
          <label>after 2 months % <Num w={70} v={p.lags[1]} pct set={(v) => setP({ ...p, lags: [p.lags[0], v] })} /></label>
          <label>Opening cash <Num w={80} v={p.opening} set={(v) => setP({ ...p, opening: v })} /></label>
          <label>Minimum cash <Num w={80} v={p.min_cash} set={(v) => setP({ ...p, min_cash: v })} /></label>
          <label>History months <Num w={60} v={p.show_from} set={(v) => setP({ ...p, show_from: v })} /></label>
        </div>
        <div className="scroll"><table>
          <thead><tr><th>Input</th>{p.months.map((m: string, i: number) => <th key={i}><input type="text" style={{ width: 70 }} value={m} onChange={(e) => { const a = [...p.months]; a[i] = e.target.value; setP({ ...p, months: a }); }} /></th>)}</tr></thead>
          <tbody>
            <tr><td>Sales</td>{p.months.map((_: any, i: number) => <td key={i}>{cell(p.sales, i, (a) => setP({ ...p, sales: a }))}</td>)}</tr>
            <tr><td>Other receipts (e.g. asset sales)</td>{p.months.map((_: any, i: number) => <td key={i}>{cell(p.other, i, (a) => setP({ ...p, other: a }))}</td>)}</tr>
            {Object.keys(p.payments).map((k) => <tr key={k}><td>{k}</td>{p.months.map((_: any, i: number) => <td key={i}>{cell(p.payments[k], i, (a) => setP({ ...p, payments: { ...p.payments, [k]: a } }))}</td>)}</tr>)}
          </tbody></table></div>
        <div className="row" style={{ marginTop: 10 }}>
          <button className="btn" onClick={() => setP({ ...p, months: [...p.months, `M${p.months.length + 1}`], sales: [...p.sales, 0], other: [...p.other, 0],
            payments: Object.fromEntries(Object.entries(p.payments).map(([k, v]: any) => [k, [...v, 0]])) })}>+ Month</button>
          <button className="btn" onClick={() => { const k = window.prompt("Payment line name:"); if (k) setP({ ...p, payments: { ...p.payments, [k]: p.months.map(() => 0) } }); }}>+ Payment line</button>
          <button className="btn pri" onClick={() => run()}>Calculate</button></div>
        {err && <div className="badbox" style={{ marginTop: 8 }}>{err}</div>}
      </div>
      {res && <div className="panel">
        <h2>Forecasted cash-flow statement</h2>
        <div className="scroll"><table>
          <thead><tr><th /> {res.rows.map((r: any) => <th key={r.month} className="n">{r.month}</th>)}</tr></thead>
          <tbody>
            <tr><td>Cash sales</td>{res.rows.map((r: any) => <td key={r.month} className="n">{fmtNum(r.cash_sales, 1)}</td>)}</tr>
            {res.rows[0]?.collections.map((_: any, k: number) => <tr key={k}><td>Collections — {k + 1} month credit</td>{res.rows.map((r: any) => <td key={r.month} className="n">{fmtNum(r.collections[k], 1)}</td>)}</tr>)}
            <tr><td>Other receipts</td>{res.rows.map((r: any) => <td key={r.month} className="n">{fmtNum(r.other_receipts, 1)}</td>)}</tr>
            <tr><td><b>Revenues (receipts)</b></td>{res.rows.map((r: any) => <td key={r.month} className="n"><b>{fmtNum(r.receipts, 1)}</b></td>)}</tr>
            <tr><td><b>Expenditures</b></td>{res.rows.map((r: any) => <td key={r.month} className="n"><b>{fmtNum(r.total_payments, 1)}</b></td>)}</tr>
            <tr><td>Net</td>{res.rows.map((r: any) => <td key={r.month} className={`n ${r.net < 0 ? "neg" : ""}`}>{fmtNum(r.net, 1)}</td>)}</tr>
            <tr><td>Balance</td>{res.rows.map((r: any) => <td key={r.month} className="n">{fmtNum(r.closing_balance, 1)}</td>)}</tr>
            <tr><td>Minimum cash</td>{res.rows.map((r: any) => <td key={r.month} className="n">({fmtNum(r.min_cash, 1)})</td>)}</tr>
            <tr><td><b>Surplus / (deficit)</b></td>{res.rows.map((r: any) => <td key={r.month} className={`n ${r.surplus_deficit < 0 ? "neg" : "pos"}`}><b>{fmtNum(r.surplus_deficit, 1)}</b></td>)}</tr>
          </tbody></table></div>
        <p className="small muted">Largest deficit: {fmtNum(res.peak_deficit, 1)} — the short-term financing to arrange in advance.</p>
      </div>}
    </>
  );
}
