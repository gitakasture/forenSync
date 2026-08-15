import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import NewCaseModal from "../components/NewCaseModal";
import PluginDrawer from "../components/PluginDrawer";
import { PluginDrawerProvider } from "../components/PluginDrawerContext";
import { mockCases, recentActivity } from "../data/mockData";

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
  const navigate = useNavigate();

  return (
    <PluginDrawerProvider>
      <div className="relative flex h-screen bg-ink">
        <Sidebar />

        <div className="flex flex-1 flex-col overflow-hidden">
          <TopBar onNewCase={() => setShowNewCase(true)} />

          <main className="flex-1 overflow-y-auto px-8 py-6">

            {/* Active Cases */}
            <div className="mb-1 flex items-center justify-between">
              <h2 className="font-display text-base font-medium text-paper">Active Cases</h2>
              <div className="flex items-center gap-3">
                <select className="rounded-sm border border-hairline bg-panel px-3 py-1.5 text-xs text-ash focus:border-amber outline-none">
                  <option>All Status</option>
                  <option>Active</option>
                  <option>Pending</option>
                  <option>Closed</option>
                </select>
                <select className="rounded-sm border border-hairline bg-panel px-3 py-1.5 text-xs text-ash focus:border-amber outline-none">
                  <option>Sort: Recent</option>
                  <option>Sort: Oldest</option>
                </select>
                <div className="flex gap-1">
                  <button className="rounded-sm border border-amber bg-amber/10 p-1.5 text-amber">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor"><rect x="1" y="1" width="5" height="12"/><rect x="8" y="1" width="5" height="12"/></svg>
                  </button>
                  <button className="rounded-sm border border-hairline p-1.5 text-ash hover:border-amber hover:text-amber">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor"><rect x="1" y="1" width="5" height="5"/><rect x="8" y="1" width="5" height="5"/><rect x="1" y="8" width="5" height="5"/><rect x="8" y="8" width="5" height="5"/></svg>
                  </button>
                </div>
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
                  {mockCases.map((c, i) => (
                    <tr key={c.caseId} className={`${i !== mockCases.length - 1 ? "border-b border-hairline" : ""} bg-ink hover:bg-panel transition-colors`}>
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
                          {c.investigators.slice(0, 2).map((inv) => (
                            <span key={inv} className="flex h-7 w-7 items-center justify-center rounded-full border border-hairline bg-raised font-mono text-xs text-paper">
                              {inv}
                            </span>
                          ))}
                          {c.extraInvestigators > 0 && (
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
                          <button className="rounded-sm border border-hairline p-1.5 text-ash hover:border-amber hover:text-amber transition-colors" aria-label="View">👁</button>
                          <button className="rounded-sm border border-hairline px-2 py-1 text-xs text-ash hover:border-amber hover:text-amber transition-colors" aria-label="More">···</button>
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

              {/* Quick Actions */}
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

              {/* Recent Activity */}
              <div>
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="font-display text-base font-medium text-paper">Recent Activity</h2>
                </div>
                <div className="space-y-3">
                  {recentActivity.map((a, i) => (
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

        <PluginDrawer />
        {showNewCase && <NewCaseModal onClose={() => setShowNewCase(false)} />}
      </div>
    </PluginDrawerProvider>
  );
}
