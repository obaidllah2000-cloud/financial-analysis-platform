let userId = Number(localStorage.getItem("fap_user") || "0") || 0;
export const setUser = (id: number) => { userId = id; try { localStorage.setItem("fap_user", String(id)); } catch { /* ignore */ } };
export const getUser = () => userId;

export const getLang = (): "en" | "ar" => { try { return localStorage.getItem("fap_lang") === "ar" ? "ar" : "en"; } catch { return "en"; } };
/** Adds the selected language so the server returns texts (never numbers) in that language. */
export const withLang = (url: string) => (url.includes("lang=") ? url : `${url}${url.includes("?") ? "&" : "?"}lang=${getLang()}`);

async function req(method: string, url: string, body?: unknown, isForm = false) {
  url = withLang(url);
  const headers: Record<string, string> = {};
  if (userId) headers["X-User-Id"] = String(userId);
  if (body && !isForm) headers["Content-Type"] = "application/json";
  const r = await fetch(url, { method, headers, body: isForm ? (body as FormData) : body ? JSON.stringify(body) : undefined });
  const text = await r.text();
  const data = text ? (() => { try { return JSON.parse(text); } catch { return text; } })() : null;
  if (r.status === 401 && data?.detail === "login_required") {
    window.dispatchEvent(new Event("fap-login-required"));
    throw new Error("Please sign in.");
  }
  if (!r.ok) {
    const d = data?.detail;
    throw new Error(typeof d === "string" ? d : d?.message || JSON.stringify(d || data));
  }
  return data;
}
export const api = {
  get: (u: string) => req("GET", u),
  post: (u: string, b?: unknown) => req("POST", u, b ?? {}),
  patch: (u: string, b: unknown) => req("PATCH", u, b),
  del: (u: string) => req("DELETE", u),
  upload: (u: string, f: File) => { const fd = new FormData(); fd.append("file", f); return req("POST", u, fd, true); },
};
export const fmtNum = (v: number | null | undefined, d = 0) =>
  v === null || v === undefined ? "—" : v.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
export const fmtPct = (v: number | null | undefined, d = 1) => (v === null || v === undefined ? "—" : `${(v * 100).toFixed(d)}%`);
