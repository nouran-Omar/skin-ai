import { ArrowUpRight, Heart } from "lucide-react";
import SkinAILogo from "./SkinAILogo";
import { useLanguage } from "../i18n";

export default function SiteFooter() {
  const { t } = useLanguage();
  const isAssistantPage = window.location.pathname.replace(/\/+$/, "") === "/assistant";
  const section = (id: string) => `${isAssistantPage ? "/" : ""}#${id}`;
  const groups = [
    { title: "Features", links: [[section("skin-check"), "Analysis"], ["/assistant", "Chatbot"], [section("acne-care"), "Acne Care"]] },
    { title: "Account", links: [[section("journal"), "Sign In"], [section("journal"), "Journal"]] },
    { title: "Resources", links: [[section("about"), "About"], [section("limitations"), "Limits"]] },
  ];

  return (
    <footer className="border-t border-line bg-white dark:border-line-dark dark:bg-panel-dark">
      <div className="mx-auto grid max-w-7xl gap-12 px-4 py-16 sm:px-6 sm:py-20 lg:grid-cols-[minmax(0,1.5fr)_repeat(3,minmax(0,1fr))] lg:gap-16 lg:px-8 lg:py-24">
        <div>
          <a href="/" className="inline-flex items-center gap-3 rounded-lg font-display text-lg font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-500">
            <SkinAILogo className="h-11 w-11" /><span>SkinAI</span>
          </a>
          <p className="mt-5 max-w-sm text-sm leading-7 text-brand-600 dark:text-brand-300">{t("SkinAI provides educational pre-screening support and general skin-care information. It does not diagnose or replace a qualified clinician.")}</p>
          <p className="mt-4 inline-flex items-center gap-1.5 text-xs text-brand-500 dark:text-brand-400"><Heart size={13} className="text-coral-500" />{t("Built to make skin-health education more accessible.")}</p>
        </div>
        {groups.map((group) => (
          <nav key={group.title} aria-label={t(group.title)}>
            <h2 className="text-sm font-semibold tracking-wide">{t(group.title)}</h2>
            <ul className="mt-5 space-y-4 text-sm">
              {group.links.map(([href, label]) => (
                <li key={label}>
                  <a className="group inline-flex min-h-9 items-center gap-1 rounded-sm text-brand-600 transition-colors duration-200 hover:text-teal-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-500 dark:text-brand-200 dark:hover:text-mint-300" href={href}>
                    <span className="underline decoration-transparent underline-offset-4 transition group-hover:decoration-current">{t(label)}</span><ArrowUpRight size={13} className="transition-transform duration-200 group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        ))}
      </div>
      <div className="border-t border-line px-4 py-5 text-center text-xs text-brand-500 dark:border-line-dark dark:text-brand-400">© {new Date().getFullYear()} SkinAI · {t("Educational use only")}</div>
    </footer>
  );
}
