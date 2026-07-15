export default function CaseTag({ id }) {
  return (
    <span className="perforated-left inline-flex items-center gap-2 rounded-sm border border-hairline bg-panel pl-3 pr-2.5 py-1 font-mono text-xs text-amber case-tag">
      {id}
    </span>
  );
}
