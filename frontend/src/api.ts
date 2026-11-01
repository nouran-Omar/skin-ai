import type { AnalysisResult, Answers, Question } from "./types";

const BASE: string = import.meta.env.VITE_API_URL ?? "";

async function parse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try { const j = await res.json(); if (typeof j.detail === "string") detail = j.detail; } catch { /* keep default */ }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export type Account = { id: string; email: string; created_at: string };
export type SavedAnalysis = { id: string; created_at: string; top_name: string; risk: string; probability: number; urgency: string; demo: boolean };
export type ProgressEntry = { id: string; lesion_id: string; recorded_at: string; note: string; analysis_id?: string | null };
const jsonRequest = (method: string, body?: unknown) => ({ method, credentials: "include" as RequestCredentials,
  headers: body === undefined ? undefined : { "Content-Type": "application/json" }, body: body === undefined ? undefined : JSON.stringify(body) });
export const register = (email: string, password: string) => fetch(`${BASE}/api/auth/register`, jsonRequest("POST", { email, password })).then(parse<Account>);
export const login = (email: string, password: string) => fetch(`${BASE}/api/auth/login`, jsonRequest("POST", { email, password })).then(parse<Account>);
export const logout = () => fetch(`${BASE}/api/auth/logout`, jsonRequest("POST")).then(parse<{ ok: boolean }>);
export const currentAccount = () => fetch(`${BASE}/api/auth/me`, { credentials: "include" }).then(parse<Account>);
export const saveAnalysis = (id: string) => fetch(`${BASE}/api/history/${id}`, jsonRequest("POST")).then(parse<SavedAnalysis>);
export const fetchHistory = () => fetch(`${BASE}/api/history`, { credentials: "include" }).then(parse<SavedAnalysis[]>);
export const deleteHistory = (id: string) => fetch(`${BASE}/api/history/${id}`, jsonRequest("DELETE")).then(parse<{ ok: boolean }>);
export const fetchProgress = () => fetch(`${BASE}/api/progress`, { credentials: "include" }).then(parse<ProgressEntry[]>);
export const addProgress = (payload: { lesion_id: string; recorded_at: string; note: string }) => fetch(`${BASE}/api/progress`, jsonRequest("POST", payload)).then(parse<ProgressEntry>);
export const deleteProgress = (id: string) => fetch(`${BASE}/api/progress/${id}`, jsonRequest("DELETE")).then(parse<{ ok: boolean }>);
export type AssistantTurn = { role: "user" | "assistant"; content: string };
export type AssistantSource = { title: string; url: string };
export type AssistantResponse = { answer: string; disclaimer: string; sources: AssistantSource[]; mode: "conversation" | "retrieval" | "generated" };
export type AssistantGuide = { topic: string; title: string; guidance: string; source: AssistantSource };
export const fetchAssistantGuide = (topic: string, language: "en" | "ar") =>
  fetch(`${BASE}/api/assistant/guide/${encodeURIComponent(topic)}?language=${language}`).then(parse<AssistantGuide>);
export const sendAssistantMessage = (message: string, language: "en" | "ar", history: AssistantTurn[] = [], allowGeneration = false) =>
  fetch(`${BASE}/api/assistant/chat`, jsonRequest("POST", { message, language, history, allow_generation: allowGeneration })).then(parse<AssistantResponse>);
export const acneGuideUrl = (_language: "en" | "ar") => `${BASE}/api/reports/acne-guide?language=en`;

export const fetchQuiz = () => fetch(`${BASE}/api/quiz`).then(parse<Question[]>);
export const fetchHealth = () => fetch(`${BASE}/api/health`).then(parse<{ demo: boolean }>);
export const reportUrl = (id: string) => `${BASE}/api/report/${id}`;

export async function analyze(file: File, answers: Answers): Promise<AnalysisResult> {
  const form = new FormData();
  form.append("image", file);
  form.append("answers", JSON.stringify(answers));
  return parse<AnalysisResult>(await fetch(`${BASE}/api/analyze`, { method: "POST", body: form, credentials: "include" }));
}
