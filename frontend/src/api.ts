import type { AnalysisResult, Answers, Question } from "./types";

// Leave empty by default: Vercel rewrites /api to the Hugging Face Space and
// the local Vite server proxies /api to FastAPI on port 8000.
const configuredBase = import.meta.env.VITE_API_URL || import.meta.env.REACT_APP_API_URL || "";
export const API_BASE = configuredBase.replace(/\/+$/, "");

export class ApiError extends Error {
  constructor(message: string, readonly status?: number, readonly code?: "network" | "timeout" | "server") {
    super(message);
    this.name = "ApiError";
  }
}

async function request(url: string, init: RequestInit = {}, timeoutMs = 45_000): Promise<Response> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("The request took too long. The screening service may be waking up; wait a moment and try again.", undefined, "timeout");
    }
    throw new ApiError("Could not connect to the SkinAI service. It may be starting, or the API URL or browser access settings may need checking. Please try again shortly.", undefined, "network");
  } finally {
    window.clearTimeout(timeout);
  }
}

async function parse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = "";
    try { const j = await res.json(); if (typeof j.detail === "string") detail = j.detail; } catch { /* use status based guidance */ }
    if (res.status === 502 || res.status === 503 || res.status === 504) {
      throw new ApiError("The SkinAI service is starting or temporarily unavailable. Please wait a minute and try again.", res.status, "server");
    }
    if (res.status >= 500) {
      throw new ApiError("The SkinAI service encountered a problem. Please try again shortly. If it keeps happening, contact support with the error code.", res.status, "server");
    }
    throw new ApiError(detail || `The request could not be completed (HTTP ${res.status}). Check your details and try again.`, res.status);
  }
  return res.json() as Promise<T>;
}

export type Account = { id: string; email: string; created_at: string };
export type SavedAnalysis = { id: string; created_at: string; top_name: string; risk: string; probability: number; urgency: string; demo: boolean };
export type ProgressEntry = { id: string; lesion_id: string; recorded_at: string; note: string; analysis_id?: string | null };
const jsonRequest = (method: string, body?: unknown) => ({ method, credentials: "include" as RequestCredentials,
  headers: body === undefined ? undefined : { "Content-Type": "application/json" }, body: body === undefined ? undefined : JSON.stringify(body) });
export const register = (email: string, password: string) => request(`${API_BASE}/api/auth/register`, jsonRequest("POST", { email, password })).then(parse<Account>);
export const login = (email: string, password: string) => request(`${API_BASE}/api/auth/login`, jsonRequest("POST", { email, password })).then(parse<Account>);
export const logout = () => request(`${API_BASE}/api/auth/logout`, jsonRequest("POST")).then(parse<{ ok: boolean }>);
export const deleteAccount = () => request(`${API_BASE}/api/auth/me`, jsonRequest("DELETE")).then(parse<{ ok: boolean }>);
export const currentAccount = () => request(`${API_BASE}/api/auth/me`, { credentials: "include" }).then(parse<Account>);
export const saveAnalysis = (id: string) => request(`${API_BASE}/api/history/${id}`, jsonRequest("POST")).then(parse<SavedAnalysis>);
export const fetchHistory = () => request(`${API_BASE}/api/history`, { credentials: "include" }).then(parse<SavedAnalysis[]>);
export const deleteHistory = (id: string) => request(`${API_BASE}/api/history/${id}`, jsonRequest("DELETE")).then(parse<{ ok: boolean }>);
export const fetchProgress = () => request(`${API_BASE}/api/progress`, { credentials: "include" }).then(parse<ProgressEntry[]>);
export const addProgress = (payload: { lesion_id: string; recorded_at: string; note: string }) => request(`${API_BASE}/api/progress`, jsonRequest("POST", payload)).then(parse<ProgressEntry>);
export const deleteProgress = (id: string) => request(`${API_BASE}/api/progress/${id}`, jsonRequest("DELETE")).then(parse<{ ok: boolean }>);
export type AssistantTurn = { role: "user" | "assistant"; content: string };
export type AssistantSource = { title: string; url: string };
export type AssistantResponse = { answer: string; disclaimer: string; sources: AssistantSource[]; mode: "conversation" | "retrieval" | "generated" };
export type AssistantGuide = { topic: string; title: string; guidance: string; source: AssistantSource };
export const fetchAssistantGuide = (topic: string, language: "en" | "ar") =>
  request(`${API_BASE}/api/assistant/guide/${encodeURIComponent(topic)}?language=${language}`).then(parse<AssistantGuide>);
export const sendAssistantMessage = (message: string, language: "en" | "ar", history: AssistantTurn[] = [], allowGeneration = false) =>
  request(`${API_BASE}/api/assistant/chat`, jsonRequest("POST", { message, language, history, allow_generation: allowGeneration })).then(parse<AssistantResponse>);
export const acneGuideUrl = (language: "en" | "ar") => `${API_BASE}/api/reports/acne-guide?language=${language}`;

export const fetchQuiz = () => request(`${API_BASE}/api/quiz`).then(parse<Question[]>);
export const fetchHealth = () => request(`${API_BASE}/api/health`).then(parse<{ demo: boolean }>);
export const reportUrl = (id: string, language: "en" | "ar" = "en") => `${API_BASE}/api/report/${id}?language=${language}`;

export async function analyze(file: File, answers: Answers): Promise<AnalysisResult> {
  const form = new FormData();
  form.append("image", file);
  form.append("answers", JSON.stringify(answers));
  return parse<AnalysisResult>(await request(`${API_BASE}/api/analyze`, { method: "POST", body: form, credentials: "include" }, 180_000));
}
