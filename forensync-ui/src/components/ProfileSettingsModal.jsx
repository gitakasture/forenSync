import { useState } from "react";
import api from "../utils/api";
import { getUser, setUser as persistUser, isOrgHead } from "../utils/auth";
import LoadingOverlay from "../components/LoadingOverlay";

export default function ProfileSettingsModal({ onClose }) {
  const head = isOrgHead();
  const user = getUser();

  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ orgName: user?.orgName || "", headName: user?.name || "" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleSave = async () => {
    setSaving(true);
    setError("");
    try {
      await api.put("/profile", {
        orgId: user.orgId,
        headUserId: user.investigatorId,
        orgName: form.orgName,
        headName: form.headName,
      });
      persistUser({ ...user, orgName: form.orgName, name: form.headName });
      setEditing(false);
    } catch (err) {
      setError(err.response?.data?.message || "Failed to save changes.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4" onClick={onClose}>
      {saving && <LoadingOverlay label="Saving profile…" />}
      <div className="relative w-full max-w-md rounded-sm border border-hairline bg-panel p-7 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <h1 className="mb-6 font-display text-xl font-medium text-paper">Profile Settings</h1>

        <div className="mb-6 space-y-4">
          <div>
            <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">Organization Name</label>
            {editing && head ? (
              <input
                type="text"
                value={form.orgName}
                onChange={(e) => setForm({ ...form, orgName: e.target.value })}
                className="w-full rounded-sm border border-hairline bg-ink px-3 py-2 text-sm text-paper focus:border-amber outline-none"
              />
            ) : (
              <p className="text-sm text-paper">{user?.orgName}</p>
            )}
          </div>

          <div>
            <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">Organization ID</label>
            <p className="font-mono text-sm text-ash">{user?.orgId}</p>
          </div>

          <div>
            <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">
              {head ? "Head Name" : "Your Name"}
            </label>
            {editing && head ? (
              <input
                type="text"
                value={form.headName}
                onChange={(e) => setForm({ ...form, headName: e.target.value })}
                className="w-full rounded-sm border border-hairline bg-ink px-3 py-2 text-sm text-paper focus:border-amber outline-none"
              />
            ) : (
              <p className="text-sm text-paper">{user?.name}</p>
            )}
          </div>

          <div>
            <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">
              {head ? "Head ID" : "Investigator ID"}
            </label>
            <p className="font-mono text-sm text-ash">{user?.investigatorId}</p>
          </div>
        </div>

        {error && <p className="mb-4 text-xs text-danger">{error}</p>}

        {head && (
          <div className="flex gap-3">
            {!editing ? (
              <button
                onClick={() => setEditing(true)}
                className="flex-1 rounded-sm border border-hairline py-2.5 text-sm text-paper transition-colors hover:border-amber hover:text-amber"
              >
                Edit
              </button>
            ) : (
              <>
                <button
                  onClick={() => { setEditing(false); setForm({ orgName: user?.orgName || "", headName: user?.name || "" }); }}
                  className="flex-1 rounded-sm border border-hairline py-2.5 text-sm text-ash transition-colors hover:border-amber hover:text-amber"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="flex-1 rounded-sm bg-amber py-2.5 text-sm font-medium text-ink transition-colors hover:bg-amber-hover disabled:opacity-60"
                >
                  {saving ? "Saving…" : "Save"}
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}