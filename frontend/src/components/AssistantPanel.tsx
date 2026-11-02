import { useState, type FormEvent } from "react";
import { ExternalLink, MessageCircle, Send, Sparkles } from "lucide-react";
import { sendAssistantMessage } from "../api";
import { localizeApiError, useLanguage } from "../i18n";

export default function AssistantPanel() {
  const { language, t } = useLanguage();
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<{ question: string; answer: string; disclaimer: string; sources: { title: string; url: string }[]; mode: string }[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [allowGeneration, setAllowGeneration] = useState(false);

  const ask = async (event: FormEvent) => {
    event.preventDefault();
    const text = question.trim();
    if (!text || busy) return;
    setBusy(true);
    setError("");
    try {
      const history = messages.slice(-4).flatMap((message) => [
        { role: "user" as const, content: message.question },
        { role: "assistant" as const, content: message.answer },
      ]);
      const response = await sendAssistantMessage(text, language, history, allowGeneration);
      setMessages((current) => [...current, { question: text, answer: response.answer, disclaimer: response.disclaimer, sources: response.sources ?? [], mode: response.mode }]);
      setQuestion("");
    } catch (error) {
      setError(localizeApiError(error instanceof Error ? error.message : "Could not connect to the SkinAI service. It may be starting, or the API URL or browser access settings may need checking. Please try again shortly.", language));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="panel h-full p-5 sm:p-6" aria-labelledby="assistant-title">
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-brand-100 text-brand-700 dark:bg-white/10 dark:text-mint-300"><MessageCircle size={20} /></span>
        <div>
          <h2 id="assistant-title" className="text-xl font-semibold">{t("Interactive SkinAI Assistant")}</h2>
          <p className="mt-1 text-sm text-brand-500 dark:text-brand-300">{t("Ask about general skin health or acne care. Guided educational responses; not a dermatologist, diagnosis, or treatment plan.")}</p>
        </div>
      </div>
      <div aria-live="polite" className="mt-4 max-h-72 space-y-3 overflow-y-auto">
        {messages.length === 0 && <p className="rounded-xl bg-brand-50 p-3 text-sm text-brand-600 dark:bg-white/5 dark:text-brand-200">{t("Try asking about gentle acne care, or when to get a spot checked.")}</p>}
        {messages.map((message, index) => (
          <div key={`${index}-${message.question}`} className="space-y-2">
            <p dir="auto" className="rounded-xl bg-brand-50 p-3 text-sm dark:bg-white/5"><b>{t("You:")}</b> {message.question}</p>
            <div dir="auto" className="rounded-xl bg-mint-100/60 p-3 text-sm dark:bg-mint-900/30">
              <p><b>SkinAI:</b> {message.answer}</p>
              {message.sources.length > 0 && <div className="mt-3 border-t border-brand-200/60 pt-2 dark:border-white/10"><p className="mb-1 text-xs font-semibold">{t("Sources")}</p><ul className="space-y-1">{message.sources.map((source) => <li key={source.url}><a className="inline-flex items-center gap-1 text-xs underline" href={source.url} target="_blank" rel="noreferrer">{source.title}<ExternalLink size={12} /></a></li>)}</ul></div>}
              {message.mode === "generated" && <p className="mt-2 text-xs">{t("Generated using retrieved references")}</p>}
              <p className="mt-2 text-xs opacity-80">{message.disclaimer}</p>
            </div>
          </div>
        ))}
      </div>
      {error && <p role="alert" className="mt-2 text-sm text-coral-500">{error}</p>}
      <form onSubmit={ask} className="mt-4 flex flex-col gap-2 sm:flex-row">
        <input dir="auto" className="min-w-0 flex-1 rounded-xl border border-line bg-transparent px-3 py-2 dark:border-line-dark" value={question} maxLength={1000} onChange={(event) => setQuestion(event.target.value)} placeholder={t("Ask about general skin or acne care")} aria-label={t("Ask about general skin or acne care")} />
        <button className="btn-primary" type="submit" disabled={!question.trim() || busy}>{busy ? t("Sending…") : <>{t("Ask")} <Send size={15} /></>}</button>
      </form>
      <label className="mt-3 flex cursor-pointer items-start gap-2 text-xs text-brand-600 dark:text-brand-200">
        <input className="mt-0.5 accent-brand-600" type="checkbox" checked={allowGeneration} onChange={(event) => setAllowGeneration(event.target.checked)} />
        <span><span className="inline-flex items-center gap-1 font-semibold"><Sparkles size={13} />{t("Allow optional Hugging Face generation")}</span><span className="mt-1 block">{t("When enabled and configured, your message and recent chat turns are sent to the selected Hugging Face model. Avoid personal or identifying details.")}</span></span>
      </label>
      <p className="mt-3 text-xs text-brand-500 dark:text-brand-300">{t("Do not share identifying or sensitive personal details.")}</p>
    </section>
  );
}
