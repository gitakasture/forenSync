import { useEffect, useState } from "react";
import api from "../utils/api";
import { getUser } from "../utils/auth";
import { getTheme, applyTheme } from "../utils/theme";

export default function SystemSettingsModal({ onClose }) {
  const user = getUser();
  const [form, setForm] = useState({ defaultPriority: "Medium Priority", defaultCorrelationWindow: 30 });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [theme, setTheme] = useState(getTheme());

  useEffect(() => {
    api
      .get("/organizations/settings", { params: { orgId: user.orgId } })
      .then(({ data }) => setForm(data.data))
      .catch(() => setError("Could not load settings."))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError("");
    setSaved(false);
    try {
      await api.put("/organizations/settings", {
        orgId: user.orgId,
        defaultPriority: form.defaultPriority,
        defaultCorrelationWindow: form.defaultCorrelationWindow,
      });
      setSaved(true);
    } catch (err) {
      setError(err.response?.data?.message || "Failed to save settings.");
    } finally {
      setSaving(false);
    }
  };

  const handleThemeToggle = () => {
    const newTheme = theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    applyTheme(newTheme);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4" onClick={onClose}>
      <div className="relative w-full max-w-md rounded-sm border border-hairline bg-panel p-7 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <h1 className="mb-1 font-display text-xl font-medium text-paper">System Settings</h1>
        <p className="mb-6 text-sm text-ash">Default behavior for new cases and timelines in your organization.</p>

        {loading && <p className="text-sm text-ash">Loading…</p>}

        {!loading && (
          <div className="mb-6 space-y-4">
            <div>
              <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">Default Case Priority</label>
              <select
                value={form.defaultPriority}
                onChange={(e) => setForm({ ...form, defaultPriority: e.target.value })}
                className="w-full rounded-sm border border-hairline bg-ink px-3 py-2 text-sm text-paper focus:border-amber outline-none"
              >
                <option>Critical</option>
                <option>High Priority</option>
                <option>Medium Priority</option>
                <option>Low Priority</option>
              </select>
            </div>

            <div>
              <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">
                Default Correlation Window (minutes)
              </label>
              <input
                type="number"
                min="1"
                value={form.defaultCorrelationWindow}
                onChange={(e) => setForm({ ...form, defaultCorrelationWindow: Number(e.target.value) })}
                className="w-full rounded-sm border border-hairline bg-ink px-3 py-2 text-sm text-paper focus:border-amber outline-none"
              />
              <p className="mt-1 text-[11px] text-ash">
                Events from the same actor and host within this many minutes are grouped into one session during timeline generation.
              </p>
            </div>

            <div>
              <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">Appearance</label>
              <div className="flex items-center justify-between rounded-sm border border-hairline bg-ink px-3 py-2.5">
                <span className="text-sm text-paper">{theme === "dark" ? "Dark Mode" : "Light Mode"}</span>
                <button
                  onClick={handleThemeToggle}
                  className={`relative h-6 w-11 rounded-full transition-colors ${theme === "dark" ? "bg-hairline" : "bg-amber"}`}
                >
                  <span
                    className={`absolute top-0.5 h-5 w-5 rounded-full bg-paper transition-transform ${
                      theme === "dark" ? "translate-x-0.5" : "translate-x-5"
                    }`}
                  />
                </button>
              </div>
              <p className="mt-1 text-[11px] text-ash">Applies instantly, saved only on this device.</p>
            </div>
            
          </div>
        )}

        {error && <p className="mb-4 text-xs text-danger">{error}</p>}
        {saved && <p className="mb-4 text-xs text-teal">✓ Settings saved.</p>}

        <div className="flex gap-3">
          <button onClick={onClose} className="flex-1 rounded-sm border border-hairline py-2.5 text-sm text-ash transition-colors hover:border-amber hover:text-amber">
            Close
          </button>
          <button
            onClick={handleSave}
            disabled={saving || loading}
            className="flex-1 rounded-sm bg-amber py-2.5 text-sm font-medium text-ink transition-colors hover:bg-amber-hover disabled:opacity-60"
          >
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}