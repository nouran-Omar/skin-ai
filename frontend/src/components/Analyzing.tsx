import { useEffect, useState } from "react";
import { useLanguage } from "../i18n";

const STAGES = ["Cleaning the image and removing hair", "Balancing colour and lighting", "Running the classification model", "Mapping the areas that influenced the result", "Combining with your answers"];

export default function Analyzing({ src }: { src: string | null }) {
  const { t } = useLanguage();
  const [k, setK] = useState(0);
  useEffect(() => { const t = setInterval(() => setK((x) => Math.min(x + 1, STAGES.length - 1)), 1400); return () => clearInterval(t); }, []);
  return (
    <section className="mx-auto grid w-full max-w-2xl place-items-center py-6 text-center sm:py-10" role="status" aria-live="polite">
      <div className="relative h-56 w-56 overflow-hidden sm:h-64 sm:w-64 rounded-2xl border border-line dark:border-line-dark">
        {src && <img src={src} alt="" className="h-full w-full object-cover opacity-80" />}
        <div className="absolute inset-x-0 h-1/4 bg-gradient-to-b from-transparent via-mint-400/50 to-transparent motion-safe:animate-[sweep_1.6s_ease-in-out_infinite_alternate]" />
      </div>
      <h2 className="mt-6 text-xl font-semibold sm:mt-8 sm:text-2xl">{t("Analysing your photo")}</h2>
      <p className="mt-2 min-h-[3rem] px-2 text-brand-500 dark:text-brand-300 sm:min-h-[1.5rem]">{t(STAGES[k])}...</p>
      <div className="mt-4 h-1.5 w-56 sm:w-64 overflow-hidden rounded-full bg-brand-100 dark:bg-white/10">
        <div className="h-full rounded-full bg-mint-500 transition-all duration-1000" style={{ width: `${((k + 1) / STAGES.length) * 100}%` }} />
      </div>
    </section>
  );
}
