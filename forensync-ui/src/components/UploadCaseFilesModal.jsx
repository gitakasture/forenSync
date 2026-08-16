import { useEffect, useState } from "react";
import api from "../utils/api";
import { getUser } from "../utils/auth";
import { useNavigate } from "react-router-dom";

export default function UploadCaseFilesModal({ caseId, onClose }) {
  const [detail, setDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(true);
  const [logFiles, setLogFiles] = useState([]);
  const [otherFiles, setOtherFiles] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const user = getUser();
  const navigate = useNavigate();

  useEffect(() => {
    if (!caseId || !user?.orgId) return;
    api
      .get(`/cases/${caseId}`, { params: { orgId: user.orgId } })
      .then(({ data }) => setDetail(data.data.case))
      .catch(() => setError("Could not load case details."))
      .finally(() => setLoadingDetail(false));
  }, [caseId]);

  const handleContinue = async () => {
    if (logFiles.length === 0) {
      setError("At least one log file is required.");
      return;
    }
    setError("");
    setSubmitting(true);

    const formData = new FormData();
    formData.append("orgId", user.orgId);
    formData.append("userId", user.investigatorId);
    logFiles.forEach((f) => formData.append("log_files", f));
    otherFiles.forEach((f) => formData.append("other_files", f));

    try {
      await api.post(`/cases/${caseId}/files`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      onClose();
      navigate(`/cases/${caseId}/files`);
    } catch (err) {
      setError(err.response?.data?.message || "Failed to upload files.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4" onClick={onClose}>
      <div
        className="relative w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-sm border border-hairline bg-panel p-7 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h1 className="mb-1 font-display text-xl font-medium text-paper">Upload Case Files</h1>
        <p className="mb-6 text-sm text-ash">Attach evidence files to this case.</p>

        {loadingDetail && <p className="text-sm text-ash">Loading case details…</p>}

        {detail && (
          <div className="mb-6 rounded-sm border border-hairline bg-ink p-4">
            <p className="mb-1 font-mono text-xs text-amber">{detail.caseId}</p>
            <p className="mb-3 text-sm font-medium text-paper">{detail.name}</p>
            <p className="mb-1 text-xs uppercase tracking-wide text-ash">Description</p>
            <p className="mb-3 text-sm text-paper">{detail.description || "No description provided."}</p>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="mb-1 text-xs uppercase tracking-wide text-ash">Created By</p>
                <p className="text-sm text-paper">{detail.createdBy.name}</p>
              </div>
              <div>
                <p className="mb-1 text-xs uppercase tracking-wide text-ash">Created On</p>
                <p className="font-mono text-sm text-paper">{detail.createdOn}</p>
              </div>
            </div>
          </div>
        )}

        <div className="mb-5">
          <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">
            Log Files <span className="text-danger">*</span>
          </label>
          <div className="flex flex-col items-center justify-center rounded-sm border border-dashed border-hairline bg-ink px-4 py-6 text-center transition-colors hover:border-amber/60">
            <p className="text-sm text-ash">Drag &amp; drop log files here, or</p>
            <label className="mt-2 cursor-pointer text-sm text-amber hover:text-amber-hover hover:underline">
              browse files
              <input type="file" multiple className="hidden" onChange={(e) => setLogFiles(Array.from(e.target.files))} />
            </label>
          </div>
          {logFiles.length > 0 && (
            <ul className="mt-3 space-y-1.5">
              {logFiles.map((f, i) => (
                <li key={i} className="flex items-center justify-between rounded-sm border border-hairline bg-ink px-3 py-1.5 font-mono text-xs text-paper">
                  {f.name}
                  <button type="button" onClick={() => setLogFiles(logFiles.filter((_, idx) => idx !== i))} className="text-ash hover:text-danger">✕</button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="mb-7">
          <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">
            Other Case Files <span className="text-ash normal-case">(optional)</span>
          </label>
          <div className="flex flex-col items-center justify-center rounded-sm border border-dashed border-hairline bg-ink px-4 py-6 text-center transition-colors hover:border-amber/60">
            <p className="text-sm text-ash">Drag &amp; drop files here, or</p>
            <label className="mt-2 cursor-pointer text-sm text-amber hover:text-amber-hover hover:underline">
              browse files
              <input type="file" multiple className="hidden" onChange={(e) => setOtherFiles(Array.from(e.target.files))} />
            </label>
          </div>
          {otherFiles.length > 0 && (
            <ul className="mt-3 space-y-1.5">
              {otherFiles.map((f, i) => (
                <li key={i} className="flex items-center justify-between rounded-sm border border-hairline bg-ink px-3 py-1.5 font-mono text-xs text-paper">
                  {f.name}
                  <button type="button" onClick={() => setOtherFiles(otherFiles.filter((_, idx) => idx !== i))} className="text-ash hover:text-danger">✕</button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {error && <p className="mb-4 text-xs text-danger">{error}</p>}

        <div className="flex gap-3">
          <button type="button" onClick={onClose} className="flex-1 rounded-sm border border-hairline py-2.5 text-sm text-ash transition-colors hover:border-amber hover:text-amber">
            Cancel
          </button>
          <button type="button" onClick={handleContinue} disabled={submitting} className="flex-1 rounded-sm bg-amber py-2.5 text-sm font-medium text-ink transition-colors hover:bg-amber-hover disabled:opacity-60">
            {submitting ? "Uploading…" : "Continue"}
          </button>
        </div>
      </div>
    </div>
  );
}