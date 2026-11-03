import { AlertTriangle, CheckCircle2, Download, Info, RotateCcw, ShieldAlert } from "lucide-react";
import { useState } from "react";
import { reportUrl } from "../api";
import { translatedContent, useLanguage } from "../i18n";
import type { AnalysisResult, Prediction } from "../types";

const RISK: Record<string, { label: string; cls: string }> = {
  malignant: { label: "Malignant", cls: "bg-coral-100 text-coral-500" },
  premalignant: { label: "Pre-malignant", cls: "bg-amber-100 text-amber-500" },
  benign: { label: "Benign", cls: "bg-mint-100 text-mint-700" },
  inflammatory: { label: "Inflammatory", cls: "bg-brand-100 text-brand-700" },
  vascular: { label: "Vascular", cls: "bg-brand-100 text-brand-700" },
  unknown: { label: "Unclassified", cls: "bg-brand-100 text-brand-700" },
};
const URGENCY = {
  urgent: { box: "bg-coral-500 text-white", Icon: ShieldAlert },
  soon: { box: "bg-amber-500 text-white", Icon: AlertTriangle },
  routine: { box: "bg-mint-600 text-white", Icon: CheckCircle2 },
} as const;

function Ring({ value, color }: { value: number; color: string }) {
  const { t } = useLanguage();
  const r = 52, c = 2 * Math.PI * r;
  return (
    <svg viewBox="0 0 120 120" className="h-32 w-32 shrink-0 sm:h-40 sm:w-40" role="img" aria-label={`${t("Confidence")} ${Math.round(value * 100)}%`}>
      <circle cx="60" cy="60" r={r} fill="none" strokeWidth="10" className="stroke-brand-100 dark:stroke-white/10" />
      <circle cx="60" cy="60" r={r} fill="none" strokeWidth="10" strokeLinecap="round" stroke={color}
        strokeDasharray={c} strokeDashoffset={c * (1 - value)} transform="rotate(-90 60 60)" className="transition-all duration-1000" />
      <text x="60" y="64" textAnchor="middle" className="fill-current font-display text-[26px] font-semibold">{Math.round(value * 100)}%</text>
      <text x="60" y="82" textAnchor="middle" className="fill-brand-500 text-[8px]">{t("confidence")}</text>
    </svg>
  );
}

function Bars({ items, adjusted }: { items: Prediction[]; adjusted: boolean }) {
  const { language } = useLanguage();
  const key = adjusted ? "adjusted_probability" : "probability";
  const sorted = [...items].sort((a, b) => b[key] - a[key]).slice(0, 5);
  return (
    <ul className="space-y-3">
      {sorted.map((p, i) => (
        <li key={p.label}>
          <div className="mb-1 flex justify-between gap-3 text-sm">
            <span className={`min-w-0 break-words ${i === 0 ? "font-semibold" : ""}`}>{translatedContent(p.name, language)}</span>
            <span className="shrink-0 tabular-nums text-brand-500 dark:text-brand-300">{(p[key] * 100).toFixed(1)}%</span>
          </div>
          <div className="h-2.5 overflow-hidden rounded-full bg-brand-100 dark:bg-white/10" role="meter" aria-valuenow={Math.round(p[key] * 100)} aria-valuemin={0} aria-valuemax={100} aria-label={translatedContent(p.name, language)}>
            <div className={`h-full rounded-full transition-all duration-700 ${i === 0 ? "bg-brand-600 dark:bg-brand-400" : "bg-brand-300 dark:bg-brand-600"}`} style={{ width: `${p[key] * 100}%` }} />
          </div>
        </li>
      ))}
    </ul>
  );
}

export default function Results({ r, onReset }: { r: AnalysisResult; onReset: () => void }) {
  const { language, t } = useLanguage();
  const [adjusted, setAdjusted] = useState(true);
  const [reveal, setReveal] = useState(60);
  const top = [...r.predictions].sort((a, b) => (adjusted ? b.adjusted_probability - a.adjusted_probability : b.probability - a.probability))[0];
  const conf = adjusted ? top.adjusted_probability : top.probability;
  const risk = RISK[top.risk] ?? RISK.unknown;
  const u = URGENCY[r.urgency.level];
  const ringColor = conf >= 0.7 ? "#1fb58a" : conf >= 0.5 ? "#3a7bc0" : "#c98a0b";

  return (
    <div className="mx-auto w-full max-w-5xl space-y-5">
      {r.demo && <p role="status" className="rounded-xl bg-amber-100 px-4 py-3 text-sm text-amber-500"><b>{t("Demo mode.")}</b> {t("No trained model is installed, so these numbers are placeholders.")}</p>}

      <div className={`flex items-start gap-3 rounded-2xl p-4 sm:gap-4 sm:p-5 ${u.box}`} role="status">
        <u.Icon size={26} className="mt-0.5 shrink-0" />
        <div><h2 className="text-xl font-semibold">{translatedContent(r.urgency.title, language)}</h2><p className="mt-1 text-white/90">{translatedContent(r.urgency.message, language)}</p></div>
      </div>

      <div className="grid gap-5 lg:grid-cols-5">
        <section className="panel min-w-0 p-4 sm:p-6 lg:col-span-3" aria-labelledby="top-title">
          <div className="flex flex-col items-center gap-4 text-center sm:flex-row sm:gap-6 sm:text-left">
            <Ring value={conf} color={ringColor} />
            <div>
              <span className={`inline-block rounded-full px-3 py-1 text-xs font-bold ${risk.cls}`}>{t(risk.label)}</span>
              <h3 id="top-title" className="mt-2 text-2xl font-semibold leading-tight sm:text-3xl">{translatedContent(top.name, language)}</h3>
              <p className="mt-2 max-w-md text-brand-600 dark:text-brand-200">{translatedContent(top.description, language)}</p>
            </div>
          </div>

          <div className="mb-4 mt-6 flex flex-wrap items-center justify-between gap-3 sm:mt-8">
            <h3 className="text-lg font-semibold">{t("Other possibilities")}</h3>
            <div className="inline-flex rounded-xl border border-line p-0.5 text-sm dark:border-line-dark" role="group" aria-label={t("Probability source")}>
              {[true, false].map((v) => (
                <button key={String(v)} aria-pressed={adjusted === v} onClick={() => setAdjusted(v)}
                  className={`rounded-lg px-3 py-2 transition sm:py-1.5 ${adjusted === v ? "bg-brand-700 text-white dark:bg-brand-400 dark:text-brand-900" : ""}`}>
                  {v ? t("With your answers") : t("Image only")}
                </button>
              ))}
            </div>
          </div>
          <Bars items={r.predictions} adjusted={adjusted} />
        </section>

        <section className="panel min-w-0 p-4 sm:p-6 lg:col-span-2" aria-labelledby="map-title">
          <h3 id="map-title" className="text-lg font-semibold">{t("What the model looked at")}</h3>
          <div className="relative mt-4 aspect-square overflow-hidden rounded-xl">
            <img src={r.images.processed} alt={t("Preprocessed photo")} className="absolute inset-0 h-full w-full object-cover" />
            <img src={r.images.gradcam} alt={t("Attention heat map")} className="absolute inset-0 h-full w-full object-cover"
              style={{ clipPath: language === "ar" ? `inset(0 0 0 ${100 - reveal}%)` : `inset(0 ${100 - reveal}% 0 0)` }} />
            <div className="absolute inset-y-0 w-0.5 bg-white shadow" style={language === "ar" ? { right: `${reveal}%` } : { left: `${reveal}%` }} />
          </div>
          <label className="mt-4 block text-sm text-brand-500 dark:text-brand-300">
            {t("Slide to compare photo and heat map")}
            <input type="range" min={0} max={100} value={reveal} onChange={(e) => setReveal(+e.target.value)} className="mt-2 h-6 w-full cursor-pointer accent-brand-600" />
          </label>
          <p className="mt-2 text-xs text-brand-500 dark:text-brand-300">{t("Warm colours mark the regions that pushed the model towards its top answer.")}</p>
        </section>
      </div>

      {(r.warnings.length > 0 || r.context_factors.length > 0) && (
        <div className="grid gap-5 md:grid-cols-2">
          {r.warnings.length > 0 && (
            <section className="panel min-w-0 p-4 sm:p-6"><h3 className="mb-3 flex items-center gap-2 text-lg font-semibold"><AlertTriangle size={18} className="text-amber-500" /> {t("Things to know")}</h3>
              <ul className="list-disc space-y-2 pl-5 text-sm">{r.warnings.map((w) => <li key={w}>{translatedContent(w, language)}</li>)}</ul></section>
          )}
          {r.context_factors.length > 0 && (
            <section className="panel min-w-0 p-4 sm:p-6"><h3 className="mb-3 flex items-center gap-2 text-lg font-semibold"><Info size={18} className="text-brand-500" /> {t("How your answers changed the result")}</h3>
              <ul className="list-disc space-y-2 pl-5 text-sm">{r.context_factors.map((f) => <li key={f.reason}>{translatedContent(f.reason, language)}</li>)}</ul></section>
          )}
        </div>
      )}

      <details className="panel p-4 sm:p-6">
        <summary className="cursor-pointer text-lg font-semibold">{t("Image processing details")}</summary>
        <dl className="mt-4 grid gap-x-8 gap-y-2 text-sm sm:grid-cols-2">
          {([["Original size", r.preprocessing.original_size], ["Model input", r.preprocessing.model_input_size], ["Hair removed", `${r.preprocessing.hair_coverage_pct}%`],
            ["Sharpness", r.preprocessing.sharpness_score], ["Brightness", r.preprocessing.mean_brightness], ["Model", r.model.arch], ["Calibration (T)", r.model.temperature]] as const)
            .map(([k, v]) => <div key={k} className="flex justify-between gap-3 border-b border-line py-1.5 dark:border-line-dark"><dt className="text-brand-500 dark:text-brand-300">{t(k)}</dt><dd className="break-words text-right tabular-nums">{v}</dd></div>)}
        </dl>
        <p className="mt-3 text-sm text-brand-500 dark:text-brand-300">{r.preprocessing.steps.map((step) => translatedContent(step, language)).join(" ← ")}</p>
      </details>

      <div className="flex flex-wrap items-center justify-between gap-4">
        <p className="max-w-2xl text-xs text-brand-500 dark:text-brand-300">{translatedContent(r.disclaimer, language)}</p>
        <div className="flex w-full flex-col-reverse gap-3 sm:w-auto sm:flex-row">
          <button className="btn-ghost w-full sm:w-auto" onClick={onReset}><RotateCcw size={16} /> {t("Start over")}</button>
          <a className="btn-primary w-full sm:w-auto" href={reportUrl(r.id, language)} download><Download size={16} /> {t("Download PDF report")}</a>
        </div>
      </div>
    </div>
  );
}
