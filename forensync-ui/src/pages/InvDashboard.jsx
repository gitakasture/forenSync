// import { useState, useEffect } from "react";
// import { useNavigate } from "react-router-dom";
// import Sidebar from "../components/Sidebar";
// import TopBar from "../components/TopBar";
// import PluginDrawer from "../components/PluginDrawer";
// import { PluginDrawerProvider } from "../components/PluginDrawerContext";
// import CaseDetailModal from "../components/CaseDetailModal";
// import api from "../utils/api";
// import { getUser } from "../utils/auth";
// import { recentActivity } from "../data/mockData";

// const statusStyles = {
//   Active: "text-teal border-teal/40 bg-teal/10",
//   Pending: "text-amber border-amber/40 bg-amber/10",
//   Closed: "text-ash border-hairline bg-raised",
// };

// export default function InvDashboard() {
//   const navigate = useNavigate();
//   const user = getUser();

//   const [cases, setCases] = useState([]);
//   const [loading, setLoading] = useState(true);
//   const [selectedCaseId, setSelectedCaseId] = useState(null);

//   useEffect(() => {
//     if (!user?.orgId || !user?.investigatorId) return;

//     api
//       .get("/cases", { params: { orgId: user.orgId, userId: user.investigatorId } })
//       .then(({ data }) => setCases(data.data.cases || []))
//       .catch(console.error)
//       .finally(() => setLoading(false));
//   }, []);

//   const activeCases = cases.filter((c) => c.status === "Active");

//   return (
//     <PluginDrawerProvider>
//       <div className="relative flex h-screen bg-ink">
//         <Sidebar />

//         <div className="flex flex-1 flex-col overflow-hidden">
//           <TopBar />

//           <main className="flex-1 overflow-y-auto px-8 py-6">

//             {/* Active Cases */}
//             <div className="mb-1 flex items-center justify-between">
//               <h2 className="font-display text-base font-medium text-paper">Active Cases</h2>
//             </div>

//             <div className="overflow-hidden rounded-sm border border-hairline mb-2">
//               <table className="w-full text-left text-sm">
//                 <thead>
//                   <tr className="border-b border-hairline bg-panel text-xs uppercase tracking-wide text-ash">
//                     <th className="px-4 py-3 font-medium">Case ID</th>
//                     <th className="px-4 py-3 font-medium">Case Name</th>
//                     <th className="px-4 py-3 font-medium">Investigators</th>
//                     <th className="px-4 py-3 font-medium">Last Updated</th>
//                     <th className="px-4 py-3 font-medium">Status</th>
//                     <th className="px-4 py-3 font-medium">Actions</th>
//                   </tr>
//                 </thead>
//                 <tbody>
//                   {loading && (
//                     <tr><td colSpan={6} className="px-4 py-6 text-center text-sm text-ash">Loading…</td></tr>
//                   )}
//                   {!loading && activeCases.length === 0 && (
//                     <tr><td colSpan={6} className="px-4 py-6 text-center text-sm text-ash">No active cases.</td></tr>
//                   )}
//                   {activeCases.map((c, i) => (
//                     <tr key={c.caseId} className={`${i !== activeCases.length - 1 ? "border-b border-hairline" : ""} bg-ink hover:bg-panel transition-colors`}>
//                       <td className="px-4 py-3">
//                         <span className="rounded-sm border border-amber/30 bg-amber/5 px-2 py-0.5 font-mono text-xs text-amber whitespace-nowrap">
//                           {c.caseId}
//                         </span>
//                       </td>
//                       <td className="px-4 py-3">
//                         <p className="text-paper text-sm">{c.name}</p>
//                         <p className={`text-xs ${c.priorityColor}`}>● {c.priority}</p>
//                       </td>
//                       <td className="px-4 py-3">
//                         <div className="flex items-center gap-1">
//                           {(c.investigators || []).slice(0, 2).map((inv) => (
//                             <span key={inv} className="flex h-7 w-7 items-center justify-center rounded-full border border-hairline bg-raised font-mono text-xs text-paper">
//                               {inv}
//                             </span>
//                           ))}
//                           {(c.extraInvestigators || 0) > 0 && (
//                             <span className="flex h-7 w-7 items-center justify-center rounded-full border border-hairline bg-raised font-mono text-xs text-ash">
//                               +{c.extraInvestigators}
//                             </span>
//                           )}
//                         </div>
//                       </td>
//                       <td className="px-4 py-3 font-mono text-xs text-ash whitespace-pre-line">{c.lastUpdated}</td>
//                       <td className="px-4 py-3">
//                         <span className={`rounded-sm border px-2 py-0.5 text-xs ${statusStyles[c.status]}`}>
//                           {c.status}
//                         </span>
//                       </td>
//                       <td className="px-4 py-3">
//                         <div className="flex items-center gap-2">
//                           <button
//                             onClick={() => setSelectedCaseId(c.caseId)}
//                             className="rounded-sm border border-hairline p-1.5 text-ash hover:border-amber hover:text-amber transition-colors"
//                             aria-label="View"
//                           >
//                             👁
//                           </button>
//                           <button className="rounded-sm border border-hairline px-2 py-1 text-xs text-ash hover:border-amber hover:text-amber transition-colors" aria-label="More">···</button>
//                         </div>
//                       </td>
//                     </tr>
//                   ))}
//                 </tbody>
//               </table>
//             </div>

//             <button
//               onClick={() => navigate("/cases")}
//               className="mb-6 w-full py-1.5 text-center text-sm text-amber hover:text-amber-hover transition-colors"
//             >
//               View all cases →
//             </button>

//             {/* Recent Activity */}
//             <div className="max-w-md">
//               <div className="mb-3 flex items-center justify-between">
//                 <h2 className="font-display text-base font-medium text-paper">Recent Activity</h2>
//                 <button className="text-xs text-amber hover:text-amber-hover">View all</button>
//               </div>
//               <div className="space-y-3">
//                 {recentActivity.map((a, i) => (
//                   <div key={i} className="flex items-start gap-3">
//                     <div className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs ${a.iconColor}`}>
//                       {a.icon}
//                     </div>
//                     <div className="flex flex-1 items-center justify-between gap-2">
//                       <p className="text-sm text-ash">{a.text}</p>
//                       <span className="shrink-0 font-mono text-xs text-ash/60">{a.time}</span>
//                     </div>
//                   </div>
//                 ))}
//               </div>
//             </div>

//           </main>
//         </div>

//         <PluginDrawer />
//         {selectedCaseId && (
//           <CaseDetailModal caseId={selectedCaseId} onClose={() => setSelectedCaseId(null)} />
//         )}
//       </div>
//     </PluginDrawerProvider>
//   );
// }



import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import PluginDrawer from "../components/PluginDrawer";
import { PluginDrawerProvider } from "../components/PluginDrawerContext";
import CaseDetailModal from "../components/CaseDetailModal";
import UploadCaseFilesModal from "../components/UploadCaseFilesModal";
import api from "../utils/api";
import { getUser } from "../utils/auth";

const statusStyles = {
  Active: "text-teal border-teal/40 bg-teal/10",
  Pending: "text-amber border-amber/40 bg-amber/10",
  Closed: "text-ash border-hairline bg-raised",
};

export default function InvDashboard() {
  const navigate = useNavigate();
  const user = getUser();

  const [cases, setCases] = useState([]);
  const [loadingCases, setLoadingCases] = useState(true);
  const [selectedCaseId, setSelectedCaseId] = useState(null);
  const [uploadCaseId, setUploadCaseId] = useState(null);

  const [pendingNotifications, setPendingNotifications] = useState([]);
  const [loadingPending, setLoadingPending] = useState(true);
  const [confirmingId, setConfirmingId] = useState(null);

  const fetchCases = () => {
    if (!user?.orgId || !user?.investigatorId) return;
    api
      .get("/cases", { params: { orgId: user.orgId, userId: user.investigatorId, role: user.role} })
      .then(({ data }) => setCases(data.data.cases || []))
      .catch(console.error)
      .finally(() => setLoadingCases(false));
  };

  const fetchPending = () => {
    if (!user?.orgId || !user?.investigatorId) return;
    api
      .get("/notifications", { params: { orgId: user.orgId, userId: user.investigatorId } })
      .then(({ data }) => {
        const unread = (data.data.notifications || []).filter((n) => !n.is_read);
        setPendingNotifications(unread);
      })
      .catch(console.error)
      .finally(() => setLoadingPending(false));
  };

  useEffect(() => {
    fetchCases();
    fetchPending();
  }, []);

  const handleConfirm = async (notificationId) => {
    setConfirmingId(notificationId);
    try {
      await api.post(`/notifications/${notificationId}/confirm`, {
        orgId: user.orgId,
        userId: user.investigatorId,
      });
      fetchPending();
      fetchCases();
    } catch (err) {
      console.error(err);
    } finally {
      setConfirmingId(null);
    }
  };

  const activeCases = cases.filter((c) => c.status === "Active");

  return (
    <PluginDrawerProvider>
      <div className="relative flex h-screen bg-ink">
        <Sidebar />

        <div className="flex flex-1 flex-col overflow-hidden">
          <TopBar />

          <main className="flex-1 overflow-y-auto px-8 py-6">

            {/* Pending Assignments */}
            <div className="mb-1 flex items-center justify-between">
              <h2 className="font-display text-base font-medium text-paper">Pending Assignments</h2>
            </div>

            <div className="mb-8 space-y-2">
              {loadingPending && (
                <p className="rounded-sm border border-hairline bg-panel px-4 py-4 text-sm text-ash">Loading…</p>
              )}
              {!loadingPending && pendingNotifications.length === 0 && (
                <p className="rounded-sm border border-hairline bg-panel px-4 py-4 text-sm text-ash">
                  No pending assignments.
                </p>
              )}
              {pendingNotifications.map((n) => (
                <div
                  key={n.id}
                  className="flex items-center justify-between gap-4 rounded-sm border border-amber/30 bg-amber/5 px-4 py-3"
                >
                  <div className="flex items-center gap-3">
                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-amber/20 text-amber">📁</span>
                    <p className="text-sm text-paper">{n.text}</p>
                  </div>
                  <button
                    onClick={() => handleConfirm(n.id)}
                    disabled={confirmingId === n.id}
                    className="shrink-0 rounded-sm bg-amber px-4 py-1.5 text-xs font-medium text-ink transition-colors hover:bg-amber-hover disabled:opacity-60"
                  >
                    {confirmingId === n.id ? "Confirming…" : "Confirm"}
                  </button>
                </div>
              ))}
            </div>

            {/* Active Cases */}
            <div className="mb-1 flex items-center justify-between">
              <h2 className="font-display text-base font-medium text-paper">Active Cases</h2>
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
                          {c.hasFiles ? (
                            <button
                              onClick={() => navigate(`/cases/${c.caseId}/files`)}
                              className="rounded-sm border border-hairline px-2 py-1 text-xs text-ash hover:border-amber hover:text-amber transition-colors"
                            >
                              View Details
                            </button>
                          ) : (
                            <button
                              onClick={() => setUploadCaseId(c.caseId)}
                              className="rounded-sm border border-hairline px-2 py-1 text-xs text-ash hover:border-amber hover:text-amber transition-colors"
                            >
                              Upload Files
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <button
              onClick={() => navigate("/cases")}
              className="w-full py-1.5 text-center text-sm text-amber hover:text-amber-hover transition-colors"
            >
              View all cases →
            </button>

          </main>
        </div>

        <PluginDrawer />
        {selectedCaseId && (
          <CaseDetailModal caseId={selectedCaseId} onClose={() => setSelectedCaseId(null)} />
        )}
        {uploadCaseId && (
          <UploadCaseFilesModal caseId={uploadCaseId} onClose={() => setUploadCaseId(null)} />
        )}
      </div>
    </PluginDrawerProvider>
  );
}