import { useEffect, useState, type FormEvent } from "react";
import { addProgress, currentAccount, deleteHistory, deleteProgress, fetchHistory, fetchProgress, login, logout, register, saveAnalysis, type Account, type ProgressEntry, type SavedAnalysis } from "../api";
import { localizeApiError, translatedContent, useLanguage } from "../i18n";

export default function AccountPanel({ analysisId }: { analysisId?: string }) {
  const { language, t } = useLanguage();
  const [account, setAccount] = useState<Account | null>(null);
  const [items, setItems] = useState<SavedAnalysis[]>([]);
  const [entries, setEntries] = useState<ProgressEntry[]>([]);
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [lesion, setLesion] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const refresh = async () => {
    const [history, progress] = await Promise.all([fetchHistory(), fetchProgress()]);
    setItems(history);
    setEntries(progress);
  };
  useEffect(() => {
    currentAccount().then((current) => { setAccount(current); return refresh(); }).catch(() => {});
  }, []);

  const showError = (value: unknown, fallback: string) => setError(localizeApiError(value instanceof Error ? value.message : fallback, language));
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError(""); setMessage("");
    try {
      const signedIn = mode === "login" ? await login(email, password) : await register(email, password);
      setAccount(signedIn); setPassword(""); await refresh();
    } catch (cause) { showError(cause, "Request failed"); }
  };
  const save = async () => {
    if (!analysisId) return;
    setError(""); setMessage("");
    try { await saveAnalysis(analysisId); await refresh(); setMessage(t("Saved summary to your account. Images are not saved.")); }
    catch (cause) { showError(cause, "Could not save"); }
  };
  const track = async (event: FormEvent) => {
    event.preventDefault(); setError(""); setMessage("");
    try { await addProgress({ lesion_id: lesion, recorded_at: new Date().toLocaleDateString("en-CA"), note }); setNote(""); await refresh(); }
    catch (cause) { showError(cause, "Could not save"); }
  };
  const signOut = async () => {
    setError("");
    try { await logout(); setAccount(null); setItems([]); setEntries([]); }
    catch (cause) { showError(cause, "Request failed"); }
  };
  const removeSaved = async (id: string) => {
    setError("");
    try { await deleteHistory(id); await refresh(); }
    catch (cause) { showError(cause, "Could not save"); }
  };
  const removeProgress = async (id: string) => {
    setError("");
    try { await deleteProgress(id); await refresh(); }
    catch (cause) { showError(cause, "Could not save"); }
  };

  return (
    <section className="panel overflow-hidden p-0 shadow-sm" aria-labelledby="account-title">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-line bg-gradient-to-r from-brand-50 to-white p-5 dark:border-line-dark dark:from-white/5 dark:to-transparent sm:p-7">
        <div className="max-w-2xl">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-mint-700 dark:text-mint-300">{t("Account")}</p>
          <h2 id="account-title" className="mt-2 text-2xl font-semibold sm:text-3xl">{t("Skin progress journal")}</h2>
          <p className="mt-2 text-sm leading-6 text-brand-600 dark:text-brand-200">{t("Save summaries and progress notes. Uploaded photos are not stored in your account.")}</p>
        </div>
        {account && <button className="btn-ghost" onClick={signOut}>{t("Sign out")}</button>}
      </div>
      <div className="p-5 sm:p-7">
        {error && <p role="alert" className="mb-4 rounded-xl bg-coral-100 px-4 py-3 text-sm text-coral-700">{error}</p>}
        {message && <p role="status" className="mb-4 rounded-xl bg-mint-100 px-4 py-3 text-sm text-mint-800">{message}</p>}
        {!account ? (
          <div className="mx-auto max-w-3xl">
            <p className="text-sm leading-6 text-brand-600 dark:text-brand-200">{t("Sign in or create an account to save analysis summaries and use skin progress tracking.")}</p>
            <div className="mt-5 inline-flex rounded-xl bg-brand-50 p-1 dark:bg-white/5" role="group" aria-label={t("Choose sign in or create account")}>
              <button type="button" onClick={() => { setMode("login"); setError(""); }} aria-pressed={mode === "login"} className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${mode === "login" ? "bg-white text-brand-900 shadow-sm dark:bg-panel-dark dark:text-white" : "text-brand-600 hover:text-brand-900 dark:text-brand-200"}`}>{t("Sign in")}</button>
              <button type="button" onClick={() => { setMode("register"); setError(""); }} aria-pressed={mode === "register"} className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${mode === "register" ? "bg-white text-brand-900 shadow-sm dark:bg-panel-dark dark:text-white" : "text-brand-600 hover:text-brand-900 dark:text-brand-200"}`}>{t("Create account")}</button>
            </div>
            <h3 className="mt-5 text-xl font-semibold">{t(mode === "login" ? "Welcome back" : "Create your SkinAI account")}</h3>
            <form onSubmit={submit} className="mt-4 grid gap-4 sm:grid-cols-2">
              <label className="grid gap-2 text-sm font-medium sm:col-span-1"><span>{t("Email address")}</span><input dir="ltr" className="min-h-12 rounded-xl border border-line bg-white px-4 text-start shadow-sm outline-none transition placeholder:text-brand-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/10 dark:border-line-dark dark:bg-white/[0.03]" type="email" autoComplete="email" required maxLength={254} placeholder="name@example.com" value={email} onChange={(event) => setEmail(event.target.value)} /></label>
              <label className="grid gap-2 text-sm font-medium sm:col-span-1"><span>{t("Password")}</span><input dir="ltr" className="min-h-12 rounded-xl border border-line bg-white px-4 text-start shadow-sm outline-none transition placeholder:text-brand-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/10 dark:border-line-dark dark:bg-white/[0.03]" type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} required minLength={12} maxLength={128} placeholder={t("Password (12+ characters)")} value={password} onChange={(event) => setPassword(event.target.value)} /></label>
              <div className="flex flex-wrap items-center justify-between gap-3 sm:col-span-2">
                <p className="text-xs text-brand-500 dark:text-brand-300">{t("Your account is private to you.")}</p>
                <button className="btn-primary min-w-44" type="submit">{t(mode === "login" ? "Sign in" : "Create account")}</button>
              </div>
            </form>
          </div>
        ) : (
          <>
            <p dir="ltr" className="text-sm text-start text-brand-600 dark:text-brand-200">{account.email}</p>
            {analysisId && <button className="btn-primary mt-4" onClick={save}>{t("Save this analysis summary")}</button>}
            <div className="mt-7 grid gap-7 lg:grid-cols-2">
              <div><h3 className="text-lg font-semibold">{t("Saved summaries")}</h3>{items.length === 0 ? <p className="mt-2 text-sm text-brand-500">{t("No saved analyses yet.")}</p> : <ul className="mt-3 space-y-2">{items.map((item) => <li key={item.id} className="flex flex-wrap items-center justify-between gap-2 rounded-xl bg-brand-50 p-3 text-sm dark:bg-white/5"><span>{translatedContent(item.top_name, language)} · {new Date(item.created_at).toLocaleDateString(language)}</span><button className="text-coral-500 underline underline-offset-2" onClick={() => removeSaved(item.id)}>{t("Delete")}</button></li>)}</ul>}</div>
              <div><h3 className="text-lg font-semibold">{t("Skin progress")}</h3><form onSubmit={track} className="mt-3 space-y-3"><input dir="auto" className="min-h-12 w-full rounded-xl border border-line bg-transparent px-4 py-3 dark:border-line-dark" required maxLength={60} placeholder={t("Spot label, e.g. left arm")} value={lesion} onChange={(event) => setLesion(event.target.value)} /><textarea dir="auto" className="min-h-24 w-full rounded-xl border border-line bg-transparent px-4 py-3 dark:border-line-dark" maxLength={1000} placeholder={t("Optional progress note")} value={note} onChange={(event) => setNote(event.target.value)} /><button className="btn-ghost" type="submit">{t("Add dated entry")}</button></form>
                <ul className="mt-4 space-y-2">{entries.map((entry) => <li key={entry.id} className="rounded-xl bg-brand-50 p-3 text-sm dark:bg-white/5"><div className="flex flex-wrap items-center justify-between gap-2"><b dir="auto">{entry.lesion_id}</b><span dir="ltr">{entry.recorded_at}</span><button className="text-coral-500 underline underline-offset-2" onClick={() => removeProgress(entry.id)}>{t("Delete")}</button></div>{entry.note && <p dir="auto" className="mt-2 whitespace-pre-wrap">{entry.note}</p>}</li>)}</ul>
              </div>
            </div>
          </>
        )}
        <p className="mt-6 border-t border-line pt-4 text-xs leading-5 text-brand-500 dark:border-line-dark dark:text-brand-300">{t("Only save information you are comfortable keeping in this account. Use a nickname for each spot; avoid names or other identifying details.")}</p>
      </div>
    </section>
  );
}
