import { useState, useEffect } from "react";
import api from "../utils/api";
import { getUser } from "../utils/auth";

function getTodayISO() {
  return new Date().toISOString().split("T")[0];
}

export default function NewCaseModal({ onClose }) {
  const [form, setForm] = useState({
    name: "",
    description: "",
    investigatorIds: [],
    date: getTodayISO(),
  });
  const [investigators, setInvestigators] = useState([]);
  const [loadingInvestigators, setLoadingInvestigators] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const user = getUser();

  useEffect(() => {
    if (!user?.orgId) return;
    api
      .get("/users", { params: { orgId: user.orgId, role: "investigator" } })
      .then(({ data }) => setInvestigators(data.data.users))
      .catch(() => setError("Could not load investigators."))
      .finally(() => setLoadingInvestigators(false));
  }, []);

  const toggleInvestigator = (id) => {
    setForm((f) => ({
      ...f,
      investigatorIds: f.investigatorIds.includes(id)
        ? f.investigatorIds.filter((x) => x !== id)
        : [...f.investigatorIds, id],
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.investigatorIds.length === 0) {
      setError("Assign at least one investigator.");
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      await api.post("/cases", {
        name: form.name,
        description: form.description,
        orgId: user.orgId,
        createdBy: user.investigatorId, // head's own user_id
        investigatorIds: form.investigatorIds,
        from: form.date,
      });
      onClose();
    } catch (err) {
      setError(err.response?.data?.message || "Failed to create case.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4" onClick={onClose}>
      <div className="relative w-full max-w-lg rounded-sm border border-hairline bg-panel p-7 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <h1 className="mb-1 font-display text-xl font-medium text-paper">New Case</h1>
        <p className="mb-6 text-sm text-ash">Create a case and assign investigators.</p>

        <form onSubmit={handleSubmit}>
          <div className="mb-5">
            <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">Case Name</label>
            <input
              type="text" required value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="e.g. Unauthorized SSH Access — prod-web-03"
              className="w-full rounded-sm border border-hairline bg-ink px-3 py-2.5 text-sm text-paper placeholder:text-ash/60 focus:border-amber outline-none"
            />
          </div>

          <div className="mb-5">
            <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">Description</label>
            <textarea
              rows={3} value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Brief summary of the incident…"
              className="w-full resize-none rounded-sm border border-hairline bg-ink px-3 py-2.5 text-sm text-paper placeholder:text-ash/60 focus:border-amber outline-none"
            />
          </div>

          <div className="mb-5">
            <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">Assign Investigators</label>
            {loadingInvestigators ? (
              <p className="text-xs text-ash">Loading investigators…</p>
            ) : (
              <div className="max-h-40 space-y-1.5 overflow-y-auto rounded-sm border border-hairline bg-ink p-2">
                {investigators.map((inv) => (
                  <label key={inv.id} className="flex cursor-pointer items-center gap-2 rounded-sm px-2 py-1.5 text-sm text-paper hover:bg-raised">
                    <input
                      type="checkbox"
                      checked={form.investigatorIds.includes(inv.id)}
                      onChange={() => toggleInvestigator(inv.id)}
                      className="accent-amber"
                    />
                    {inv.name}
                    <span className="ml-auto font-mono text-[11px] text-ash">{inv.id}</span>
                  </label>
                ))}
              </div>
            )}
          </div>

          <div className="mb-7">
            <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">Date</label>
            <input
              type="date" value={form.date}
              onChange={(e) => setForm({ ...form, date: e.target.value })}
              className="w-full rounded-sm border border-hairline bg-ink px-3 py-2 font-mono text-sm text-paper focus:border-amber outline-none"
            />
          </div>

          {error && <p className="mb-4 text-xs text-danger">{error}</p>}

          <div className="flex gap-3">
            <button type="button" onClick={onClose} className="flex-1 rounded-sm border border-hairline py-2.5 text-sm text-ash transition-colors hover:border-amber hover:text-amber">
              Cancel
            </button>
            <button type="submit" disabled={submitting} className="flex-1 rounded-sm bg-amber py-2.5 text-sm font-medium text-ink transition-colors hover:bg-amber-hover disabled:opacity-60">
              {submitting ? "Creating…" : "Create Case"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}