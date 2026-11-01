import { useEffect, useState } from "react";
import { BookOpenCheck, ExternalLink, FileDown } from "lucide-react";
import { acneGuideUrl, fetchAssistantGuide, type AssistantGuide } from "../api";
import { useLanguage } from "../i18n";

export default function AcneCarePanel() {
  const { language, t } = useLanguage();
  const [guide, setGuide] = useState<AssistantGuide | null>(null);
  useEffect(() => {
    let active = true;
    fetchAssistantGuide("acne", language).then((result) => { if (active) setGuide(result); }).catch(() => { if (active) setGuide(null); });
    return () => { active = false; };
  }, [language]);
  return (
    <section className="panel h-full p-5 sm:p-6" aria-labelledby="acne-title">
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-mint-100 text-mint-700 dark:bg-mint-900/40 dark:text-mint-300"><BookOpenCheck size={20} /></span>
        <div>
          <h2 id="acne-title" className="text-xl font-semibold">{t("Acne care guide")}</h2>
          <p className="mt-1 text-sm text-brand-500 dark:text-brand-300">{t("General education for gentle, over-the-counter skin care. Acne is not a class supported by this image model.")}</p>
        </div>
      </div>
      {guide && <div dir="auto" className="mt-4 rounded-xl border border-mint-300/70 bg-mint-50/70 p-3 text-sm leading-6 dark:border-mint-700 dark:bg-mint-900/20"><p>{guide.guidance}</p><a className="mt-2 inline-flex items-center gap-1 text-xs font-medium underline" href={guide.source.url} target="_blank" rel="noreferrer">{guide.source.title}<ExternalLink size={12} /></a></div>}
      <ul className="mt-4 list-disc space-y-2 ps-5 text-sm">
        <li>{t("Wash gently and avoid scrubbing or picking.")}</li>
        <li>{t("If suitable, try one OTC active such as benzoyl peroxide or salicylic acid gradually and follow its product label.")}</li>
        <li>{t("Avoid adapalene during pregnancy or when trying to conceive unless a clinician advises otherwise.")}</li>
      </ul>
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <a className="btn-primary" href={acneGuideUrl(language)} download><FileDown size={16} /> {t("Download acne care guide (English)")}</a>
        <a className="inline-flex items-center gap-1 text-sm text-brand-600 underline dark:text-brand-200" href="https://www.aad.org/public/diseases/acne/diy/adult-acne-treatment" target="_blank" rel="noreferrer">{t("AAD self-care guidance")} <ExternalLink size={13} /></a>
      </div>
      <p className="mt-3 text-xs text-brand-500 dark:text-brand-300">{t("Educational information only. Seek medical advice for painful nodules, scarring, severe irritation, or persistent concerns.")}</p>
    </section>
  );
}
