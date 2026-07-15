import CaseTag from "./CaseTag";

const statusStyles = {
  Active: "text-teal border-teal/40 bg-teal/10",
  "Under Review": "text-amber border-amber/40 bg-amber/10",
  Closed: "text-ash border-hairline bg-raised",
};

export default function CaseTable({ cases }) {
  return (
    <div className="overflow-hidden rounded-sm border border-hairline">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-hairline bg-panel text-xs uppercase tracking-wide text-ash">
            <th className="px-5 py-3 font-medium">Case ID</th>
            <th className="px-5 py-3 font-medium">Name</th>
            <th className="px-5 py-3 font-medium">Timeframe</th>
            <th className="px-5 py-3 font-medium">Last Modified</th>
            <th className="px-5 py-3 font-medium">Status</th>
            <th className="px-5 py-3 font-medium text-right">Action</th>
          </tr>
        </thead>
        <tbody>
          {cases.map((c, i) => (
            <tr
              key={c.caseId}
              className={`${i !== cases.length - 1 ? "border-b border-hairline" : ""} bg-ink hover:bg-panel transition-colors`}
            >
              <td className="px-5 py-3.5">
                <CaseTag id={c.caseId} />
              </td>
              <td className="px-5 py-3.5 text-paper">{c.name}</td>
              <td className="px-5 py-3.5 font-mono text-xs text-ash">{c.timeframe}</td>
              <td className="px-5 py-3.5 font-mono text-xs text-ash">{c.lastModified}</td>
              <td className="px-5 py-3.5">
                <span className={`rounded-sm border px-2 py-0.5 text-xs ${statusStyles[c.status]}`}>
                  {c.status}
                </span>
              </td>
              <td className="px-5 py-3.5 text-right">
                <button className="text-xs text-amber hover:text-amber-hover hover:underline">
                  {c.action} →
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
