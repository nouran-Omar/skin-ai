import { ArrowLeft, MessageCircleHeart } from "lucide-react";
import AssistantPanel from "../components/AssistantPanel";
import SiteFooter from "../components/SiteFooter";
import SiteHeader from "../components/SiteHeader";
import { useLanguage } from "../i18n";

export default function AssistantPage() {
  const { t } = useLanguage();
  return (
    <div className="min-h-screen min-h-[100dvh]">
      <SiteHeader />
      <main className="mx-auto max-w-5xl px-4 pb-16 pt-6 sm:px-6 sm:pt-10">
        <a href="/" className="inline-flex items-center gap-2 text-sm font-medium text-brand-600 underline-offset-4 hover:underline dark:text-brand-200"><ArrowLeft size={16} />{t("Back to SkinAI")}</a>
        <section className="mx-auto mt-8 max-w-4xl" aria-labelledby="assistant-page-title">
          <div className="mb-6 flex items-start gap-4 sm:mb-8">
            <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-brand-800 text-mint-300 shadow-md"><MessageCircleHeart size={24} /></span>
            <div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-mint-700 dark:text-mint-300">{t("A thoughtful place to start")}</p><h1 id="assistant-page-title" className="mt-1 text-3xl font-semibold sm:text-4xl">{t("Your SkinAI Assistant")}</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-brand-600 dark:text-brand-200 sm:text-base">{t("Ask naturally in English or Arabic about everyday skin care, acne, or general skin-health questions. The assistant shares educational guidance and helps you find trusted sources.")}</p></div>
          </div>
          <AssistantPanel />
          <p className="mx-auto mt-5 max-w-3xl text-center text-xs leading-5 text-brand-500 dark:text-brand-300">{t("If a skin spot is changing, bleeding, or worrying you, arrange an in-person medical assessment. Chat cannot examine skin or diagnose a condition.")}</p>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
