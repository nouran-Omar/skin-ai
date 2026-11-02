import { ArrowLeft, ArrowRight, ShieldCheck } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { analyze, fetchQuiz } from "../api";
import Analyzing from "../components/Analyzing";
import Quiz from "../components/Quiz";
import Results from "../components/Results";
import SiteFooter from "../components/SiteFooter";
import SiteHeader from "../components/SiteHeader";
import Stepper from "../components/Stepper";
import Uploader from "../components/Uploader";
import { localizeApiError, useLanguage } from "../i18n";
import type { AnalysisResult, Answers, Question } from "../types";

type Stage = "consent" | "quiz" | "upload" | "analyzing" | "results";
const INDEX: Record<Stage, number> = { consent: 0, quiz: 1, upload: 2, analyzing: 2, results: 3 };

export default function ScreeningPage() {
  const { language, t } = useLanguage();
  const [stage, setStage] = useState<Stage>("consent");
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loadErr, setLoadErr] = useState<string | null>(null);
  const [agreedMedical, setAgreedMedical] = useState(false);
  const [agreedPrivacy, setAgreedPrivacy] = useState(false);
  const [answers, setAnswers] = useState<Answers>({});
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadQuestions = useCallback(() => {
    setLoadErr(null);
    fetchQuiz().then(setQuestions).catch((error) => {
      setLoadErr(localizeApiError(error instanceof Error ? error.message : "Could not connect to the SkinAI service. It may be starting, or the API URL or browser access settings may need checking. Please try again shortly.", language));
    });
  }, [language]);
  useEffect(loadQuestions, [loadQuestions]);
  useEffect(() => {
    if (!file) { setPreview(null); return; }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const run = async () => {
    if (!file) return;
    setError(null);
    setStage("analyzing");
    try { setResult(await analyze(file, answers)); setStage("results"); }
    catch (e) {
      setError(localizeApiError(e instanceof Error ? e.message : "Something went wrong.", language));
      setStage("upload");
    }
  };
  const reset = () => {
    setAnswers({}); setFile(null); setResult(null); setError(null);
    setAgreedMedical(false); setAgreedPrivacy(false); setStage("consent");
  };

  return <div className="min-h-screen min-h-[100dvh]">
    <SiteHeader />
    <main className="mx-auto max-w-5xl px-4 pb-16 pt-6 sm:px-6 sm:pt-10">
      <a href="/" className="inline-flex items-center gap-2 text-sm font-medium text-brand-600 underline-offset-4 hover:underline dark:text-brand-200"><ArrowLeft size={16} />{t("Back to SkinAI")}</a>
      <header className="mx-auto mt-8 max-w-3xl text-center">
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-mint-700 dark:text-mint-300">{t("Primary feature")}</p>
        <h1 className="mt-2 text-3xl font-semibold leading-tight xs:text-4xl sm:text-5xl">{t("Check a skin spot, with context a camera can't see.")}</h1>
        <p className="mx-auto mt-4 max-w-3xl text-base leading-7 text-brand-600 dark:text-brand-200 sm:text-lg">{t("Answer a few questions about the spot, add a photo, and get a ranked list of likely conditions, an urgency level and a PDF summary you can bring to your doctor.")}</p>
      </header>
      <div className="mx-auto max-w-3xl pt-8"><Stepper current={INDEX[stage]} /></div>
      {loadErr && <div role="alert" className="mx-auto my-6 max-w-2xl rounded-xl bg-coral-100 px-4 py-3 text-sm text-coral-500"><p>{t(loadErr)}</p><button type="button" className="mt-2 font-semibold underline underline-offset-2" onClick={loadQuestions}>{t("Try again")}</button></div>}
      <section id="skin-check" className="px-0 py-10 sm:py-12" aria-label={t("Skin lesion check")}>
        {stage === "consent" && <div className="panel mx-auto max-w-3xl border-brand-200/80 p-4 shadow-sm dark:border-line-dark sm:p-6">
          <div className="flex items-start gap-3 rounded-xl bg-brand-50 p-3.5 text-sm leading-6 dark:bg-white/5 sm:p-4">
            <ShieldCheck className="mt-0.5 shrink-0 text-mint-600 dark:text-mint-300" size={20} />
            <div><p className="font-semibold">{t("Medical safety notice")}</p><p className="mt-1 text-brand-600 dark:text-brand-200">{t("This tool supports, and never replaces, a clinician. It cannot diagnose. Photos are processed on the server, kept for 24 hours so you can download your report, then deleted.")}</p></div>
          </div>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 sm:gap-4">
            <label className="flex min-h-24 cursor-pointer items-start gap-3 rounded-xl border border-line bg-white/70 p-4 text-sm leading-6 transition hover:border-brand-300 dark:border-line-dark dark:bg-white/[0.02] dark:hover:border-brand-500">
              <input type="checkbox" checked={agreedMedical} onChange={(e) => setAgreedMedical(e.target.checked)} className="mt-1 h-4 w-4 shrink-0 accent-brand-600" />
              <span>{t("I understand SkinAI is educational and cannot diagnose or replace a clinician.")}</span>
            </label>
            <label className="flex min-h-24 cursor-pointer items-start gap-3 rounded-xl border border-line bg-white/70 p-4 text-sm leading-6 transition hover:border-brand-300 dark:border-line-dark dark:bg-white/[0.02] dark:hover:border-brand-500">
              <input type="checkbox" checked={agreedPrivacy} onChange={(e) => setAgreedPrivacy(e.target.checked)} className="mt-1 h-4 w-4 shrink-0 accent-brand-600" />
              <span>{t("I understand my photo is processed on the server and the report is temporarily available for up to 24 hours.")}</span>
            </label>
          </div>
          <div className="mt-5 flex justify-center"><button className="btn-primary min-w-52" disabled={!agreedMedical || !agreedPrivacy || questions.length === 0} onClick={() => setStage("quiz")}>{t("Start questions")}<ArrowRight size={17} /></button></div>
        </div>}
        {stage === "quiz" && <Quiz questions={questions} answers={answers} onChange={setAnswers} onBack={() => setStage("consent")} onDone={() => setStage("upload")} />}
        {stage === "upload" && <Uploader file={file} error={error} onFile={setFile} onBack={() => setStage("quiz")} onAnalyze={run} />}
        {stage === "analyzing" && <Analyzing src={preview} />}
        {stage === "results" && result && <Results r={result} onReset={reset} />}
      </section>
    </main>
    <SiteFooter />
  </div>;
}
