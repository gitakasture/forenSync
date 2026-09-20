import { useEffect, useState } from "react";
import api from "../utils/api";
import { getUser } from "../utils/auth";
import LoadingOverlay from "../components/LoadingOverlay";

export default function ManageInvestigatorsModal({ onClose }) {
  const user = getUser();
  const [investigators, setInvestigators] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newInv, setNewInv] = useState({ id: "", name: "" });
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState("");

  const fetchInvestigators = () => {
    api
      .get("/users", { params: { orgId: user.orgId, role: "investigator" } })
      .then(({ data }) => setInvestigators(data.data.users))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(fetchInvestigators, []);

  const handleAdd = async () => {
    if (!newInv.id.trim() || !newInv.name.trim()) {
      setError("Both ID and name are required.");
      return;
    }
    setAdding(true);
    setError("");
    try {
      await api.post("/users", { orgId: user.orgId, id: newInv.id.trim(), name: newInv.name.trim() });
      setNewInv({ id: "", name: "" });
      fetchInvestigators();
    } catch (err) {
      setError(err.response?.data?.message || "Failed to add investigator.");
    } finally {
      setAdding(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4" onClick={onClose}>
      {(loading || busy) && <LoadingOverlay label="Loading…" />}

      <div className="relative w-full max-w-md max-h-[85vh] overflow-y-auto rounded-sm border border-hairline bg-panel p-7 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <h1 className="mb-6 font-display text-xl font-medium text-paper">Manage Investigators</h1>

        <p className="mb-2 text-xs uppercase tracking-wide text-ash">Current Investigators</p>
        {loading && <p className="text-sm text-ash">Loading…</p>}
        {!loading && investigators.length === 0 && <p className="text-sm italic text-ash">No investigators added yet.</p>}
        <div className="mb-6 max-h-48 space-y-1.5 overflow-y-auto">
          {investigators.map((inv) => (
            <div key={inv.id} className="flex items-center justify-between rounded-sm border border-hairline bg-ink px-3 py-1.5">
              <span className="text-sm text-paper">{inv.name}</span>
              <span className="font-mono text-[11px] text-ash">{inv.id}</span>
            </div>
          ))}
        </div>

        <div className="rounded-sm border border-hairline bg-ink p-3">
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
          {error && <p className="mb-2 text-xs text-danger">{error}</p>}
          <button
            onClick={handleAdd}
            disabled={adding}
            className="w-full rounded-sm bg-amber py-1.5 text-xs font-medium text-ink transition-colors hover:bg-amber-hover disabled:opacity-60"
          >
            {adding ? "Adding…" : "+ Add & Save"}
          </button>
        </div>

        <button
          onClick={onClose}
          className="mt-6 w-full rounded-sm border border-hairline py-2.5 text-sm text-ash transition-colors hover:border-amber hover:text-amber"
        >
          Close
        </button>
      </div>
    </div>
  );
}