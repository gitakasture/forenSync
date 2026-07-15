import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

let nextId = 1;

export default function Register() {
  const navigate = useNavigate();
  const [orgName, setOrgName] = useState("");
  const [orgId, setOrgId] = useState("");
  const [orgHeadId, setOrgHeadId] = useState("");
  const [investigators, setInvestigators] = useState([]);
  const [draft, setDraft] = useState({ name: "", id: "" });

  const addInvestigator = () => {
    if (!draft.name.trim() || !draft.id.trim()) return;
    setInvestigators([...investigators, { ...draft, key: nextId++ }]);
    setDraft({ name: "", id: "" });
  };

  const removeInvestigator = (key) => {
    setInvestigators(investigators.filter((inv) => inv.key !== key));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Mock registration — replace with real Axios call once the backend exists.
    navigate("/login");
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-ink px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <p className="font-display text-2xl font-semibold text-paper">ForenSync</p>
          <p className="mt-1 font-mono text-xs tracking-wide text-ash">ORGANIZATION REGISTRATION</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-sm border border-hairline bg-panel p-7"
        >
          <div className="mb-5">
            <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">Name</label>
            <input
              type="text"
              required
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              placeholder="Organization name"
              className="w-full rounded-sm border border-hairline bg-ink px-3 py-2.5 text-sm text-paper placeholder:text-ash/60 focus:border-amber outline-none"
            />
          </div>

          <div className="mb-6">
            <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">Org ID</label>
            <input
              type="text"
              required
              value={orgId}
              onChange={(e) => setOrgId(e.target.value)}
              placeholder="ORG-XXXX"
              className="w-full rounded-sm border border-hairline bg-ink px-3 py-2.5 font-mono text-sm text-paper placeholder:text-ash/60 focus:border-amber outline-none"
            />
          </div>

          <div className="mb-6">
            <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">Organization Head ID</label>
            <input
              type="text"
              required
              value={orgHeadId}
              onChange={(e) => setOrgHeadId(e.target.value)}
              placeholder="HEAD-XXXX"
              className="w-full rounded-sm border border-hairline bg-ink px-3 py-2.5 font-mono text-sm text-paper placeholder:text-ash/60 focus:border-amber outline-none"
            />
          </div>

          <div className="mb-4 border-t border-hairline pt-5">
            <p className="mb-3 text-xs uppercase tracking-wide text-ash">Investigators</p>

            {investigators.length > 0 && (
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
            )}

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
          </div>

          <button
            type="submit"
            className="mt-6 w-full rounded-sm bg-amber py-2.5 text-sm font-medium text-ink transition-colors hover:bg-amber-hover"
          >
            Register
          </button>

          <p className="mt-5 text-center text-sm text-ash">
            Already registered?{" "}
            <Link to="/login" className="text-amber hover:text-amber-hover hover:underline">
              Login
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
