import { ChevronLeft, ChevronRight } from "lucide-react";
import { useMemo, useState } from "react";
import type { AnswerValue, Answers, Question } from "../types";
import { localizeQuestion, useLanguage } from "../i18n";

export function isVisible(q: Question, a: Answers): boolean {
  const s = q.show_if;
  if (!s) return true;
  const v = a[s.question];
  if (s.equals !== undefined) return v === s.equals;
  if (s.includes !== undefined) return Array.isArray(v) && v.includes(s.includes);
  if (s.includes_any) return Array.isArray(v) && s.includes_any.some((x) => v.includes(x));
  if (s.in) return typeof v === "string" && s.in.includes(v);
  return true;
}

/** Drop answers to questions that became hidden after a change (keeps the payload clean). */
function prune(questions: Question[], a: Answers): Answers {
  let out = a;
  for (let pass = 0; pass < 3; pass++) {
    const next: Answers = {};
    for (const q of questions) if (q.id in out && isVisible(q, out)) next[q.id] = out[q.id];
    out = next;
  }
  return out;
}

const answered = (v: AnswerValue | undefined) => v !== undefined && (Array.isArray(v) ? v.length > 0 : v !== "");

interface Props { questions: Question[]; answers: Answers; onChange: (a: Answers) => void; onBack: () => void; onDone: () => void }

export default function Quiz({ questions, answers, onChange, onBack, onDone }: Props) {
  const { language, t } = useLanguage();
  const [idx, setIdx] = useState(0);
  const visible = useMemo(() => questions.filter((q) => isVisible(q, answers)).map((q) => localizeQuestion(q, language)), [questions, answers, language]);
  const i = Math.min(idx, visible.length - 1);
  const q = visible[i];
  const value = answers[q.id];
  const set = (v: AnswerValue | undefined) => {
    const next = { ...answers };
    if (v === undefined) delete next[q.id]; else next[q.id] = v;
    onChange(prune(questions, next));
  };
  const canNext = !q.required || answered(value);
  const last = i === visible.length - 1;

  const toggle = (opt: { value: string; exclusive?: boolean }) => {
    const cur = Array.isArray(value) ? value : [];
    if (opt.exclusive) return set(cur.includes(opt.value) ? undefined : [opt.value]);
    const without = cur.filter((x) => x !== opt.value && !q.options?.find((o) => o.value === x)?.exclusive);
    set(cur.includes(opt.value) ? (without.length ? without : undefined) : [...without, opt.value]);
  };

  return (
    <section className="panel mx-auto w-full max-w-2xl p-4 xs:p-6 sm:p-8" aria-labelledby="q-title">
      <div className="mb-5 flex items-center justify-between gap-3 text-sm sm:mb-6 text-brand-500 dark:text-brand-300">
        <span className="min-w-0 truncate">{q.section}</span>
        <span className="shrink-0">{i + 1} {t("of")} {visible.length}</span>
      </div>
      <div className="mb-8 h-1.5 overflow-hidden rounded-full bg-brand-100 dark:bg-white/10" role="progressbar" aria-valuemin={0} aria-valuemax={visible.length} aria-valuenow={i + 1}>
        <div className="h-full rounded-full bg-mint-500 transition-all duration-300" style={{ width: `${((i + 1) / visible.length) * 100}%` }} />
      </div>

      <h2 id="q-title" className="text-xl font-semibold leading-snug sm:text-2xl">{q.text}</h2>
      {q.help && <p className="mt-2 text-sm text-brand-500 dark:text-brand-300">{q.help}</p>}

      <div className="mt-5 space-y-2.5 sm:mt-6" role={q.type === "multi" ? "group" : "radiogroup"} aria-labelledby="q-title">
        {(q.type === "single" || q.type === "multi") && q.options?.map((o) => {
          const on = q.type === "multi" ? Array.isArray(value) && value.includes(o.value) : value === o.value;
          return (
            <button key={o.value} type="button" className="choice" aria-pressed={on}
              onClick={() => (q.type === "multi" ? toggle(o) : set(o.value))}>
              <span className="font-medium">{o.label}</span>
              {o.hint && <span className="ml-2 text-sm text-brand-400">{o.hint}</span>}
            </button>
          );
        })}

        {q.type === "number" && (
          <label className="block">
            <span className="sr-only">{q.text}</span>
            <div className="flex items-center gap-3">
              <input type="number" inputMode="numeric" min={q.min} max={q.max} value={typeof value === "number" ? value : ""}
                className="w-32 rounded-xl border border-line bg-transparent px-4 py-3 text-lg dark:border-line-dark"
                onChange={(e) => { const n = e.target.valueAsNumber; set(Number.isNaN(n) ? undefined : Math.min(q.max ?? 120, Math.max(q.min ?? 0, n))); }} />
              <span className="text-brand-500">{q.unit}</span>
            </div>
          </label>
        )}

        {q.type === "scale" && (
          <div className="grid grid-cols-5 gap-2 xs:grid-cols-6 md:grid-cols-11">
            {Array.from({ length: (q.max ?? 10) - (q.min ?? 0) + 1 }, (_, k) => (q.min ?? 0) + k).map((n) => (
              <button key={n} type="button" className="choice !px-0 text-center font-semibold" aria-pressed={value === n} onClick={() => set(n)}>{n}</button>
            ))}
          </div>
        )}
      </div>

      <div className="mt-8 flex justify-between gap-3">
        <button className="btn-ghost" onClick={() => (i === 0 ? onBack() : setIdx(i - 1))}><ChevronLeft size={16} /> {t("Back")}</button>
        <button className="btn-primary flex-1 sm:flex-none" disabled={!canNext} onClick={() => (last ? onDone() : setIdx(i + 1))}>
          {last ? t("Continue to photo") : t("Next")} <ChevronRight size={16} />
        </button>
      </div>
    </section>
  );
}
