export default function SkinAILogo({ className = "h-10 w-10" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 48 48" fill="none" role="img" aria-label="SkinAI">
      <defs>
        <linearGradient id="skinai-mark" x1="7" y1="5" x2="41" y2="43" gradientUnits="userSpaceOnUse">
          <stop stopColor="#48C8B5" />
          <stop offset="1" stopColor="#A9D8BC" />
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="44" height="44" rx="15" fill="#102A43" />
      <path d="M24 9.5c-7.18 0-13 5.82-13 13v3c0 7.18 5.82 13 13 13s13-5.82 13-13v-3c0-7.18-5.82-13-13-13Z" stroke="url(#skinai-mark)" strokeWidth="2.4" />
      <path d="M24 16v15M16.5 23.5h15" stroke="white" strokeWidth="2.8" strokeLinecap="round" />
      <circle cx="35.5" cy="12.5" r="3.5" fill="#48C8B5" stroke="#102A43" strokeWidth="1.5" />
      <circle cx="35.5" cy="12.5" r="1" fill="#102A43" />
    </svg>
  );
}
