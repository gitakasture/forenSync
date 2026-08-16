import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import PluginDrawer from "../components/PluginDrawer";
import { PluginDrawerProvider } from "../components/PluginDrawerContext";
import api from "../utils/api";
import { getUser } from "../utils/auth";

export default function Plugins() {
  const user = getUser();
  const [plugins, setPlugins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyName, setBusyName] = useState(null);
  const [error, setError] = useState("");

  const fetchPlugins = () => {
    if (!user?.orgId) return;
    api
      .get("/plugins", { params: { orgId: user.orgId } })
      .then(({ data }) => setPlugins(data.data.plugins))
      .catch(() => setError("Could not load plugins."))
      .finally(() => setLoading(false));
  };

  useEffect(fetchPlugins, []);

  const handleAdd = async (name) => {
    setBusyName(name);
    try {
      await api.post(`/plugins/${name}/add`, { orgId: user.orgId });
      fetchPlugins();
    } catch {
      setError("Failed to add plugin.");
    } finally {
      setBusyName(null);
    }
  };

  const handleRemove = async (name) => {
    setBusyName(name);
    try {
      await api.post(`/plugins/${name}/remove`, { orgId: user.orgId });
      fetchPlugins();
    } catch {
      setError("Failed to remove plugin.");
    } finally {
      setBusyName(null);
    }
  };

  const addedPlugins = plugins.filter((p) => p.added);
  const availablePlugins = plugins.filter((p) => !p.added);

  return (
    <PluginDrawerProvider>
      <div className="relative flex h-screen bg-ink">
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <TopBar />
          <main className="flex-1 overflow-y-auto px-8 py-6">
            <h1 className="mb-1 font-display text-lg font-medium text-paper">Plugins</h1>
            <p className="mt-1 text-sm text-ash">
              Manage the log-parsing plugins used to ingest evidence for your cases.
            </p>

            {loading && <p className="mt-6 text-sm text-ash">Loading…</p>}
            {error && <p className="mt-6 text-sm text-danger">{error}</p>}

            <div className="mt-6 max-w-md">
              <p className="mb-3 text-[11px] uppercase tracking-wide text-ash">Added Plugins</p>
              {addedPlugins.length === 0 ? (
                <p className="rounded-sm border border-hairline bg-panel px-4 py-4 text-sm italic text-ash">
                  No plugins added yet.
                </p>
              ) : (
                <ul className="space-y-2">
                  {addedPlugins.map((p) => (
                    <li key={p.name} className="rounded-sm border border-hairline bg-panel px-4 py-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-paper">{p.label}</span>
                        <button
                          type="button"
                          disabled={busyName === p.name}
                          onClick={() => handleRemove(p.name)}
                          className="text-xs text-ash transition-colors hover:text-danger disabled:opacity-60"
                        >
                          {busyName === p.name ? "…" : "Remove"}
                        </button>
                      </div>
                      <p className="mt-1 text-xs text-ash">{p.description}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="mt-6 max-w-md">
              <p className="mb-3 text-[11px] uppercase tracking-wide text-ash">Available Plugins</p>
              {availablePlugins.length === 0 ? (
                <p className="text-sm italic text-ash">All available plugins have been added.</p>
              ) : (
                <ul className="space-y-2">
                  {availablePlugins.map((p) => (
                    <li key={p.name} className="rounded-sm border border-hairline bg-panel px-4 py-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-paper">{p.label}</span>
                        <button
                          type="button"
                          disabled={busyName === p.name}
                          onClick={() => handleAdd(p.name)}
                          className="text-xs text-ash transition-colors hover:text-amber disabled:opacity-60"
                        >
                          {busyName === p.name ? "…" : "Add"}
                        </button>
                      </div>
                      <p className="mt-1 text-xs text-ash">{p.description}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </main>
        </div>
        <PluginDrawer />
      </div>
    </PluginDrawerProvider>
  );
}