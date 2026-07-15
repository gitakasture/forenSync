import { useState } from "react";

export default function CollapsibleAside({ title, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label={`Expand ${title}`}
        className="flex h-9 w-9 shrink-0 items-center justify-center self-start rounded-sm border border-hairline bg-panel text-ash transition-colors hover:border-amber hover:text-amber"
      >
        ‹
      </button>
    );
  }

  return (
    <aside className="w-64 shrink-0 self-start">
      <div className="rounded-sm border border-hairline bg-panel p-5">
        <div className="mb-4 flex items-center justify-between gap-2">
          <p className="text-xs uppercase tracking-wide text-ash">{title}</p>
          <button
            type="button"
            onClick={() => setOpen(false)}
            aria-label={`Collapse ${title}`}
            className="shrink-0 text-ash transition-colors hover:text-amber"
          >
            ›
          </button>
        </div>
        {children}
      </div>
    </aside>
  );
}
