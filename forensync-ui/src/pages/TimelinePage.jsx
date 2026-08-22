import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import PluginDrawer from "../components/PluginDrawer";
import { PluginDrawerProvider } from "../components/PluginDrawerContext";
import api from "../utils/api";
import { getUser } from "../utils/auth";
import TimelineSwimlane from "../components/TimelineSwimlane";

function formatTime(ts) {
  if (!ts) return "Unknown";
  return ts.replace("T", " ").replace("Z", " UTC");
}

function toCSV(events) {
  const headers = ["timestamp", "source", "host", "actor", "action", "object", "result", "session_id"];
  const rows = events.map((e) => headers.map((h) => `"${(e[h] ?? "").toString().replace(/"/g, '""')}"`).join(","));
  return [headers.join(","), ...rows].join("\n");
}

export default function TimelinePage() {
  const { caseId } = useParams();
  const navigate = useNavigate();
  const user = getUser();

  const [events, setEvents] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState({ actor: "", host: "", source: "", action: "" });
  const [viewMode, setViewMode] = useState("table");
  const [selectedEvent, setSelectedEvent] = useState(null);

  const [savedViews, setSavedViews] = useState([]);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [viewName, setViewName] = useState("");

  const [page, setPage] = useState(0);
  const PAGE_SIZE = 100;

  const fetchTimeline = () => {
    if (!caseId || !user?.orgId) return;
    setLoading(true);
    setError("");
    const params = { orgId: user.orgId };
    Object.entries(filters).forEach(([k, v]) => { if (v) params[k] = v; });

    api
      .get(`/cases/${caseId}/timeline`, { params })
      .then(({ data }) => {
        setEvents(data.data.events);
        setStats(data.data.stats);
      })
      .catch(() => setError("Could not load timeline."))
      .finally(() => setLoading(false));
  };

  useEffect(fetchTimeline, [caseId]);

  const fetchSavedViews = () => {
    if (!caseId || !user?.orgId || !user?.investigatorId) return;
    api
      .get(`/cases/${caseId}/saved-views`, { params: { orgId: user.orgId, userId: user.investigatorId } })
      .then(({ data }) => setSavedViews(data.data.views))
      .catch(() => {});
  };
  useEffect(fetchSavedViews, [caseId]);

  const handleApplyFilters = () => {
    setPage(0);
    fetchTimeline();
  };
  const handleClearFilters = () => {
    setPage(0);
    setFilters({ actor: "", host: "", source: "", action: "" });
    setTimeout(fetchTimeline, 0);
  };

  const handleExport = () => {
    const csv = toCSV(events);
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${caseId}_timeline.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleSaveView = async () => {
    if (!viewName.trim()) return;
    try {
      await api.post(`/cases/${caseId}/saved-views`, {
        orgId: user.orgId,
        userId: user.investigatorId,
        name: viewName.trim(),
        filters,
        viewMode,
      });
      setViewName("");
      setShowSaveDialog(false);
      fetchSavedViews();
    } catch {
      setError("Failed to save view.");
    }
  };

  const handleLoadView = (view) => {
    setFilters({ actor: "", host: "", source: "", action: "", ...view.filters });
    setViewMode(view.viewMode);
    setPage(0);
    setTimeout(fetchTimeline, 0);
  };

  const handleDeleteView = async (viewId) => {
    try {
      await api.delete(`/saved-views/${viewId}`, { params: { orgId: user.orgId, userId: user.investigatorId } });
      fetchSavedViews();
    } catch {
      setError("Failed to delete view.");
    }
  };


  // Distinct filter options, derived from currently loaded events
  const distinct = (field) => [...new Set(events.map((e) => e[field]).filter(Boolean))];

  const pagedEvents = events.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  const totalPages = Math.ceil(events.length / PAGE_SIZE);

  let lastSessionId = null;

  return (
    <PluginDrawerProvider>
      <div className="relative flex h-screen bg-ink">
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <TopBar />
          <main className="flex-1 overflow-y-auto px-8 py-6">
            <button onClick={() => navigate(-1)} className="mb-4 text-xs text-ash hover:text-amber transition-colors">
              ← Back
            </button>

            <div className="mb-5 flex items-center justify-between">
              <div>
                <h1 className="font-display text-lg font-medium text-paper">Timeline — {caseId}</h1>
                <p className="text-sm text-ash">Correlated events across all uploaded log sources.</p>
              </div>
              <button
                onClick={handleExport}
                disabled={events.length === 0}
                className="rounded-sm border border-hairline px-4 py-2 text-sm text-paper transition-colors hover:border-amber hover:text-amber disabled:opacity-40"
              >
                Export CSV
              </button>

              <div className="flex items-center gap-2">
                {savedViews.length > 0 && (
                  <select
                    onChange={(e) => {
                      const view = savedViews.find((v) => v.id === e.target.value);
                      if (view) handleLoadView(view);
                    }}
                    value=""
                    className="rounded-sm border border-hairline bg-ink px-3 py-2 text-sm text-paper focus:border-amber outline-none"
                  >
                    <option value="" disabled>Load a saved view…</option>
                    {savedViews.map((v) => (
                      <option key={v.id} value={v.id}>{v.name}</option>
                    ))}
                  </select>
                )}
                <button
                  onClick={() => setShowSaveDialog(true)}
                  className="rounded-sm border border-hairline px-4 py-2 text-sm text-paper transition-colors hover:border-amber hover:text-amber"
                >
                  Save View
                </button>
                <button
                  onClick={handleExport}
                  disabled={events.length === 0}
                  className="rounded-sm border border-hairline px-4 py-2 text-sm text-paper transition-colors hover:border-amber hover:text-amber disabled:opacity-40"
                >
                  Export CSV
                </button>
              </div>
            </div>

            {stats && (
              <div className="mb-6 grid grid-cols-5 gap-3">
                <div className="rounded-sm border border-hairline bg-panel p-3">
                  <p className="text-xs text-ash">Total Events</p>
                  <p className="font-display text-xl font-semibold text-paper">{stats.totalEvents}</p>
                </div>
                <div className="rounded-sm border border-hairline bg-panel p-3">
                  <p className="text-xs text-ash">Unique Sources</p>
                  <p className="font-display text-xl font-semibold text-paper">{stats.uniqueSources}</p>
                </div>
                <div className="rounded-sm border border-hairline bg-panel p-3">
                  <p className="text-xs text-ash">Correlated Events</p>
                  <p className="font-display text-xl font-semibold text-teal">
                    {stats.correlatedEvents} <span className="text-xs text-ash">({stats.correlatedPercent}%)</span>
                  </p>
                </div>
                <div className="rounded-sm border border-hairline bg-panel p-3">
                  <p className="text-xs text-ash">Earliest Event</p>
                  <p className="font-mono text-xs text-paper">{formatTime(stats.earliestEvent)}</p>
                </div>
                <div className="rounded-sm border border-hairline bg-panel p-3">
                  <p className="text-xs text-ash">Latest Event</p>
                  <p className="font-mono text-xs text-paper">{formatTime(stats.latestEvent)}</p>
                </div>
              </div>
            )}

            <div className="mb-6 grid grid-cols-5 gap-3 rounded-sm border border-hairline bg-panel p-4">
              {["actor", "host", "source", "action"].map((field) => (
                <select
                  key={field}
                  value={filters[field]}
                  onChange={(e) => setFilters({ ...filters, [field]: e.target.value })}
                  className="rounded-sm border border-hairline bg-ink px-2 py-1.5 text-xs text-paper focus:border-amber outline-none"
                >
                  <option value="">All {field}</option>
                  {distinct(field).map((v) => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </select>
              ))}
              <div className="flex gap-2">
                <button onClick={handleApplyFilters} className="flex-1 rounded-sm bg-amber py-1.5 text-xs font-medium text-ink hover:bg-amber-hover">
                  Apply
                </button>
                <button onClick={handleClearFilters} className="flex-1 rounded-sm border border-hairline py-1.5 text-xs text-ash hover:border-amber hover:text-amber">
                  Clear
                </button>
              </div>
            </div>


            <div className="mb-4 flex gap-2">
              <button
                onClick={() => setViewMode("table")}
                className={`rounded-sm border px-3 py-1.5 text-xs transition-colors ${
                  viewMode === "table" ? "border-amber bg-amber/10 text-amber" : "border-hairline text-ash hover:border-amber hover:text-amber"
                }`}
              >
                Table View
              </button>
              <button
                onClick={() => setViewMode("swimlane")}
                className={`rounded-sm border px-3 py-1.5 text-xs transition-colors ${
                  viewMode === "swimlane" ? "border-amber bg-amber/10 text-amber" : "border-hairline text-ash hover:border-amber hover:text-amber"
                }`}
              >
                Timeline View
              </button>
            </div>

            {loading && <p className="text-sm text-ash">Loading…</p>}
            {error && <p className="text-sm text-danger">{error}</p>}

            {!loading && viewMode === "table" && events.length > 0 && (
              <div className="overflow-hidden rounded-sm border border-hairline">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-hairline bg-panel text-xs uppercase tracking-wide text-ash">
                      <th className="px-4 py-2.5 font-medium">Timestamp</th>
                      <th className="px-4 py-2.5 font-medium">Source</th>
                      <th className="px-4 py-2.5 font-medium">Host</th>
                      <th className="px-4 py-2.5 font-medium">Actor</th>
                      <th className="px-4 py-2.5 font-medium">Action</th>
                      <th className="px-4 py-2.5 font-medium">Object</th>
                      <th className="px-4 py-2.5 font-medium">Result</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pagedEvents.map((e) => {
                      const newSession = e.session_id !== lastSessionId;
                      lastSessionId = e.session_id;
                      return (
                        <tr key={e.id} className={`border-b border-hairline ${newSession ? "border-t-2 border-t-amber/30" : ""}`}>
                          <td className="px-4 py-2 font-mono text-xs text-ash">{formatTime(e.timestamp)}</td>
                          <td className="px-4 py-2 text-xs text-paper">{e.source}</td>
                          <td className="px-4 py-2 text-xs text-paper">{e.host}</td>
                          <td className="px-4 py-2 text-xs text-paper">{e.actor}</td>
                          <td className="px-4 py-2 text-xs text-paper">{e.action}</td>
                          <td className="px-4 py-2 text-xs text-ash">{e.object}</td>
                          <td className="px-4 py-2 text-xs text-ash">{e.result}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                {totalPages > 1 && (
                  <div className="flex items-center justify-between border-t border-hairline bg-panel px-4 py-2 text-xs text-ash">
                    <span>Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, events.length)} of {events.length}</span>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setPage((p) => Math.max(0, p - 1))}
                        disabled={page === 0}
                        className="rounded-sm border border-hairline px-3 py-1 hover:border-amber hover:text-amber disabled:opacity-40"
                      >
                        Previous
                      </button>
                      <button
                        onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                        disabled={page >= totalPages - 1}
                        className="rounded-sm border border-hairline px-3 py-1 hover:border-amber hover:text-amber disabled:opacity-40"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}


            {!loading && viewMode === "swimlane" && (
              <>
                <TimelineSwimlane events={events} onSelectEvent={setSelectedEvent} />

                {selectedEvent && (
                  <div className="mt-4 rounded-sm border border-hairline bg-panel p-4">
                    <div className="mb-2 flex items-center justify-between">
                      <p className="text-sm font-medium text-paper">Event Details</p>
                      <button onClick={() => setSelectedEvent(null)} className="text-xs text-ash hover:text-amber">✕</button>
                    </div>
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div><span className="text-ash">Timestamp: </span><span className="font-mono text-paper">{formatTime(selectedEvent.timestamp)}</span></div>
                      <div><span className="text-ash">Source: </span><span className="text-paper">{selectedEvent.source}</span></div>
                      <div><span className="text-ash">Host: </span><span className="text-paper">{selectedEvent.host}</span></div>
                      <div><span className="text-ash">Actor: </span><span className="text-paper">{selectedEvent.actor}</span></div>
                      <div><span className="text-ash">Action: </span><span className="text-paper">{selectedEvent.action}</span></div>
                      <div><span className="text-ash">Result: </span><span className="text-paper">{selectedEvent.result}</span></div>
                    </div>
                    <p className="mt-3 rounded-sm bg-ink p-2 font-mono text-[11px] text-ash break-all">{selectedEvent.raw_log}</p>
                  </div>
                )}
              </>
            )}

            {!loading && events.length === 0 && (
              <p className="rounded-sm border border-hairline bg-panel px-4 py-6 text-center text-sm text-ash">
                No events found. Generate the timeline first.
              </p>
            )}

            {showSaveDialog && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4" onClick={() => setShowSaveDialog(false)}>
                <div className="w-full max-w-sm rounded-sm border border-hairline bg-panel p-5" onClick={(e) => e.stopPropagation()}>
                  <p className="mb-3 text-sm font-medium text-paper">Save current view</p>
                  <input
                    type="text"
                    value={viewName}
                    onChange={(e) => setViewName(e.target.value)}
                    placeholder="e.g. Brute force attempts"
                    className="mb-4 w-full rounded-sm border border-hairline bg-ink px-3 py-2 text-sm text-paper placeholder:text-ash/60 focus:border-amber outline-none"
                    autoFocus
                  />
                  <div className="flex gap-2">
                    <button onClick={() => setShowSaveDialog(false)} className="flex-1 rounded-sm border border-hairline py-2 text-sm text-ash hover:border-amber hover:text-amber">
                      Cancel
                    </button>
                    <button onClick={handleSaveView} className="flex-1 rounded-sm bg-amber py-2 text-sm font-medium text-ink hover:bg-amber-hover">
                      Save
                    </button>
                  </div>
                </div>
              </div>
            )}

          </main>
        </div>
        <PluginDrawer />
      </div>
    </PluginDrawerProvider>
  );
}