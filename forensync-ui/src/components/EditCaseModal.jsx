import { useState } from "react";
import api from "../utils/api";
import { getUser } from "../utils/auth";
import LoadingOverlay from "../components/LoadingOverlay";

export default function EditCaseModal({ caseData, onClose, onUpdated }) {
  const user = getUser();
  const [form, setForm] = useState({
    name: caseData.name,
    description: caseData.description || "",
    priority: caseData.priority,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleSave = async () => {
    setSaving(true);
    setError("");
    try {
      await api.put(`/cases/${caseData.caseId}`, { orgId: user.orgId, ...form });
      onUpdated();
      onClose();
    } catch (err) {
      setError(err.response?.data?.message || "Failed to update case.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4" onClick={onClose}>
      {saving && <LoadingOverlay label="Saving case…" />}   
      <div className="relative w-full max-w-md rounded-sm border border-hairline bg-panel p-7 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <h1 className="mb-6 font-display text-xl font-medium text-paper">Edit Case — {caseData.caseId}</h1>

        <div className="mb-5">
          <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">Case Name</label>
          <input
            type="text"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full rounded-sm border border-hairline bg-ink px-3 py-2 text-sm text-paper focus:border-amber outline-none"
          />
        </div>

        <div className="mb-5">
          <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">Description</label>
          <textarea
            rows={3}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            className="w-full resize-none rounded-sm border border-hairline bg-ink px-3 py-2 text-sm text-paper focus:border-amber outline-none"
          />
        </div>

        <div className="mb-6">
          <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">Priority</label>
          <select
            value={form.priority}
            onChange={(e) => setForm({ ...form, priority: e.target.value })}
            className="w-full rounded-sm border border-hairline bg-ink px-3 py-2 text-sm text-paper focus:border-amber outline-none"
          >
            <option>Critical</option>
            <option>High Priority</option>
            <option>Medium Priority</option>
            <option>Low Priority</option>
          </select>
        </div>

        {error && <p className="mb-4 text-xs text-danger">{error}</p>}

        <div className="flex gap-3">
          <button onClick={onClose} className="flex-1 rounded-sm border border-hairline py-2.5 text-sm text-ash transition-colors hover:border-amber hover:text-amber">
            Cancel
          </button>
          <button onClick={handleSave} disabled={saving} className="flex-1 rounded-sm bg-amber py-2.5 text-sm font-medium text-ink transition-colors hover:bg-amber-hover disabled:opacity-60">
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}