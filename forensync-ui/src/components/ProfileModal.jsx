import { useEffect, useState } from "react";
import api from "../utils/api";
import { getUser, setUser as persistUser, isOrgHead } from "../utils/auth";

export default function ProfileModal({ onClose }) {
  const head = isOrgHead();
  const user = getUser();

  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ orgName: user?.orgName || "", headName: user?.name || "" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [investigators, setInvestigators] = useState([]);
  const [loadingInvestigators, setLoadingInvestigators] = useState(head);

  const [newInv, setNewInv] = useState({ id: "", name: "" });
  const [addingInv, setAddingInv] = useState(false);
  const [addError, setAddError] = useState("");

  const fetchInvestigators = () => {
    if (!head || !user?.orgId) return;
    api
      .get("/users", { params: { orgId: user.orgId, role: "investigator" } })
      .then(({ data }) => setInvestigators(data.data.users))
      .catch(() => {})
      .finally(() => setLoadingInvestigators(false));
  };

  useEffect(fetchInvestigators, []);

  const handleEdit = () => {
    setForm({ orgName: user?.orgName || "", headName: user?.name || "" });
    setEditing(true);
  };

  const handleCancel = () => {
    setForm({ orgName: user?.orgName || "", headName: user?.name || "" });
    setEditing(false);
    setError("");
  };

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

  const handleAddInvestigator = async () => {
    if (!newInv.id.trim() || !newInv.name.trim()) {
      setAddError("Both ID and name are required.");
      return;
    }
    setAddingInv(true);
    setAddError("");
    try {
      await api.post("/users", { orgId: user.orgId, id: newInv.id.trim(), name: newInv.name.trim() });
      setNewInv({ id: "", name: "" });
      fetchInvestigators();
    } catch (err) {
      setAddError(err.response?.data?.message || "Failed to add investigator.");
    } finally {
      setAddingInv(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4" onClick={onClose}>
      <div
        className="relative w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-sm border border-hairline bg-panel p-7 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h1 className="mb-6 font-display text-xl font-medium text-paper">Profile</h1>

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

        {head && (
          <>
            <div className="mb-4">
              <p className="mb-2 text-xs uppercase tracking-wide text-ash">Investigators</p>
              {loadingInvestigators && <p className="text-sm text-ash">Loading…</p>}
              {!loadingInvestigators && investigators.length === 0 && (
                <p className="text-sm italic text-ash">No investigators added yet.</p>
              )}
              <div className="max-h-40 space-y-1.5 overflow-y-auto">
                {investigators.map((inv) => (
                  <div key={inv.id} className="flex items-center justify-between rounded-sm border border-hairline bg-ink px-3 py-1.5">
                    <span className="text-sm text-paper">{inv.name}</span>
                    <span className="font-mono text-[11px] text-ash">{inv.id}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="mb-6 rounded-sm border border-hairline bg-ink p-3">
              <p className="mb-2 text-xs uppercase tracking-wide text-ash">Add New Investigator</p>
              <div className="mb-2 grid grid-cols-2 gap-2">
                <input
                  type="text"
                  value={newInv.name}
                  onChange={(e) => setNewInv({ ...newInv, name: e.target.value })}
                  placeholder="Name"
                  className="rounded-sm border border-hairline bg-panel px-2 py-1.5 text-xs text-paper placeholder:text-ash/60 focus:border-amber outline-none"
                />
                <input
                  type="text"
                  value={newInv.id}
                  onChange={(e) => setNewInv({ ...newInv, id: e.target.value })}
                  placeholder="Investigator ID"
                  className="rounded-sm border border-hairline bg-panel px-2 py-1.5 text-xs text-paper placeholder:text-ash/60 focus:border-amber outline-none"
                />
              </div>
              {addError && <p className="mb-2 text-xs text-danger">{addError}</p>}
              <button
                onClick={handleAddInvestigator}
                disabled={addingInv}
                className="w-full rounded-sm border border-hairline py-1.5 text-xs text-ash transition-colors hover:border-amber hover:text-amber disabled:opacity-60"
              >
                {addingInv ? "Adding…" : "+ Add Investigator"}
              </button>
            </div>
          </>
        )}

        {error && <p className="mb-4 text-xs text-danger">{error}</p>}

        {head && (
          <div className="flex gap-3">
            {!editing ? (
              <button
                onClick={handleEdit}
                className="flex-1 rounded-sm border border-hairline py-2.5 text-sm text-paper transition-colors hover:border-amber hover:text-amber"
              >
                Edit
              </button>
            ) : (
              <>
                <button
                  onClick={handleCancel}
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