import { useEffect, useState } from "react";
import api from "../utils/api";
import { getUser } from "../utils/auth";

export default function CaseDetailModal({ caseId, onClose }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const user = getUser();

  useEffect(() => {
    if (!caseId || !user?.orgId) return;
    api
      .get(`/cases/${caseId}`, { params: { orgId: user.orgId } })
      .then(({ data }) => setDetail(data.data.case))
      .catch(() => setError("Could not load case details."))
      .finally(() => setLoading(false));
  }, [caseId]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4" onClick={onClose}>
      <div
        className="relative w-full max-w-lg rounded-sm border border-hairline bg-panel p-7 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <button onClick={onClose} className="mb-4 text-xs text-ash hover:text-amber transition-colors">
          ← Back to My Cases
        </button>

        {loading && <p className="text-sm text-ash">Loading…</p>}
        {error && <p className="text-sm text-danger">{error}</p>}

        {detail && (
          <>
            <p className="mb-1 font-mono text-xs text-amber">{detail.caseId}</p>
            <h1 className="mb-5 font-display text-xl font-medium text-paper">{detail.name}</h1>

            <div className="mb-5 rounded-sm border border-hairline bg-ink p-4">
              <p className="mb-1 text-xs uppercase tracking-wide text-ash">Description</p>
              <p className="text-sm text-paper">{detail.description || "No description provided."}</p>
            </div>

            <div className="mb-5 grid grid-cols-2 gap-4">
              <div>
                <p className="mb-1 text-xs uppercase tracking-wide text-ash">Created By</p>
                <p className="text-sm text-paper">{detail.createdBy.name}</p>
                <p className="text-xs text-ash">{detail.createdBy.role}</p>
              </div>
              <div>
                <p className="mb-1 text-xs uppercase tracking-wide text-ash">Created On</p>
                <p className="font-mono text-sm text-paper">{detail.createdOn}</p>
              </div>
            </div>

            <div>
              <p className="mb-2 text-xs uppercase tracking-wide text-ash">Assigned Investigators</p>
              <div className="flex flex-wrap gap-2">
                {detail.investigators.map((inv) => (
                  <span
                    key={inv.id}
                    className="flex items-center gap-2 rounded-sm border border-hairline bg-raised px-3 py-1.5 text-sm text-paper"
                  >
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-amber/20 font-mono text-[10px] text-amber">
                      {inv.initials}
                    </span>
                    {inv.name}
                    {inv.id === user?.investigatorId ? " (You)" : ""}
                  </span>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}