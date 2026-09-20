export default function LoadingOverlay({ label = "Processing…" }) {
  return (
    <div className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-ink/85 backdrop-blur-sm">
      <div className="relative h-16 w-16">
        <div className="absolute inset-0 flex flex-col justify-center gap-1.5">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-[2px] w-full overflow-hidden rounded-full bg-hairline">
              <div
                className="h-full w-1/3 bg-amber"
                style={{ animation: "scan-line 1.4s ease-in-out infinite", animationDelay: `${i * 0.15}s` }}
              />
            </div>
          ))}
        </div>
        <div className="absolute inset-0" style={{ animation: "glass-sweep 2s ease-in-out infinite" }}>
          <svg
            viewBox="0 0 24 24"
            className="h-6 w-6 text-amber"
            style={{ filter: "drop-shadow(0 0 6px rgba(232,163,61,0.6))" }}
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="10" cy="10" r="6" />
            <line x1="14.5" y1="14.5" x2="20" y2="20" />
          </svg>
        </div>
      </div>
      <p className="mt-5 font-mono text-xs tracking-wide text-ash">{label}</p>
    </div>
  );
}