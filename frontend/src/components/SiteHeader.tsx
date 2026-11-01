import { useEffect, useState } from "react";
import ThemeToggle from "./ThemeToggle";
import SkinAILogo from "./SkinAILogo";
import { useLanguage } from "../i18n";

export default function SiteHeader() {
  const { language, setLanguage, t } = useLanguage();
  const [scrolled, setScrolled] = useState(false);
  const isAssistantPage = window.location.pathname.replace(/\/+$/, "") === "/assistant";
  const section = (id: string) => `${isAssistantPage ? "/" : ""}#${id}`;

  useEffect(() => {
    const update = () => setScrolled(window.scrollY > 12);
    update();
    window.addEventListener("scroll", update, { passive: true });
    return () => window.removeEventListener("scroll", update);
  }, []);

  const links = [
    [section("skin-check"), "Skin lesion check"],
    ["/assistant", "SkinAI Assistant"],
    [section("acne-care"), "Acne care"],
    [section("journal"), "History & progress"],
  ];

  return (
    <header className={`sticky top-0 z-50 border-b transition-all duration-300 motion-reduce:transition-none ${scrolled ? "border-line/80 bg-white/85 shadow-[0_8px_30px_-18px_rgba(16,42,67,.35)] backdrop-blur-xl dark:border-line-dark/80 dark:bg-panel-dark/85" : "border-transparent bg-canvas/80 backdrop-blur-md dark:bg-canvas-dark/80"}`}>
      <div className={`mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-x-5 gap-y-2 px-4 transition-all duration-300 sm:px-6 lg:px-8 ${scrolled ? "py-2.5" : "py-3.5 sm:py-4"}`}>
        <a href="/" aria-label="SkinAI | Skin lesion pre-screening" className="flex min-w-0 items-center gap-3 rounded-xl focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-500">
          <SkinAILogo className="h-10 w-10 shrink-0 drop-shadow-sm" />
          <span className="min-w-0">
            <span className="block truncate font-display text-[15px] font-semibold leading-tight tracking-[-0.02em] sm:text-base">SkinAI</span>
            <span className="mt-0.5 hidden text-[10px] font-medium leading-tight tracking-wide text-brand-600 dark:text-brand-300 sm:block">{t("Skin lesion pre-screening")}</span>
          </span>
        </a>
        <div className="order-2 flex shrink-0 items-center gap-2 md:order-3">
          <button className="min-h-10 rounded-xl border border-line/80 bg-white/70 px-3 text-sm font-semibold text-brand-800 transition hover:border-teal-300 hover:bg-teal-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-500 dark:border-line-dark dark:bg-white/5 dark:text-brand-100 dark:hover:bg-white/10" onClick={() => setLanguage(language === "en" ? "ar" : "en")} aria-label={language === "en" ? t("Switch to Arabic") : t("Switch to English")}>
            {language === "en" ? "العربية" : "English"}
          </button>
          <ThemeToggle />
        </div>
        <nav className="order-3 w-full overflow-x-auto pb-0.5 md:order-2 md:w-auto md:pb-0" aria-label={t("Main navigation")}>
          <ul className="flex min-w-max items-center gap-1 rounded-2xl border border-line/70 bg-white/60 p-1 text-xs shadow-sm shadow-brand-900/[0.03] dark:border-line-dark dark:bg-white/[0.04] sm:text-sm">
            {links.map(([href, label]) => <li key={label}><a className="block rounded-xl px-3 py-2 text-brand-700 transition-colors hover:bg-teal-50 hover:text-brand-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal-600 dark:text-brand-100 dark:hover:bg-white/10 sm:px-3.5" href={href}>{t(label)}</a></li>)}
          </ul>
        </nav>
      </div>
    </header>
  );
}
