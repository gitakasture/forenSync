import { useEffect, useRef } from "react";

export default function InvestigatorDetailModal({ investigator, onClose }) {
  const overlayRef = useRef(null);

  useEffect(() => {
    const handleEsc = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, [onClose]);

  const handleOverlayClick = (e) => {
    if (e.target === overlayRef.current) onClose();
  };

  if (!investigator) return null;

  return (
    <div
      ref={overlayRef}
      onClick={handleOverlayClick}
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/80 backdrop-blur-sm"
    >
      <div className="w-full max-w-md rounded-sm border border-hairline bg-panel p-6 shadow-2xl">
        {/* Header */}
        <div className="mb-5 flex items-start justify-between">
          <div>
            <h2 className="font-display text-lg font-medium text-paper">
              Investigator Details
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-ash hover:text-paper transition-colors"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="space-y-4">
          {/* Avatar */}
          <div className="flex items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-full border-2 border-amber bg-amber/10 font-mono text-lg font-medium text-amber">
              {investigator.initials || 
                investigator.name?.split(" ").map((n) => n[0]).join("") || 
                "?"}
            </div>
            <div>
              <p className="text-lg text-paper">{investigator.name || "Unknown"}</p>
              <p className="font-mono text-sm text-amber">
                {investigator.id || investigator.investigatorId || "N/A"}
              </p>
            </div>
          </div>

          {/* Details */}
          <div className="space-y-3 rounded-sm border border-hairline bg-ink p-4">
            {investigator.role && (
              <div>
                <p className="text-xs uppercase tracking-wide text-ash">Role</p>
                <p className="mt-1 text-sm text-paper">{investigator.role}</p>
              </div>
            )}

            {investigator.status && (
              <div>
                <p className="text-xs uppercase tracking-wide text-ash">Status</p>
                <div className="mt-1">
                  <span
                    className={`rounded-sm border px-2 py-0.5 text-xs ${
                      investigator.status === "Active"
                        ? "border-teal/40 bg-teal/10 text-teal"
                        : "border-hairline bg-raised text-ash"
                    }`}
                  >
                    {investigator.status}
                  </span>
                </div>
              </div>
            )}

            {investigator.cases !== undefined && (
              <div>
                <p className="text-xs uppercase tracking-wide text-ash">Active Cases</p>
                <p className="mt-1 text-sm text-paper">{investigator.cases}</p>
              </div>
            )}

            {investigator.orgId && (
              <div>
                <p className="text-xs uppercase tracking-wide text-ash">Organization</p>
                <p className="mt-1 font-mono text-sm text-paper">{investigator.orgId}</p>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-5 flex justify-end">
          <button
            onClick={onClose}
            className="rounded-sm border border-hairline px-4 py-2 text-sm text-ash hover:border-amber hover:text-amber transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
