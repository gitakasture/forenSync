import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";

export default function NewCaseFile() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    description: "",
    from: "",
    to: "",
  });
  const [files, setFiles] = useState([]);

  const handleDrop = (e) => {
    e.preventDefault();
    setFiles([...files, ...Array.from(e.dataTransfer.files)]);
  };

  const handleFilePick = (e) => {
    setFiles([...files, ...Array.from(e.target.files)]);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Mock upload — replace with real Axios call to case-ingestion endpoint.
    navigate("/dashboard");
  };

  return (
    <div className="flex h-screen bg-ink">
      <Sidebar />

      <div className="flex flex-1 overflow-y-auto">
        <div className="mx-auto flex w-full max-w-3xl gap-8 px-8 py-8">
          {/* Main form */}
          <form onSubmit={handleSubmit} className="flex-1 rounded-sm border border-hairline bg-panel p-7">
            <h1 className="mb-1 font-display text-xl font-medium text-paper">New Case File</h1>
            <p className="mb-6 text-sm text-ash">Create a case and attach the log evidence for analysis.</p>

            <div className="mb-5">
              <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">Case Name</label>
              <input
                type="text"
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="e.g. Unauthorized SSH Access — prod-web-03"
                className="w-full rounded-sm border border-hairline bg-ink px-3 py-2.5 text-sm text-paper placeholder:text-ash/60 focus:border-amber outline-none"
              />
            </div>

            <div className="mb-5">
              <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">Description</label>
              <textarea
                rows={3}
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="Brief summary of the incident…"
                className="w-full resize-none rounded-sm border border-hairline bg-ink px-3 py-2.5 text-sm text-paper placeholder:text-ash/60 focus:border-amber outline-none"
              />
            </div>

            <div className="mb-5">
              <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">Upload Log Files</label>
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                className="flex flex-col items-center justify-center rounded-sm border border-dashed border-hairline bg-ink px-4 py-8 text-center transition-colors hover:border-amber/60"
              >
                <p className="text-sm text-ash">Drag &amp; drop log files here, or</p>
                <label className="mt-2 cursor-pointer text-sm text-amber hover:text-amber-hover hover:underline">
                  browse files
                  <input type="file" multiple className="hidden" onChange={handleFilePick} />
                </label>
              </div>

              {files.length > 0 && (
                <ul className="mt-3 space-y-1.5">
                  {files.map((f, i) => (
                    <li
                      key={i}
                      className="flex items-center justify-between rounded-sm border border-hairline bg-ink px-3 py-1.5 font-mono text-xs text-paper"
                    >
                      {f.name}
                      <button
                        type="button"
                        onClick={() => setFiles(files.filter((_, idx) => idx !== i))}
                        className="text-ash hover:text-danger"
                      >
                        ✕
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="mb-7">
              <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">
                Estimate Incident Timeframe
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="date"
                  value={form.from}
                  onChange={(e) => setForm({ ...form, from: e.target.value })}
                  className="w-full rounded-sm border border-hairline bg-ink px-3 py-2 font-mono text-sm text-paper focus:border-amber outline-none"
                />
                <span className="text-ash">to</span>
                <input
                  type="date"
                  value={form.to}
                  onChange={(e) => setForm({ ...form, to: e.target.value })}
                  className="w-full rounded-sm border border-hairline bg-ink px-3 py-2 font-mono text-sm text-paper focus:border-amber outline-none"
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full rounded-sm bg-amber py-2.5 text-sm font-medium text-ink transition-colors hover:bg-amber-hover"
            >
              Upload
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
