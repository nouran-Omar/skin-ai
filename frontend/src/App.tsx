import { ArrowRight, MessageCircleHeart, Sparkles } from "lucide-react";
import { useEffect } from "react";
import AccountPanel from "./components/AccountPanel";
import AcneCarePanel from "./components/AcneCarePanel";
import SiteHeader from "./components/SiteHeader";
import SiteFooter from "./components/SiteFooter";
import AssistantPage from "./pages/AssistantPage";
import ScreeningPage from "./pages/ScreeningPage";
import { useLanguage } from "./i18n";

export default function App() {
  const path = window.location.pathname.replace(/\/+$/, "");
  if (path === "/assistant") return <AssistantPage />;
  if (path === "/screening") return <ScreeningPage />;
  return <HomePage />;
}

function HomePage() {
  const { t } = useLanguage();
  useEffect(() => {
    const id = window.location.hash.slice(1);
    if (id) requestAnimationFrame(() => document.getElementById(decodeURIComponent(id))?.scrollIntoView({ behavior: "smooth" }));
  }, []);
  return (
    <div className="min-h-screen min-h-[100dvh]">
      <SiteHeader />
      <section id="about" className="hero-surface relative isolate w-full overflow-hidden bg-[radial-gradient(ellipse_at_78%_18%,rgba(55,184,174,.23),transparent_34%),linear-gradient(120deg,#102a43_0%,#174454_55%,#126264_100%)] text-white">
        <div aria-hidden="true" className="pointer-events-none absolute -end-20 -top-28 h-80 w-80 rounded-full border border-white/10 sm:h-[26rem] sm:w-[26rem]" />
        <div aria-hidden="true" className="pointer-events-none absolute -bottom-32 -start-16 h-80 w-80 rounded-full bg-teal-400/15 blur-3xl" />
        <div className="relative mx-auto flex max-w-7xl flex-col items-center px-5 pb-28 pt-20 text-center sm:px-8 sm:pb-32 sm:pt-24 lg:pb-40 lg:pt-32">
          <span className="inline-flex items-center gap-2 rounded-full border border-teal-100/25 bg-white/[0.08] px-4 py-2 text-xs font-semibold tracking-wide text-teal-100 shadow-sm shadow-black/10"><Sparkles size={14} />{t("AI-supported skin health")}</span>
          <h1 className="mt-6 max-w-5xl text-4xl font-semibold leading-[1.2] tracking-tight text-white xs:text-5xl sm:text-6xl lg:text-7xl">{t("SkinAI | Smart skin lesion pre-screening")}</h1>
          <p className="mt-6 max-w-3xl text-base leading-8 text-slate-100/90 sm:text-lg sm:leading-9">{t("Explore a skin concern with AI-supported pre-screening, receive a clear clinical-style report to discuss with a clinician, and build awareness for earlier care.")}</p>
          <a href="/screening" className="group mt-9 inline-flex min-h-14 items-center gap-4 rounded-full bg-white px-6 py-3 text-sm font-bold text-brand-900 shadow-[0_14px_40px_-18px_rgba(0,0,0,.55)] transition duration-300 hover:-translate-y-0.5 hover:bg-teal-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal-200 focus-visible:outline-offset-4 motion-reduce:transition-none">
            {t("Start screening")}<span className="grid h-8 w-8 place-items-center rounded-full bg-teal-100 text-teal-700 transition-transform duration-300 group-hover:translate-y-0.5"><ArrowRight size={16} /></span>
          </a>
        </div>
        <svg aria-hidden="true" className="pointer-events-none absolute inset-x-0 bottom-[-1px] h-14 w-full sm:h-20 lg:h-28" viewBox="0 0 1440 120" preserveAspectRatio="none">
          <path className="fill-[#f7f8fb] dark:hidden" d="M0 50C190 100 372 116 600 91c238-26 405-89 623-75 83 5 153 24 217 45v59H0V50Z" />
          <path className="hidden fill-[#0b1620] dark:block" d="M0 50C190 100 372 116 600 91c238-26 405-89 623-75 83 5 153 24 217 45v59H0V50Z" />
        </svg>
      </section>

      <main className="w-full">
        <section className="scroll-mt-24 border-y border-sage-100 bg-sage-50/70 px-4 py-20 sm:px-6 sm:py-24 lg:px-8 lg:py-32 dark:border-line-dark dark:bg-white/[0.02]" aria-labelledby="features-title">
          <div className="mx-auto max-w-7xl">
          <div className="mb-6 flex flex-col gap-2 sm:mb-8 sm:flex-row sm:items-end sm:justify-between">
            <div><p className="text-xs font-bold uppercase tracking-[0.18em] text-mint-700 dark:text-mint-300">{t("Optional features")}</p><h2 id="features-title" className="mt-2 text-2xl font-semibold sm:text-3xl">{t("Explore at your own pace")}</h2></div>
            <p className="max-w-xl text-sm leading-6 text-brand-600 dark:text-brand-200">{t("Helpful tools and education are here when you want them.")}</p>
          </div>
          <div className="grid items-stretch gap-6 md:grid-cols-2 md:gap-8">
            <div id="assistant" className="scroll-mt-6">
              <section className="relative flex h-full min-h-[22rem] flex-col overflow-hidden rounded-2xl border border-brand-700 bg-gradient-to-br from-brand-900 via-brand-800 to-[#315d79] p-5 text-white shadow-sm sm:p-7" aria-labelledby="assistant-feature-title">
                <div aria-hidden="true" className="pointer-events-none absolute -end-12 -top-12 h-48 w-48 rounded-full border border-white/10" />
                <span className="grid h-12 w-12 place-items-center rounded-2xl bg-white/10 text-mint-200"><MessageCircleHeart size={24} /></span>
                <p className="mt-6 text-xs font-bold uppercase tracking-[0.16em] text-mint-200">{t("A friendly place to ask")}</p>
                <h3 id="assistant-feature-title" className="mt-2 text-2xl font-semibold text-white">{t("Interactive SkinAI Assistant")}</h3>
                <p className="mt-3 max-w-lg text-sm leading-6 text-brand-100">{t("A welcoming space for everyday skin questions, with trusted sources and gentle guidance.")}</p>
                <a href="/assistant" className="btn mt-7 w-full justify-between border border-white/20 bg-white text-brand-900 transition hover:bg-mint-100 sm:w-auto sm:min-w-56">
                  {t("Start Free Chat")}<ArrowRight size={17} />
                </a>
              </section>
            </div>
            <div id="acne-care" className="scroll-mt-6"><AcneCarePanel /></div>
          </div>
          </div>
        </section>

        <section id="journal" className="scroll-mt-24 px-4 py-20 sm:px-6 sm:py-24 lg:px-8 lg:py-32" aria-label={t("Account") }>
          <div className="mx-auto max-w-7xl"><AccountPanel /></div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
