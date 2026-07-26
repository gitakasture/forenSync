import { useState } from "react";
import { useNavigate } from "react-router-dom";

// Mock parser matching data
const mockParsers = [
  { file: "auth.log", detectedType: "Linux Auth Log", parser: "Linux_Auth_Parser", confidence: 96 },
  { file: "syslog.log", detectedType: "System Log", parser: "Syslog_Parser", confidence: 94 },
  { file: "firewall.log", detectedType: "Firewall Log", parser: "Firewall_Parser", confidence: 97 },
  { file: "apache_access.log", detectedType: "Web Access Log", parser: "Apache_Access_Parser", confidence: 95 },
  { file: "dns_queries.csv", detectedType: "DNS Log", parser: "DNS_CSV_Parser", confidence: 93 },
];

const mockUploaded = [
  { name: "auth.log", size: "2.4 MB", type: ".log" },
  { name: "syslog.log", size: "1.8 MB", type: ".log" },
  { name: "firewall.log", size: "3.2 MB", type: ".log" },
  { name: "apache_access.log", size: "4.7 MB", type: ".log" },
  { name: "dns_queries.csv", size: "1.1 MB", type: ".csv" },
];

// Step 1: New Case Form
function StepForm({ onClose, onUpload }) {
  const [form, setForm] = useState({ name: "", description: "", from: "", to: "" });
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
    onUpload(files);
  };

  return (
    <>
      <h1 className="mb-1 font-display text-xl font-medium text-paper">New Case File</h1>
      <p className="mb-6 text-sm text-ash">Create a case and attach the log evidence for analysis.</p>

      <form onSubmit={handleSubmit}>
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
                <li key={i} className="flex items-center justify-between rounded-sm border border-hairline bg-ink px-3 py-1.5 font-mono text-xs text-paper">
                  {f.name}
                  <button type="button" onClick={() => setFiles(files.filter((_, idx) => idx !== i))} className="text-ash hover:text-danger">✕</button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="mb-7">
          <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">Estimate Incident Timeframe</label>
          <div className="flex items-center gap-3">
            <input type="date" value={form.from} onChange={(e) => setForm({ ...form, from: e.target.value })}
              className="w-full rounded-sm border border-hairline bg-ink px-3 py-2 font-mono text-sm text-paper focus:border-amber outline-none" />
            <span className="text-ash">to</span>
            <input type="date" value={form.to} onChange={(e) => setForm({ ...form, to: e.target.value })}
              className="w-full rounded-sm border border-hairline bg-ink px-3 py-2 font-mono text-sm text-paper focus:border-amber outline-none" />
          </div>
        </div>

        <button type="submit" className="w-full rounded-sm bg-amber py-2.5 text-sm font-medium text-ink transition-colors hover:bg-amber-hover">
          Upload
        </button>
        <button type="button" onClick={onClose} className="mt-2 w-full rounded-sm bg-danger/80 py-2.5 text-sm font-medium text-paper transition-colors hover:bg-danger">
          Cancel
        </button>
      </form>
    </>
  );
}

// Step 2: Files Uploaded
function StepUploaded({ files, onUploadMore, onFindParsers }) {
  const displayed = mockUploaded.slice(0, 8);
  return (
    <>
      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-teal/20 text-teal text-xl">✓</div>
        <div>
          <p className="font-display text-lg font-medium text-paper">Files Uploaded</p>
          <p className="text-sm text-ash">{mockUploaded.length} log files uploaded successfully.</p>
        </div>
      </div>

      <div className="overflow-hidden rounded-sm border border-hairline mb-5">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-hairline bg-panel text-xs uppercase tracking-wide text-ash">
              <th className="px-4 py-2.5 text-left font-medium">File Name</th>
              <th className="px-4 py-2.5 text-left font-medium">Size</th>
              <th className="px-4 py-2.5 text-left font-medium">Type</th>
              <th className="px-4 py-2.5 text-left font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {displayed.map((f, i) => (
              <tr key={i} className={i !== displayed.length - 1 ? "border-b border-hairline" : ""}>
                <td className="px-4 py-2.5 flex items-center gap-2 text-paper">
                  <span className="text-ash text-xs">☐</span>{f.name}
                </td>
                <td className="px-4 py-2.5 text-ash font-mono text-xs">{f.size}</td>
                <td className="px-4 py-2.5 text-ash font-mono text-xs">{f.type}</td>
                <td className="px-4 py-2.5">
                  <span className="rounded-sm border border-teal/40 bg-teal/10 px-2 py-0.5 text-xs text-teal">Uploaded</span>
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t border-hairline">
              <td className="px-4 py-2.5 text-sm text-ash">Total {mockUploaded.length} files</td>
              <td className="px-4 py-2.5 font-mono text-xs text-ash">28.3 MB</td>
              <td colSpan={2} />
            </tr>
          </tfoot>
        </table>
      </div>

      <div className="flex gap-3">
        <button onClick={onUploadMore} className="flex-1 rounded-sm border border-hairline py-2.5 text-sm text-ash transition-colors hover:border-amber hover:text-amber">
          Upload More Files
        </button>
        <button onClick={onFindParsers} className="flex-1 rounded-sm bg-amber py-2.5 text-sm font-medium text-ink transition-colors hover:bg-amber-hover">
          Find Matching Parsers
        </button>
      </div>
    </>
  );
}

// Step 3: Matching Parsers Found
function StepParsers({ onBack, onConfirm }) {
  return (
    <>
      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-purple-500/20 text-2xl">🧩</div>
        <div>
          <p className="font-display text-lg font-medium text-paper">Matching Parsers Found</p>
          <p className="text-sm text-ash">We found the best matching parser for each file. Please review and confirm.</p>
        </div>
      </div>

      <div className="overflow-hidden rounded-sm border border-hairline mb-4">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-hairline bg-panel text-xs uppercase tracking-wide text-ash">
              <th className="px-4 py-2.5 text-left font-medium">File Name</th>
              <th className="px-4 py-2.5 text-left font-medium">Detected Type</th>
              <th className="px-4 py-2.5 text-left font-medium">Matched Parser</th>
              <th className="px-4 py-2.5 text-left font-medium">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {mockParsers.map((p, i) => (
              <tr key={i} className={i !== mockParsers.length - 1 ? "border-b border-hairline" : ""}>
                <td className="px-4 py-2.5 flex items-center gap-2 text-paper"><span className="text-ash text-xs">☐</span>{p.file}</td>
                <td className="px-4 py-2.5 text-ash text-xs">{p.detectedType}</td>
                <td className="px-4 py-2.5 font-mono text-xs text-paper">{p.parser}</td>
                <td className="px-4 py-2.5 font-mono text-xs text-teal">{p.confidence}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mb-5 flex items-center gap-2 rounded-sm border border-hairline bg-raised px-4 py-3 text-xs text-ash">
        <span>ℹ</span>
        <span>Parsers are selected based on file structure, patterns and content analysis.</span>
      </div>

      <div className="flex gap-3">
        <button onClick={onBack} className="flex-1 rounded-sm border border-hairline py-2.5 text-sm text-ash transition-colors hover:border-amber hover:text-amber">
          Back
        </button>
        <button onClick={onBack} className="flex-1 rounded-sm border border-hairline py-2.5 text-sm text-ash transition-colors hover:border-amber hover:text-amber">
          Re-scan Parsers
        </button>
        <button onClick={onConfirm} className="flex-1 rounded-sm bg-amber py-2.5 text-sm font-medium text-ink transition-colors hover:bg-amber-hover">
          Confirm &amp; Convert
        </button>
      </div>
    </>
  );
}

// Step 4: Converting Logs (animated progress)
function StepConverting({ onDone }) {
  const [progress, setProgress] = useState(75);

  const convertingFiles = [
    { name: "auth.log", parser: "Linux_Auth_Parser", status: "Completed", pct: 100 },
    { name: "syslog.log", parser: "Syslog_Parser", status: "Completed", pct: 100 },
    { name: "firewall.log", parser: "Firewall_Parser", status: "Completed", pct: 100 },
    { name: "apache_access.log", parser: "Apache_Access_Parser", status: "In Progress", pct: 75 },
    { name: "dns_queries.csv", parser: "DNS_CSV_Parser", status: "Pending", pct: 0 },
  ];

  const statusStyle = (s) => ({
    Completed: "text-teal",
    "In Progress": "text-amber",
    Pending: "text-ash",
  }[s]);

  const barColor = (s) => ({
    Completed: "bg-teal",
    "In Progress": "bg-amber",
    Pending: "bg-hairline",
  }[s]);

  return (
    <>
      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-amber/20 text-amber text-xl">↻</div>
        <div>
          <p className="font-display text-lg font-medium text-paper">Converting Logs</p>
          <p className="text-sm text-ash">Please wait while we convert logs to the standard format.</p>
        </div>
      </div>

      <div className="mb-5 flex items-center gap-4">
        <p className="shrink-0 text-sm text-paper">Overall Progress</p>
        <div className="flex-1 h-2 rounded-full bg-raised overflow-hidden">
          <div className="h-full bg-amber rounded-full transition-all" style={{ width: `${progress}%` }} />
        </div>
        <p className="shrink-0 font-mono text-sm text-paper">{progress}%</p>
      </div>

      <div className="overflow-hidden rounded-sm border border-hairline mb-4">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-hairline bg-panel text-xs uppercase tracking-wide text-ash">
              <th className="px-4 py-2.5 text-left font-medium">File Name</th>
              <th className="px-4 py-2.5 text-left font-medium">Parser</th>
              <th className="px-4 py-2.5 text-left font-medium">Status</th>
              <th className="px-4 py-2.5 text-left font-medium">Progress</th>
            </tr>
          </thead>
          <tbody>
            {convertingFiles.map((f, i) => (
              <tr key={i} className={i !== convertingFiles.length - 1 ? "border-b border-hairline" : ""}>
                <td className="px-4 py-2.5 flex items-center gap-2 text-paper">
                  {f.status === "Completed" ? <span className="text-teal">✓</span> : <span className="text-ash">◌</span>}
                  {f.name}
                </td>
                <td className="px-4 py-2.5 font-mono text-xs text-ash">{f.parser}</td>
                <td className={`px-4 py-2.5 text-xs ${statusStyle(f.status)}`}>{f.status}</td>
                <td className="px-4 py-2.5">
                  <div className="flex items-center gap-2">
                    <div className="w-20 h-1.5 rounded-full bg-raised overflow-hidden">
                      <div className={`h-full rounded-full ${barColor(f.status)}`} style={{ width: `${f.pct}%` }} />
                    </div>
                    <span className="font-mono text-xs text-ash">{f.pct}%</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mb-5 flex items-center gap-2 rounded-sm border border-hairline bg-raised px-4 py-3 text-xs text-ash">
        <span>ℹ</span>
        <span>Please do not close this page. This may take a few minutes depending on file sizes.</span>
      </div>

      <button onClick={onDone} className="w-full rounded-sm bg-amber py-2.5 text-sm font-medium text-ink transition-colors hover:bg-amber-hover">
        Complete (Demo)
      </button>
    </>
  );
}

// Step 5: Conversion Completed
function StepDone({ onClose, onSave }) {
  const summaryFiles = [
    { name: "auth.log", originalType: "Linux Auth Log", parser: "Linux_Auth_Parser", output: "Standard JSON" },
    { name: "syslog.log", originalType: "System Log", parser: "Syslog_Parser", output: "Standard JSON" },
    { name: "firewall.log", originalType: "Firewall Log", parser: "Firewall_Parser", output: "Standard JSON" },
    { name: "apache_access.log", originalType: "Web Access Log", parser: "Apache_Access_Parser", output: "Standard JSON" },
    { name: "dns_queries.csv", originalType: "DNS Log", parser: "DNS_CSV_Parser", output: "Standard JSON" },
  ];

  return (
    <>
      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-teal/20 text-teal text-xl">✓</div>
        <div>
          <p className="font-display text-lg font-medium text-paper">Conversion Completed</p>
          <p className="text-sm text-ash">All logs have been successfully converted to standard format.</p>
        </div>
      </div>

      <div className="mb-5 grid grid-cols-4 gap-3">
        {[
          { label: "Files Processed", value: "12", color: "text-paper" },
          { label: "Successfully Converted", value: "12", color: "text-teal" },
          { label: "Failed", value: "0", color: "text-danger" },
          { label: "Total Size", value: "28.3 MB", color: "text-paper" },
        ].map((s) => (
          <div key={s.label} className="rounded-sm border border-hairline bg-raised p-3 text-center">
            <p className={`font-display text-xl font-semibold ${s.color}`}>{s.value}</p>
            <p className="mt-0.5 text-[11px] text-ash">{s.label}</p>
          </div>
        ))}
      </div>

      <p className="mb-2 text-sm font-medium text-paper">Converted Files Summary</p>
      <div className="overflow-hidden rounded-sm border border-hairline mb-4">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-hairline bg-panel text-xs uppercase tracking-wide text-ash">
              <th className="px-4 py-2.5 text-left font-medium">File Name</th>
              <th className="px-4 py-2.5 text-left font-medium">Original Type</th>
              <th className="px-4 py-2.5 text-left font-medium">Parser Used</th>
              <th className="px-4 py-2.5 text-left font-medium">Output Format</th>
              <th className="px-4 py-2.5 text-left font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {summaryFiles.map((f, i) => (
              <tr key={i} className={i !== summaryFiles.length - 1 ? "border-b border-hairline" : ""}>
                <td className="px-4 py-2.5 text-paper">{f.name}</td>
                <td className="px-4 py-2.5 text-xs text-ash">{f.originalType}</td>
                <td className="px-4 py-2.5 font-mono text-xs text-ash">{f.parser}</td>
                <td className="px-4 py-2.5 text-xs text-ash">{f.output}</td>
                <td className="px-4 py-2.5">
                  <span className="rounded-sm border border-teal/40 bg-teal/10 px-2 py-0.5 text-xs text-teal">Converted</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="border-t border-hairline px-4 py-2.5 text-xs text-ash">+ 7 more files</div>
      </div>

      <div className="flex gap-3">
        <button onClick={onClose} className="flex-1 rounded-sm border border-hairline py-2.5 text-sm text-ash transition-colors hover:border-amber hover:text-amber">
          Cancel
        </button>
        <button onClick={onSave} className="flex-1 rounded-sm border border-hairline py-2.5 text-sm text-ash transition-colors hover:border-amber hover:text-amber">
          Save Case File
        </button>
        <button onClick={onClose} className="flex-1 rounded-sm bg-amber py-2.5 text-sm font-medium text-ink transition-colors hover:bg-amber-hover">
          Start Investigation
        </button>
      </div>
    </>
  );
}

// Main modal orchestrator
export default function NewCaseModal({ onClose }) {
  const [step, setStep] = useState("form"); // form | uploaded | parsers | converting | done

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-sm border border-hairline bg-panel p-7 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {step === "form" && (
          <StepForm onClose={onClose} onUpload={() => setStep("uploaded")} />
        )}
        {step === "uploaded" && (
          <StepUploaded files={[]} onUploadMore={() => setStep("form")} onFindParsers={() => setStep("parsers")} />
        )}
        {step === "parsers" && (
          <StepParsers onBack={() => setStep("uploaded")} onConfirm={() => setStep("converting")} />
        )}
        {step === "converting" && (
          <StepConverting onDone={() => setStep("done")} />
        )}
        {step === "done" && (
          <StepDone onClose={onClose} onSave={onClose} />
        )}
      </div>
    </div>
  );
}
