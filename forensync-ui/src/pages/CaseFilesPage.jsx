import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import PluginDrawer from "../components/PluginDrawer";
import { PluginDrawerProvider } from "../components/PluginDrawerContext";
import api from "../utils/api";
import { getUser } from "../utils/auth";

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function CaseFilesPage() {
  const { caseId } = useParams();
  const navigate = useNavigate();
  const user = getUser();

  const [detail, setDetail] = useState(null);
  const [logFiles, setLogFiles] = useState([]);
  const [newLogFiles, setNewLogFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [addedPlugins, setAddedPlugins] = useState([]);
  const [matchResults, setMatchResults] = useState(null);
  const [matching, setMatching] = useState(false);

  const [parsing, setParsing] = useState(false);
  const [parseResult, setParseResult] = useState(null);

  const fetchData = () => {
    if (!caseId || !user?.orgId) return;
    setError("");
    Promise.all([
      api.get(`/cases/${caseId}`, { params: { orgId: user.orgId } }),
      api.get(`/cases/${caseId}/files`, { params: { orgId: user.orgId, category: "log" } }),
      api.get("/plugins", { params: { orgId: user.orgId } }),
      api.get(`/cases/${caseId}/parse-status`, { params: { orgId: user.orgId } }),
    ])
      .then(([caseRes, filesRes, pluginsRes, statusRes]) => {
        setDetail(caseRes.data.data.case);
        setLogFiles(filesRes.data.data.files);
        setAddedPlugins(pluginsRes.data.data.plugins.filter((p) => p.added));

        const statusRows = statusRes.data.data.status;
        const alreadyParsed = statusRows.some((r) => r.matchedPlugin);

        if (alreadyParsed) {
          setMatchResults(
            statusRows.map((r) => ({
              fileId: r.fileId,
              fileName: r.fileName,
              matchedPlugin: r.matchedPlugin,
              confidence: null,
              alternatives: [],
            }))
          );
          const totalEvents = statusRows.reduce((sum, r) => sum + r.eventCount, 0);
          setParseResult({ filesParsed: statusRows.filter((r) => r.matchedPlugin).length, totalEvents });
        }
      })
      .catch(() => setError("Could not load case files."))
      .finally(() => setLoading(false));
  };

  useEffect(fetchData, [caseId]);

  const handleAddMore = (e) => {
    setNewLogFiles((prev) => [...prev, ...Array.from(e.target.files)]);
  };

  const handleSave = async () => {
    if (newLogFiles.length === 0) {
      navigate(-1);
      return;
    }
    setSaving(true);
    setError("");

    const formData = new FormData();
    formData.append("orgId", user.orgId);
    formData.append("userId", user.investigatorId);
    newLogFiles.forEach((f) => formData.append("log_files", f));

    try {
      await api.post(`/cases/${caseId}/files`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      navigate(-1);
    } catch (err) {
      setError(err.response?.data?.message || "Failed to save files.");
      setSaving(false);
    }
  };

  const handleCancel = () => {
    navigate(-1);
  };

  const handleMatchParsers = async () => {
    setMatching(true);
    setError("");
    try {
      const { data } = await api.post(`/cases/${caseId}/match-parsers`, { orgId: user.orgId });
      setMatchResults(data.data.results);
    } catch (err) {
      setError(err.response?.data?.message || "Failed to match parsers.");
    } finally {
      setMatching(false);
    }
  };

  const handleChangeMatch = (fileId, newPluginName) => {
    setMatchResults((prev) =>
      prev.map((r) => (r.fileId === fileId ? { ...r, matchedPlugin: newPluginName } : r))
    );
  };

  const allFilesMatched =
    matchResults &&
    logFiles.length > 0 &&
    logFiles.every((f) => matchResults.find((r) => r.fileId === f.id && r.matchedPlugin));

  const handleParseFiles = async () => {
    setParsing(true);
    setError("");
    try {
      const matches = matchResults.map((r) => ({ fileId: r.fileId, pluginName: r.matchedPlugin }));
      const { data } = await api.post(`/cases/${caseId}/parse-files`, { orgId: user.orgId, matches });
      setParseResult(data.data);
    } catch (err) {
      setError(err.response?.data?.message || "Failed to parse files.");
    } finally {
      setParsing(false);
    }
  };

  return (
    <PluginDrawerProvider>
      <div className="relative flex h-screen bg-ink">
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <TopBar />
          <main className="flex-1 overflow-y-auto px-8 py-6">
            <button onClick={() => navigate(-1)} className="mb-4 text-xs text-ash hover:text-amber transition-colors">
              ← Back to My Cases
            </button>

            {loading && <p className="text-sm text-ash">Loading…</p>}

            {detail && (
              <>
                <div className="mb-6 rounded-sm border border-hairline bg-panel p-5">
                  <p className="mb-1 font-mono text-xs text-amber">{detail.caseId}</p>
                  <h1 className="mb-3 font-display text-xl font-medium text-paper">{detail.name}</h1>
                  <p className="mb-1 text-xs uppercase tracking-wide text-ash">Description</p>
                  <p className="text-sm text-paper">{detail.description || "No description provided."}</p>
                </div>

                <div className="mb-6">
                  <h2 className="mb-3 font-display text-base font-medium text-paper">Uploaded Log Files</h2>
                  {logFiles.length === 0 ? (
                    <p className="rounded-sm border border-hairline bg-panel px-4 py-4 text-sm text-ash">
                      No log files uploaded yet.
                    </p>
                  ) : (
                    <div className="overflow-hidden rounded-sm border border-hairline">
                      <table className="w-full text-left text-sm">
                        <thead>
                          <tr className="border-b border-hairline bg-panel text-xs uppercase tracking-wide text-ash">
                            <th className="px-4 py-2.5 font-medium">File Name</th>
                            <th className="px-4 py-2.5 font-medium">Size</th>
                          </tr>
                        </thead>
                        <tbody>
                          {logFiles.map((f, i) => (
                            <tr key={f.id} className={i !== logFiles.length - 1 ? "border-b border-hairline" : ""}>
                              <td className="px-4 py-2.5 text-paper">{f.fileName}</td>
                              <td className="px-4 py-2.5 font-mono text-xs text-ash">{formatSize(f.fileSize)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>

                <div className="mb-6">
                  <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">Upload More Log Files</label>
                  <div className="flex flex-col items-center justify-center rounded-sm border border-dashed border-hairline bg-ink px-4 py-6 text-center transition-colors hover:border-amber/60">
                    <p className="text-sm text-ash">Drag &amp; drop log files here, or</p>
                    <label className="mt-2 cursor-pointer text-sm text-amber hover:text-amber-hover hover:underline">
                      browse files
                      <input type="file" multiple className="hidden" onChange={handleAddMore} />
                    </label>
                  </div>
                  {newLogFiles.length > 0 && (
                    <ul className="mt-3 space-y-1.5">
                      {newLogFiles.map((f, i) => (
                        <li key={i} className="flex items-center justify-between rounded-sm border border-hairline bg-ink px-3 py-1.5 font-mono text-xs text-paper">
                          {f.name}
                          <button
                            type="button"
                            onClick={() => setNewLogFiles(newLogFiles.filter((_, idx) => idx !== i))}
                            className="text-ash hover:text-danger"
                          >
                            ✕
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                <button
                  type="button"
                  onClick={handleMatchParsers}
                  disabled={matching}
                  className="mb-4 w-full rounded-sm border border-hairline py-2.5 text-sm text-paper transition-colors hover:border-amber hover:text-amber disabled:opacity-60"
                >
                  {matching ? "Matching…" : "🧩 Match Parsers"}
                </button>

                {error && <p className="mb-4 text-xs text-danger">{error}</p>}

                {matchResults && (
                  <div className="mb-7 space-y-2">
                    <p className="text-xs uppercase tracking-wide text-ash">Matched Parsers</p>
                    {matchResults.map((r) => (
                      <div key={r.fileId} className="flex items-center justify-between gap-3 rounded-sm border border-hairline bg-ink px-4 py-3">
                        <div className="min-w-0">
                          <p className="truncate text-sm text-paper">{r.fileName}</p>
                          {r.matchedPlugin && (
                            <p className="text-xs text-teal">{r.confidence}% confidence</p>
                          )}
                        </div>
                        <select
                          value={r.matchedPlugin || ""}
                          onChange={(e) => handleChangeMatch(r.fileId, e.target.value)}
                          className="shrink-0 rounded-sm border border-hairline bg-panel px-2 py-1.5 text-xs text-paper focus:border-amber outline-none"
                        >
                          <option value="" disabled>No match — select manually</option>
                          {addedPlugins.map((p) => (
                            <option key={p.name} value={p.name}>{p.label}</option>
                          ))}
                        </select>
                      </div>
                    ))}
                  </div>
                )}


                {matchResults && (
                  <button
                    type="button"
                    onClick={handleParseFiles}
                    disabled={!allFilesMatched || parsing}
                    className="mb-7 w-full rounded-sm bg-amber py-2.5 text-sm font-medium text-ink transition-colors hover:bg-amber-hover disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    {parsing ? "Parsing…" : "Parse Log Files"}
                  </button>
                )}

                {parseResult && (
                  <p className="mb-7 rounded-sm border border-teal/40 bg-teal/10 px-4 py-3 text-sm text-teal">
                    ✓ Parsed {parseResult.filesParsed} file(s) — {parseResult.totalEvents} events extracted.
                  </p>
                )}


                <div className="flex gap-3 max-w-md">
                  <button
                    onClick={handleCancel}
                    className="flex-1 rounded-sm border border-hairline py-2.5 text-sm text-ash transition-colors hover:border-amber hover:text-amber"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex-1 rounded-sm bg-amber py-2.5 text-sm font-medium text-ink transition-colors hover:bg-amber-hover disabled:opacity-60"
                  >
                    {saving ? "Saving…" : "Save"}
                  </button>
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