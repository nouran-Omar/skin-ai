import { Check } from "lucide-react";
import { useLanguage } from "../i18n";

const STEPS = ["Consent", "Questions", "Photo", "Result"];

export default function Stepper({ current }: { current: number }) {
  const { t } = useLanguage();
  return (
    <ol className="mx-auto flex w-full max-w-4xl items-center gap-1.5 px-4 sm:gap-2" aria-label={t("Progress")}>
      {STEPS.map((label, i) => {
        const done = i < current, active = i === current;
        return (
          <li key={label} className="flex flex-1 items-center gap-1.5 sm:gap-2" aria-current={active ? "step" : undefined}>
            <span className={`grid h-7 w-7 shrink-0 place-items-center rounded-full text-xs font-bold transition
              ${done ? "bg-mint-500 text-white" : active ? "bg-brand-700 text-white dark:bg-brand-400 dark:text-brand-900" : "border border-line text-brand-400 dark:border-line-dark"}`}>
              {done ? <Check size={14} /> : i + 1}
            </span>
            <span className={`whitespace-nowrap text-sm ${active ? "block font-semibold" : "hidden text-brand-500 dark:text-brand-300 sm:block"}`}>{t(label)}</span>
            {i < STEPS.length - 1 && <span className={`h-px flex-1 ${done ? "bg-mint-500" : "bg-line dark:bg-line-dark"}`} />}
          </li>
        );
      })}
    </ol>
  );
}
