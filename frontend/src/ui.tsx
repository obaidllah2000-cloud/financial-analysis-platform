import { useEffect, useState } from "react";
import { api, fmtNum } from "./api";

const STATUS_LABEL: Record<string, string> = {
  verified: "verified", approved_assumption: "approved assumption", provisional: "provisional", needs_info: "needs info", invalid: "invalid",
  info_requested: "info requested",
};
export function Chip({ s, label }: { s: string; label?: string }) {
  const cls = (s || "").split(" ")[0];
  return <span className={`chip c-${cls}`}>{label ?? STATUS_LABEL[s] ?? s}</span>;
}

export function Modal({ onClose, children }: { onClose: () => void; children: any }) {
  useEffect(() => { const h = (e: KeyboardEvent) => e.key === "Escape" && onClose(); window.addEventListener("keydown", h); return () => window.removeEventListener("keydown", h); }, []);
  return <div className="modal-bg" onClick={onClose}><div className="modal" onClick={(e) => e.stopPropagation()}>
    <div style={{ textAlign: "end" }}><button className="btn sm" onClick={onClose}>✕</button></div>{children}</div></div>;
}

/** Drill-down from a ratio result to formula → aggregates → original accounts → assumptions. */
export function TraceModal({ cid, ratio, year, onClose }: { cid: number; ratio: string; year: number; onClose: () => void }) {
  const [t, setT] = useState<any>(null);
  useEffect(() => { api.get(`/api/companies/${cid}/trace/${ratio}/${year}`).then(setT); }, [ratio, year]);
  return (
    <Modal onClose={onClose}>
      {!t ? <p>Loading…</p> : <>
        <h2>{t.ratio.name_en} — {year}</h2>
        <dl className="kv">
          <dt>Formula</dt><dd className="mono">{t.ratio.formula}</dd>
          <dt>Result</dt><dd><b>{t.cell.display}</b> <Chip s={t.cell.status} /> <span className="small muted">{t.status_text}</span></dd>
          <dt>Methodology</dt><dd>{t.ratio.methodology} · {t.ratio.source}</dd>
          {t.cell.reasons.length > 0 && <><dt>Why this status</dt><dd>{t.cell.reasons.join(" · ")}</dd></>}
          {t.cell.notes.length > 0 && <><dt>Calculation notes</dt><dd>{t.cell.notes.map((n: string, i: number) => <div key={i}>{n}</div>)}</dd></>}
        </dl>
        <h3 style={{ fontSize: 13, color: "var(--muted)" }}>Assumptions applied</h3>
        {Object.keys(t.assumption_values).length === 0 ? <p className="small muted">No assumptions involved in this calculation.</p> :
          <table><tbody>{Object.entries(t.assumption_values).map(([k, v]: any) => <tr key={k}><td className="mono small">{k}</td><td>{v}</td><td><Chip s={t.assumption_status[k]} /></td></tr>)}</tbody></table>}
        <h3 style={{ fontSize: 13, color: "var(--muted)" }}>Inputs and underlying accounts</h3>
        {t.inputs.map((i: any) => (
          <div key={i.key} className="card">
            <div className="row"><b>{i.label}</b><span className="mono">{fmtNum(i.value, 2)}</span>
              {i.detail && <span className="small muted">source: {i.detail.source} · {i.detail.formula}</span>}
              {i.detail?.provisional && <Chip s="provisional" />}</div>
            {i.detail?.components?.length > 0 && (
              <table style={{ marginTop: 6 }}><thead><tr><th>Original account / component</th><th>Classification used</th><th className="n">Original value</th><th className="n">Normalized</th><th>Status</th></tr></thead>
                <tbody>{i.detail.components.map((c: any, k: number) => (
                  <tr key={k}><td>{c.account || c.label || c.additional || c.aggregate}{c.note && <div className="small muted">{c.note}</div>}</td>
                    <td className="small mono">{c.category || (c.aggregate ? "aggregate" : c.additional ? "Additional_Info" : "")}</td>
                    <td className="n">{fmtNum(c.original ?? c.value, 2)}</td><td className="n">{fmtNum(c.normalized ?? (c.value !== undefined ? c.value * (c.sign ?? 1) : undefined), 2)}</td>
                    <td>{c.status && <Chip s={c.status} />}</td></tr>))}</tbody></table>)}
          </div>))}
      </>}
    </Modal>
  );
}
