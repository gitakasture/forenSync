import { useNavigate } from "react-router-dom";
import { mockInvestigator } from "../data/mockData";
import { usePluginDrawer } from "./PluginDrawerContext";

export default function TopBar() {
  const navigate = useNavigate();
  const { open, toggle } = usePluginDrawer();

  return (
    <div className="flex items-center justify-between gap-4 border-b border-hairline bg-panel px-8 py-5">
      <div className="shrink-0">
        <p className="text-sm text-ash">Welcome back,</p>
        <p className="font-display text-xl font-medium text-paper">{mockInvestigator.name}</p>
      </div>

      <div className="flex flex-1 items-center gap-3">
        <div className="relative w-full max-w-md">
          <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ash">⌕</span>
          <input
            type="text"
            placeholder="Search case ID, host, actor…"
            className="w-full rounded-sm border border-hairline bg-ink py-2 pl-9 pr-3 text-sm text-paper placeholder:text-ash focus:border-amber outline-none"
          />
        </div>
      </div>

      <button
        onClick={() => navigate("/cases/new")}
        className="flex shrink-0 items-center gap-2 whitespace-nowrap rounded-sm bg-amber px-4 py-2 text-sm font-medium text-ink transition-colors hover:bg-amber-hover"
      >
        <span className="text-base leading-none">+</span> New Case File
      </button>

      <button
        type="button"
        onClick={toggle}
        aria-label="Toggle plugins panel"
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full border transition-colors ${
          open
            ? "border-amber text-amber"
            : "border-hairline text-ash hover:border-amber hover:text-amber"
        }`}
      >
        ☰
      </button>
    </div>
  );
}
