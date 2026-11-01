import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import { useLanguage } from "../i18n";

export default function ThemeToggle() {
  const { t } = useLanguage();
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"));
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    try { localStorage.setItem("theme", dark ? "dark" : "light"); } catch { /* private mode */ }
  }, [dark]);
  return (
    <button className="btn-ghost min-w-[44px] !px-3 !py-2" onClick={() => setDark((d) => !d)} aria-label={t(dark ? "Switch to light mode" : "Switch to dark mode")}>
      {dark ? <Sun size={18} /> : <Moon size={18} />}
    </button>
  );
}
