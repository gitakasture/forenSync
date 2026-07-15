import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { mockInvestigator, supportedFormats } from "../data/mockData";
import { isOrgHead, logout } from "../utils/auth";

let nextId = 100;

export default function SystemSettings() {
  const navigate = useNavigate();
  const [orgName, setOrgName] = useState(mockInvestigator.orgName);
  const [orgId] = useState(mockInvestigator.orgId);
  const [investigators, setInvestigators] = useState([
    { key: nextId++, name: "Aditi Rao", id: "INV-2291" },
    { key: nextId++, name: "Rohan Mehta", id: "INV-2287" },
  ]);
  const [draft, setDraft] = useState({ name: "", id: "" });
  const [formats, setFormats] = useState(
    supportedFormats.reduce((acc, f) => ({ ...acc, [f.id]: true }), {})
  );

  // Extra safety net — if a non-head reaches this route directly, bounce them.
  if (!isOrgHead()) {
    return <Navigate to="/dashboard" replace />;
  }

  const addInvestigator = () => {
    if (!draft.name.trim() || !draft.id.trim()) return;
    setInvestigators([...investigators, { ...draft, key: nextId++ }]);
    setDraft({ name: "", id: "" });
  };

  const removeInvestigator = (key) => {
    setInvestigators(investigators.filter((inv) => inv.key !== key));
  };

  const toggleFormat = (id) => {
    setFormats({ ...formats, [id]: !formats[id] });
  };

  const handleDeactivate = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="flex h-screen bg-ink">
      <Sidebar />

      <main className="flex-1 overflow-y-auto px-8 py-8">
        <div className="mx-auto max-w-3xl space-y-6">
          <div>
            <h1 className="font-display text-xl font-medium text-paper">System Settings</h1>
            <p className="mt-1 text-sm text-ash">Organization Head access only.</p>
          </div>

          {/* Organization details */}
          <section className="rounded-sm border border-hairline bg-panel p-6">
            <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-ash">
              Organization Details
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">Name</label>
                <input
                  type="text"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  className="w-full rounded-sm border border-hairline bg-ink px-3 py-2 text-sm text-paper focus:border-amber outline-none"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">Org ID</label>
                <input
                  type="text"
                  value={orgId}
                  disabled
                  className="w-full cursor-not-allowed rounded-sm border border-hairline bg-raised px-3 py-2 font-mono text-sm text-ash"
                />
              </div>
            </div>
          </section>

          {/* Manage investigators */}
          <section className="rounded-sm border border-hairline bg-panel p-6">
            <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-ash">
              Manage Investigators
            </h2>

            <ul className="mb-4 space-y-2">
              {investigators.map((inv) => (
                <li
                  key={inv.key}
                  className="flex items-center justify-between rounded-sm border border-hairline bg-ink px-3 py-2"
                >
                  <span className="text-sm text-paper">{inv.name}</span>
                  <span className="font-mono text-xs text-amber">{inv.id}</span>
                  <button
                    type="button"
                    onClick={() => removeInvestigator(inv.key)}
                    className="ml-3 text-ash hover:text-danger"
                    aria-label={`Remove ${inv.name}`}
                  >
                    ✕
                  </button>
                </li>
              ))}
            </ul>

            <div className="flex gap-2">
              <input
                type="text"
                value={draft.name}
                onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                placeholder="Name"
                className="w-1/2 rounded-sm border border-hairline bg-ink px-3 py-2 text-sm text-paper placeholder:text-ash/60 focus:border-amber outline-none"
              />
              <input
                type="text"
                value={draft.id}
                onChange={(e) => setDraft({ ...draft, id: e.target.value })}
                placeholder="ID"
                className="w-1/2 rounded-sm border border-hairline bg-ink px-3 py-2 font-mono text-sm text-paper placeholder:text-ash/60 focus:border-amber outline-none"
              />
            </div>
            <button
              type="button"
              onClick={addInvestigator}
              className="mt-2 w-full rounded-sm border border-hairline py-2 text-sm text-ash transition-colors hover:border-amber hover:text-amber"
            >
              + Add Investigator
            </button>
          </section>

          {/* Ingestion formats */}
          <section className="rounded-sm border border-hairline bg-panel p-6">
            <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-ash">
              Ingestion Format Management
            </h2>
            <ul className="space-y-3">
              {supportedFormats.map((fmt) => (
                <li key={fmt.id} className="flex items-center justify-between">
                  <span className="text-sm text-paper">{fmt.label}</span>
                  <button
                    type="button"
                    onClick={() => toggleFormat(fmt.id)}
                    className={`rounded-sm border px-3 py-1 text-xs transition-colors ${
                      formats[fmt.id]
                        ? "border-teal/40 bg-teal/10 text-teal"
                        : "border-hairline bg-ink text-ash"
                    }`}
                  >
                    {formats[fmt.id] ? "Enabled" : "Disabled"}
                  </button>
                </li>
              ))}
            </ul>
          </section>

          {/* Danger zone */}
          <section className="rounded-sm border border-danger/30 bg-danger/5 p-6">
            <h2 className="mb-2 text-sm font-medium uppercase tracking-wide text-danger">
              Danger Zone
            </h2>
            <p className="mb-4 text-sm text-ash">
              Deactivating the organization revokes access for all investigators immediately.
            </p>
            <button
              type="button"
              onClick={handleDeactivate}
              className="rounded-sm border border-danger px-4 py-2 text-sm text-danger transition-colors hover:bg-danger hover:text-ink"
            >
              Deactivate Organization
            </button>
          </section>
        </div>
      </main>
    </div>
  );
}
