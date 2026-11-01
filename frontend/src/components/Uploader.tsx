import { Camera, ChevronLeft, ImagePlus, ScanSearch, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { localizeApiError, useLanguage } from "../i18n";

const OK = ["image/jpeg", "image/png", "image/webp"];
const MAX_MB = 10;

interface Props { file: File | null; error: string | null; onFile: (f: File | null) => void; onBack: () => void; onAnalyze: () => void }

export default function Uploader({ file, error, onFile, onBack, onAnalyze }: Props) {
  const { language, t } = useLanguage();
  const [drag, setDrag] = useState(false);
  const [localErr, setLocalErr] = useState<string | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const pick = useRef<HTMLInputElement>(null);
  const cam = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!file) { setPreview(null); return; }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const accept = (f?: File) => {
    if (!f) return;
    if (!OK.includes(f.type)) return setLocalErr("Use a JPEG, PNG or WebP photo.");
    if (f.size > MAX_MB * 1024 * 1024) return setLocalErr(`The photo is over ${MAX_MB} MB. Choose a smaller one.`);
    setLocalErr(null); onFile(f);
  };

  return (
    <section className="mx-auto w-full max-w-2xl" aria-labelledby="up-title">
      <h2 id="up-title" className="mb-1 text-xl font-semibold sm:text-2xl">{t("Add a photo of the spot")}</h2>
      <p className="mb-5 text-sm text-brand-500 dark:text-brand-300 sm:text-base">{t("Natural light, in focus, the spot centred and filling about half the frame. Dermoscopy images work best.")}</p>

      {!file ? (
        <div role="button" tabIndex={0} aria-label={t("Upload a photo. Drop a file here or press Enter to browse.")}
          onClick={() => pick.current?.click()} onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && pick.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); accept(e.dataTransfer.files[0]); }}
          className={`panel grid cursor-pointer place-items-center border-2 border-dashed px-4 py-10 text-center sm:px-6 sm:py-16 transition
            ${drag ? "border-mint-500 bg-mint-50 dark:bg-mint-500/10" : "hover:border-brand-300"}`}>
          <ImagePlus size={36} className="mb-3 text-brand-500" />
          <p className="text-lg font-semibold">{t("Drop a photo here")}</p>
          <p className="text-sm text-brand-500 dark:text-brand-300">{t("or click to browse. JPEG, PNG or WebP, up to {size} MB.").replace("{size}", String(MAX_MB))}</p>
          <button type="button" className="btn-ghost mt-5 md:hidden" onClick={(e) => { e.stopPropagation(); cam.current?.click(); }}><Camera size={16} /> {t("Take a photo")}</button>
        </div>
      ) : (
        <div className="panel overflow-hidden">
          <div className="relative bg-black/5 dark:bg-black/30">
            {preview && <img src={preview} alt={t("Selected skin photo")} className="mx-auto max-h-[50vh] w-auto max-w-full object-contain sm:max-h-[420px]" />}
            <button className="btn-ghost absolute right-3 top-3 !bg-panel !px-2.5 !py-2 dark:!bg-panel-dark" onClick={() => onFile(null)} aria-label={t("Remove photo")}><X size={16} /></button>
          </div>
          <p className="break-all px-4 py-3 text-sm text-brand-500 dark:text-brand-300 sm:px-5">{file.name} · {(file.size / 1024 / 1024).toFixed(1)} MB</p>
        </div>
      )}

      <input ref={pick} type="file" accept={OK.join(",")} hidden onChange={(e) => accept(e.target.files?.[0])} />
      <input ref={cam} type="file" accept="image/*" capture="environment" hidden onChange={(e) => accept(e.target.files?.[0])} />
      {(localErr || error) && <p role="alert" className="mt-3 rounded-xl bg-coral-100 px-4 py-3 text-sm text-coral-500">{localizeApiError(localErr ?? error ?? "", language)}</p>}

      <div className="mt-6 flex justify-between gap-3">
        <button className="btn-ghost" onClick={onBack}><ChevronLeft size={16} /> {t("Back")}</button>
        <button className="btn-primary flex-1 sm:flex-none" disabled={!file} onClick={onAnalyze}><ScanSearch size={16} /> {t("Analyse photo")}</button>
      </div>
    </section>
  );
}
