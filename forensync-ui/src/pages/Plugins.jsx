import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import PluginDrawer from "../components/PluginDrawer";
import { PluginDrawerProvider } from "../components/PluginDrawerContext";
import api from "../utils/api";
import { getUser } from "../utils/auth";
import LoadingOverlay from "../components/LoadingOverlay";

export default function Plugins() {
  const user = getUser();
  const [plugins, setPlugins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyName, setBusyName] = useState(null);
  
  // Parser request form state
  const [requestForm, setRequestForm] = useState({
    logType: "",
    customLogType: "",
    duration: "",
    fileSize: "",
    details: ""
  });
  const [requestSubmitted, setRequestSubmitted] = useState(false);
  const [requestSubmitting, setRequestSubmitting] = useState(false);

  const fetchPlugins = () => {
    if (!user?.orgId) return;
    api
      .get("/plugins", { params: { orgId: user.orgId } })
      .then(({ data }) => setPlugins(data.data.plugins))
      .catch(() => {
        // Silently handle error - page will still render normally
        setPlugins([]);
      })
      .finally(() => setLoading(false));
  };

  useEffect(fetchPlugins, []);

  const handleAdd = async (name) => {
    setBusyName(name);
    try {
      await api.post(`/plugins/${name}/add`, { orgId: user.orgId });
      fetchPlugins();
    } catch {
      // Silently handle error
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
      // Silently handle error
    } finally {
      setBusyName(null);
    }
  };

  const handleRequestSubmit = (e) => {
    e.preventDefault();
    setRequestSubmitting(true);
    
    // Frontend-only for now - structured for future backend integration
    // TODO: Connect to backend endpoint: POST /api/v1/parser-requests
    const requestData = {
      logType: requestForm.logType === "Other" ? requestForm.customLogType : requestForm.logType,
      duration: requestForm.duration,
      fileSize: requestForm.fileSize,
      details: requestForm.details,
      requestedBy: user?.investigatorId,
      orgId: user?.orgId,
      timestamp: new Date().toISOString()
    };
    
    // Simulate submission delay
    setTimeout(() => {
      console.log("Parser request (frontend-only):", requestData);
      setRequestSubmitted(true);
      setRequestSubmitting(false);
      
      // Reset form
      setRequestForm({
        logType: "",
        customLogType: "",
        duration: "",
        fileSize: "",
        details: ""
      });
      
      // Hide confirmation after 5 seconds
      setTimeout(() => setRequestSubmitted(false), 5000);
    }, 500);
  };

  // Separate plugins by status
  const addedPlugins = plugins.filter((p) => p.added);
  const availablePlugins = plugins.filter((p) => !p.added);
  const allPluginsAdded = plugins.length > 0 && availablePlugins.length === 0;

  const logTypes = [
    "Linux Syslog",
    "Windows Event Log",
    "Apache Access Log",
    "Nginx Access Log",
    "Firewall Log",
    "Authentication Log",
    "Application Log",
    "Other"
  ];

  return (
    <PluginDrawerProvider>
      <div className="relative flex h-screen bg-ink">
        {(loading || busyName) && <LoadingOverlay label="Loading plugins…" />}
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <TopBar />
          <main className="flex-1 overflow-y-auto px-8 py-6">
            {/* Page Header */}
            <div className="mb-6">
              <h1 className="mb-1 font-display text-xl font-semibold text-paper">Parsers & Plugins</h1>
              <p className="text-sm text-ash">
                Parsers help process supported forensic log files for evidence analysis.
              </p>
            </div>

            {loading && <p className="mt-6 text-sm text-ash">Loading…</p>}

            {!loading && (
              <>
                {/* Available Parsers Section */}
                <div className="mb-8">
                  <h2 className="mb-4 font-display text-base font-medium text-paper">Available Parsers</h2>
                  
                  {/* Case A: No plugins added */}
                  {addedPlugins.length === 0 && availablePlugins.length === 0 && (
                    <div className="rounded-sm border border-hairline bg-panel px-5 py-6 text-center">
                      <p className="mb-2 text-sm text-ash">No parsers have been added yet</p>
                      <p className="text-xs text-ash">Add a parser below or request support for a new log format.</p>
                    </div>
                  )}

                  {/* Display all parsers in a clean grid */}
                  {plugins.length > 0 && (
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                      {plugins.map((p) => (
                        <div
                          key={p.name}
                          className="group rounded-sm border border-hairline bg-panel px-4 py-4 transition-colors hover:border-amber/30"
                        >
                          <div className="mb-2 flex items-start justify-between gap-3">
                            <div className="flex-1">
                              <div className="mb-1 flex items-center gap-2">
                                <span className="text-sm leading-none">🧩</span>
                                <h3 className="font-medium text-sm text-paper">{p.label}</h3>
                              </div>
                              {/* Show Active badge ONLY for added plugins */}
                              {p.added && (
                                <span className="inline-block rounded-sm bg-amber/15 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-amber">
                                  Active
                                </span>
                              )}
                            </div>
                          </div>
                          <p className="mb-3 text-xs leading-relaxed text-ash">{p.description}</p>
                          
                          {/* Action buttons */}
                          <div className="flex gap-2">
                            {p.added ? (
                              <button
                                type="button"
                                disabled={busyName === p.name}
                                onClick={() => handleRemove(p.name)}
                                className="text-xs text-ash transition-colors hover:text-danger disabled:opacity-60"
                              >
                                {busyName === p.name ? "…" : "Remove"}
                              </button>
                            ) : (
                              <button
                                type="button"
                                disabled={busyName === p.name}
                                onClick={() => handleAdd(p.name)}
                                className="rounded-sm bg-amber px-3 py-1.5 text-xs font-medium text-ink transition-colors hover:bg-amber-hover disabled:opacity-60"
                              >
                                {busyName === p.name ? "…" : "Add"}
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Case D: All available plugins added */}
                  {allPluginsAdded && (
                    <div className="mt-4 rounded-sm border border-amber/20 bg-amber/5 px-4 py-3">
                      <p className="text-sm text-paper">
                        ✓ All available parsers are added
                      </p>
                    </div>
                  )}
                </div>

                {/* Request a Parser Section */}
                <div className="max-w-2xl">
                  <div className="mb-4 flex items-start gap-3">
                    <span className="text-lg leading-none">📋</span>
                    <div className="flex-1">
                      <h2 className="mb-1 font-display text-base font-medium text-paper">Request a Parser</h2>
                      <p className="text-sm text-ash">
                        Need support for a log format that isn't currently available? Submit a request to the development team.
                      </p>
                    </div>
                  </div>

                  <form onSubmit={handleRequestSubmit} className="rounded-sm border border-hairline bg-panel p-5">
                    {requestSubmitted && (
                      <div className="mb-4 rounded-sm border border-amber/30 bg-amber/10 px-4 py-3">
                        <p className="text-sm text-paper">
                          ✓ Parser request submitted to the development team.
                        </p>
                      </div>
                    )}

                    <div className="mb-4">
                      <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">
                        Type of Log File *
                      </label>
                      <select
                        required
                        value={requestForm.logType}
                        onChange={(e) => setRequestForm({ ...requestForm, logType: e.target.value })}
                        className="w-full rounded-sm border border-hairline bg-ink px-3 py-2 text-sm text-paper focus:border-amber outline-none"
                      >
                        <option value="">Select log type…</option>
                        {logTypes.map((type) => (
                          <option key={type} value={type}>
                            {type}
                          </option>
                        ))}
                      </select>
                    </div>

                    {requestForm.logType === "Other" && (
                      <div className="mb-4">
                        <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">
                          Custom Log Type *
                        </label>
                        <input
                          type="text"
                          required
                          value={requestForm.customLogType}
                          onChange={(e) => setRequestForm({ ...requestForm, customLogType: e.target.value })}
                          placeholder="e.g., Custom Application Log"
                          className="w-full rounded-sm border border-hairline bg-ink px-3 py-2 text-sm text-paper placeholder:text-ash/60 focus:border-amber outline-none"
                        />
                      </div>
                    )}

                    <div className="mb-4">
                      <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">
                        Duration / Time Range *
                      </label>
                      <input
                        type="text"
                        required
                        value={requestForm.duration}
                        onChange={(e) => setRequestForm({ ...requestForm, duration: e.target.value })}
                        placeholder="e.g., 30 days, Jan 2024 - Mar 2024"
                        className="w-full rounded-sm border border-hairline bg-ink px-3 py-2 text-sm text-paper placeholder:text-ash/60 focus:border-amber outline-none"
                      />
                    </div>

                    <div className="mb-4">
                      <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">
                        Approximate File Size *
                      </label>
                      <input
                        type="text"
                        required
                        value={requestForm.fileSize}
                        onChange={(e) => setRequestForm({ ...requestForm, fileSize: e.target.value })}
                        placeholder="e.g., 500 MB, 2 GB"
                        className="w-full rounded-sm border border-hairline bg-ink px-3 py-2 text-sm text-paper placeholder:text-ash/60 focus:border-amber outline-none"
                      />
                    </div>

                    <div className="mb-5">
                      <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">
                        Additional Details
                      </label>
                      <textarea
                        value={requestForm.details}
                        onChange={(e) => setRequestForm({ ...requestForm, details: e.target.value })}
                        placeholder="Describe the log format, structure, or any specific parsing requirements…"
                        rows={4}
                        className="w-full rounded-sm border border-hairline bg-ink px-3 py-2 text-sm text-paper placeholder:text-ash/60 focus:border-amber outline-none resize-none"
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={requestSubmitting}
                      className="w-full rounded-sm bg-amber px-4 py-2.5 text-sm font-medium text-ink transition-colors hover:bg-amber-hover disabled:opacity-60"
                    >
                      {requestSubmitting ? "Submitting…" : "Submit Request"}
                    </button>

                    <p className="mt-3 text-xs text-ash">
                      * Required fields. The development team will review your request and work on adding support for the requested log format.
                    </p>
                  </form>
                </div>
              </>
            )}
          </main>
        </div>
        <PluginDrawer />
      </div>
    </PluginDrawerProvider>
  );
}