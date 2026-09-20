import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import NewCaseModal from "../components/NewCaseModal";
import CaseDetailModal from "../components/CaseDetailModal";
// import PluginDrawer from "../components/PluginDrawer";
// import { PluginDrawerProvider } from "../components/PluginDrawerContext";
import api from "../utils/api";
import { getUser } from "../utils/auth";
import CaseActionsMenu from "../components/CaseActionsMenu";
import LoadingOverlay from "../components/LoadingOverlay";

const statusStyles = {
  Active: "text-teal border-teal/40 bg-teal/10",
  Pending: "text-amber border-amber/40 bg-amber/10",
  Closed: "text-ash border-hairline bg-raised",
};

const quickActions = [
  { icon: "📋", label: "Create New\nCase" },
  { icon: "👥", label: "Manage\nUsers" },
];

export default function Dashboard() {
  const [showNewCase, setShowNewCase] = useState(false);
  const [selectedCaseId, setSelectedCaseId] = useState(null);
  const navigate = useNavigate();
  const user = getUser();

  const [cases, setCases] = useState([]);
  const [loadingCases, setLoadingCases] = useState(true);
  const [activity, setActivity] = useState([]);
  const [loadingActivity, setLoadingActivity] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  const fetchCases = () => {
    if (!user?.orgId || !user?.investigatorId) return;
    api
      .get("/cases", { params: { orgId: user.orgId, userId: user.investigatorId, role: "head" } })
      .then(({ data }) => setCases(data.data.cases || []))
      .catch(console.error)
      .finally(() => setLoadingCases(false));
  };

  const fetchActivity = () => {
    if (!user?.orgId) return;
    api
      .get("/activity", { params: { orgId: user.orgId, limit: 10 } })
      .then(({ data }) => setActivity(data.data.activity || []))
      .catch(console.error)
      .finally(() => setLoadingActivity(false));
  };

 
  useEffect(() => {
    fetchCases();
    fetchActivity();
  }, []);

  const activeCases = cases
    .filter((c) => c.status === "Active")
    .filter((c) =>
      searchTerm.trim() === "" ||
      c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.caseId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.status.toLowerCase().includes(searchTerm.toLowerCase())
    );

  return (
    
      <div className="relative flex h-screen bg-ink">
        {(loadingCases || loadingActivity) && <LoadingOverlay label="Loading dashboard…" />}
        <Sidebar />

        <div className="flex flex-1 flex-col overflow-hidden">
          <TopBar onNewCase={() => setShowNewCase(true)} />

          <main className="flex-1 overflow-y-auto px-8 py-6">

            {/* Active Cases */}
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-display text-base font-medium text-paper">Active Cases</h2>
              <div className="relative w-64">
                <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ash text-sm">⌕</span>
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search case ID or name…"
                  className="w-full rounded-sm border border-hairline bg-ink py-1.5 pl-9 pr-3 text-xs text-paper placeholder:text-ash focus:border-amber outline-none"
                />
              </div>
            </div>

            <div className="overflow-hidden rounded-sm border border-hairline mb-2">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-hairline bg-panel text-xs uppercase tracking-wide text-ash">
                    <th className="px-4 py-3 font-medium">Case ID</th>
                    <th className="px-4 py-3 font-medium">Case Name</th>
                    <th className="px-4 py-3 font-medium">Investigators</th>
                    <th className="px-4 py-3 font-medium">Last Updated</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {loadingCases && (
                    <tr><td colSpan={6} className="px-4 py-6 text-center text-sm text-ash">Loading…</td></tr>
                  )}
                  {!loadingCases && activeCases.length === 0 && (
                    <tr><td colSpan={6} className="px-4 py-6 text-center text-sm text-ash">No active cases.</td></tr>
                  )}
                  {activeCases.map((c, i) => (
                    <tr key={c.caseId} className={`${i !== activeCases.length - 1 ? "border-b border-hairline" : ""} bg-ink hover:bg-panel transition-colors`}>
                      <td className="px-4 py-3">
                        <span className="rounded-sm border border-amber/30 bg-amber/5 px-2 py-0.5 font-mono text-xs text-amber whitespace-nowrap">
                          {c.caseId}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <p className="text-paper text-sm">{c.name}</p>
                        <p className={`text-xs ${c.priorityColor}`}>● {c.priority}</p>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          {(c.investigators || []).slice(0, 2).map((inv) => (
                            <span key={inv} className="flex h-7 w-7 items-center justify-center rounded-full border border-hairline bg-raised font-mono text-xs text-paper">
                              {inv}
                            </span>
                          ))}
                          {(c.extraInvestigators || 0) > 0 && (
                            <span className="flex h-7 w-7 items-center justify-center rounded-full border border-hairline bg-raised font-mono text-xs text-ash">
                              +{c.extraInvestigators}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-ash whitespace-pre-line">{c.lastUpdated}</td>
                      <td className="px-4 py-3">
                        <span className={`rounded-sm border px-2 py-0.5 text-xs ${statusStyles[c.status]}`}>
                          {c.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setSelectedCaseId(c.caseId)}
                            className="rounded-sm border border-hairline p-1.5 text-ash hover:border-amber hover:text-amber transition-colors"
                            aria-label="View"
                          >
                            👁
                          </button>
                          <CaseActionsMenu caseData={c} onUpdated={fetchCases} />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <button
              onClick={() => navigate("/cases")}
              className="mb-6 w-full py-1.5 text-center text-sm text-amber hover:text-amber-hover transition-colors"
            >
              View all cases →
            </button>

            {/* Bottom row */}
            <div className="grid grid-cols-2 gap-6">

              {/* Quick Actions — unchanged */}
              <div>
                <h2 className="mb-3 font-display text-base font-medium text-paper">Quick Actions</h2>
                <div className="grid grid-cols-2 gap-3">
                  {quickActions.map((qa, i) => (
                    <button
                      key={i}
                      onClick={i === 0 ? () => setShowNewCase(true) : undefined}
                      className="flex flex-col items-center gap-2 rounded-sm border border-hairline bg-panel px-3 py-4 text-center transition-colors hover:border-amber/50 hover:bg-raised"
                    >
                      <span className="text-2xl">{qa.icon}</span>
                      <span className="text-xs text-ash whitespace-pre-line leading-tight">{qa.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Recent Activity — real data now */}
              <div>
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="font-display text-base font-medium text-paper">Recent Activity</h2>
                </div>
                <div className="space-y-3">
                  {loadingActivity && <p className="text-sm text-ash">Loading…</p>}
                  {!loadingActivity && activity.length === 0 && (
                    <p className="text-sm text-ash">No recent activity.</p>
                  )}
                  {activity.map((a, i) => (
                    <div key={i} className="flex items-start gap-3">
                      <div className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs ${a.iconColor}`}>
                        {a.icon}
                      </div>
                      <div className="flex flex-1 items-center justify-between gap-2">
                        <p className="text-sm text-ash">{a.text}</p>
                        <span className="shrink-0 font-mono text-xs text-ash/60">{a.time}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          </main>
        </div>

        
        {showNewCase && <NewCaseModal onClose={() => setShowNewCase(false)} />}
        {selectedCaseId && (
          <CaseDetailModal caseId={selectedCaseId} onClose={() => setSelectedCaseId(null)} />
        )}
      </div>

  );
}