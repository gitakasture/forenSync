import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../utils/api";
import { getUser } from "../utils/auth";
import EditCaseModal from "./EditCaseModal";
import ManageCaseInvestigatorsModal from "./ManageInvestigatorsModal";

export default function CaseActionsMenu({ caseData, onUpdated }) {
  const navigate = useNavigate();
  const user = getUser();
  const [open, setOpen] = useState(false);
  const [activeModal, setActiveModal] = useState(null); // "edit" | "investigators"
  const [statusBusy, setStatusBusy] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleChangeStatus = async () => {
    const newStatus = caseData.status === "Closed" ? "Active" : "Closed";
    const confirmed = window.confirm(`${newStatus === "Closed" ? "Close" : "Reopen"} case ${caseData.caseId}?`);
    if (!confirmed) return;
    setStatusBusy(true);
    try {
      await api.patch(`/cases/${caseData.caseId}/status`, { orgId: user.orgId, status: newStatus });
      onUpdated();
    } catch {
      // could surface an error toast here later
    } finally {
      setStatusBusy(false);
      setOpen(false);
    }
  };

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="rounded-sm border border-hairline px-2 py-1 text-xs text-ash hover:border-amber hover:text-amber transition-colors"
        aria-label="More actions"
      >
        ···
      </button>

      {open && (
        <div className="absolute right-0 top-8 z-20 w-48 overflow-hidden rounded-sm border border-hairline bg-panel shadow-2xl">
          <button
            onClick={() => { setActiveModal("edit"); setOpen(false); }}
            className="block w-full px-3 py-2 text-left text-sm text-paper hover:bg-raised transition-colors"
          >
            Edit Case Details
          </button>
          <button
            onClick={() => { setActiveModal("investigators"); setOpen(false); }}
            className="block w-full px-3 py-2 text-left text-sm text-paper hover:bg-raised transition-colors"
          >
            Manage Investigators
          </button>
          <button
            onClick={handleChangeStatus}
            disabled={statusBusy}
            className="block w-full px-3 py-2 text-left text-sm text-paper hover:bg-raised transition-colors disabled:opacity-60"
          >
            {caseData.status === "Closed" ? "Reopen Case" : "Close Case"}
          </button>
          <button
            onClick={() => { navigate(`/cases/${caseData.caseId}/timeline`); setOpen(false); }}
            className="block w-full px-3 py-2 text-left text-sm text-paper hover:bg-raised transition-colors"
          >
            View Timeline
          </button>
        </div>
      )}

      {activeModal === "edit" && (
        <EditCaseModal caseData={caseData} onClose={() => setActiveModal(null)} onUpdated={onUpdated} />
      )}
      {activeModal === "investigators" && (
        <ManageCaseInvestigatorsModal caseId={caseData.caseId} onClose={() => setActiveModal(null)} onUpdated={onUpdated} />
      )}
    </div>
  );
}