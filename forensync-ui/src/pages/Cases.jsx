import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
// import PluginDrawer from "../components/PluginDrawer";
// import { PluginDrawerProvider } from "../components/PluginDrawerContext";
import NewCaseModal from "../components/NewCaseModal";
import CaseActionsMenu from "../components/CaseActionsMenu";
import InvestigatorDetailModal from "../components/InvestigatorDetailModal";
import api from "../utils/api";
import { getUser } from "../utils/auth";
import CaseDetailModal from "../components/CaseDetailModal";
import UploadCaseFilesModal from "../components/UploadCaseFilesModal";
import { isOrgHead } from "../utils/auth";
import LoadingOverlay from "../components/LoadingOverlay";

const statusStyles = {
  Active: "text-teal border-teal/40 bg-teal/10",
  Pending: "text-amber border-amber/40 bg-amber/10",
  Closed: "text-ash border-hairline bg-raised",
};

export default function Cases() {

  const navigate = useNavigate();
  const [showNewCase, setShowNewCase] = useState(false);
  const [filter, setFilter] = useState("All");

  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const user = getUser();

  const [selectedCaseId, setSelectedCaseId] = useState(null);
  const [selectedInvestigator, setSelectedInvestigator] = useState(null);

  const [searchTerm, setSearchTerm] = useState("");

  const head = isOrgHead();
  const [uploadCaseId, setUploadCaseId] = useState(null);

  const fetchCases = () => {
    if (!user?.orgId || !user?.investigatorId) return;

    api
      .get("/cases", {
        params: {
          orgId: user.orgId,
          userId: user.investigatorId,
          role: user.role,
        },
      })
      .then(({ data }) => {
        setCases(data.data.cases || []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const filtered = cases
    .filter((c) => filter === "All" || c.status === filter)
    .filter((c) =>
      searchTerm.trim() === "" ||
      c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.caseId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.status.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
  
      <div className="relative flex h-screen bg-ink">

        {loading && <LoadingOverlay label="Loading cases…" />}

        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <TopBar onNewCase={() => setShowNewCase(true)} />
          <main className="flex-1 overflow-y-auto px-8 py-6">

            <div className="mb-5 flex items-center justify-between">
              <h1 className="font-display text-lg font-medium text-paper">All Cases</h1>
              <div className="flex items-center gap-3">
                <div className="relative w-64">
                  <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ash text-sm">⌕</span>
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search case ID, name, status…"
                    className="w-full rounded-sm border border-hairline bg-ink py-1.5 pl-9 pr-3 text-xs text-paper placeholder:text-ash focus:border-amber outline-none"
                  />
                </div>
                <div className="flex gap-2">
                  {["All", "Active", "Pending", "Closed"].map((s) => (
                    <button
                      key={s}
                      onClick={() => setFilter(s)}
                      className={`rounded-sm border px-3 py-1.5 text-xs transition-colors ${
                        filter === s
                          ? "border-amber bg-amber/10 text-amber"
                          : "border-hairline text-ash hover:border-amber hover:text-amber"
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="overflow-hidden rounded-sm border border-hairline">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-hairline bg-panel text-xs uppercase tracking-wide text-ash">
                    <th className="px-5 py-3 font-medium">Case ID</th>
                    <th className="px-5 py-3 font-medium">Case Name</th>
                    <th className="px-5 py-3 font-medium">Investigators</th>
                    <th className="px-5 py-3 font-medium">Last Updated</th>
                    <th className="px-5 py-3 font-medium">Status</th>
                    <th className="px-5 py-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((c, i) => (
                    <tr key={c.caseId} className={`${i !== filtered.length - 1 ? "border-b border-hairline" : ""} bg-ink hover:bg-panel transition-colors`}>
                      <td className="px-5 py-3.5">
                        <span className="rounded-sm border border-amber/30 bg-amber/5 px-2 py-0.5 font-mono text-xs text-amber whitespace-nowrap">
                          {c.caseId}
                        </span>
                      </td>
                      <td className="px-5 py-3.5">
                        <p className="text-paper">{c.name}</p>
                        <p className={`text-xs ${c.priorityColor}`}>● {c.priority}</p>
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-1">
                          {(c.investigators || []).slice(0, 2).map((inv) => (
                            <button
                              key={inv}
                              onClick={() => setSelectedInvestigator({ id: inv, name: inv })}
                              className="flex h-7 w-7 items-center justify-center rounded-full border border-hairline bg-raised font-mono text-xs text-paper hover:border-amber hover:bg-amber/10 transition-colors cursor-pointer"
                              title="Click to view investigator details"
                            >
                              {inv}
                            </button>
                          ))}
                          {(c.extraInvestigators || 0) > 0 && (
                            <span className="flex h-7 w-7 items-center justify-center rounded-full border border-hairline bg-raised font-mono text-xs text-ash">
                              +{c.extraInvestigators}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-5 py-3.5 font-mono text-xs text-ash whitespace-pre-line">{c.lastUpdated}</td>
                      <td className="px-5 py-3.5">
                        <span className={`rounded-sm border px-2 py-0.5 text-xs ${statusStyles[c.status]}`}>
                          {c.status}
                        </span>
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-2">
                          <button onClick={() => setSelectedCaseId(c.caseId)} className="rounded-sm border border-hairline p-1.5 text-ash hover:border-amber hover:text-amber transition-colors">👁</button>
                          {head ? (
                            <CaseActionsMenu caseData={c} onUpdated={fetchCases} />
                          ) : c.hasFiles ? (
                            <button
                              onClick={() => navigate(`/cases/${c.caseId}/files`)}
                              className="rounded-sm border border-hairline px-2 py-1 text-xs text-ash hover:border-amber hover:text-amber transition-colors"
                            >
                              VIEW CASE
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
          </main>
        </div>
        {showNewCase && <NewCaseModal onClose={() => setShowNewCase(false)} />}
        {selectedCaseId && (
          <CaseDetailModal caseId={selectedCaseId} onClose={() => setSelectedCaseId(null)} />
        )}
        {uploadCaseId && (
          <UploadCaseFilesModal caseId={uploadCaseId} onClose={() => setUploadCaseId(null)} />
        )}
        {selectedInvestigator && (
          <InvestigatorDetailModal 
            investigator={selectedInvestigator} 
            onClose={() => setSelectedInvestigator(null)} 
          />
        )}
      </div>
    
  );
}
