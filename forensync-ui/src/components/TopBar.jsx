import { useNavigate } from "react-router-dom";
import { mockInvestigator } from "../data/mockData";
import { usePluginDrawer } from "./PluginDrawerContext";
import { isOrgHead } from "../utils/auth";

export default function TopBar({ onNewCase }) {
  const navigate = useNavigate();
  const { open, toggle } = usePluginDrawer();
  const head = isOrgHead();

  return (
    <div className="flex items-center justify-between gap-4 border-b border-hairline bg-panel px-6 py-3">
      {/* Welcome */}
      <div className="shrink-0">
        <p className="text-xs text-ash">Welcome back,</p>
        <p className="font-display text-lg font-semibold text-paper leading-tight">{mockInvestigator.name}</p>
        <p className="text-xs text-ash">{head ? "Head of Team" : mockInvestigator.investigatorId}</p>
      </div>

      {/* Search */}
      <div className="flex flex-1 items-center gap-3 max-w-md">
        <div className="relative w-full">
          <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ash text-sm">⌕</span>
          <input
            type="text"
            placeholder="Search Case ID, name, investigator, tags…"
            className="w-full rounded-sm border border-hairline bg-ink py-2 pl-9 pr-3 text-sm text-paper placeholder:text-ash focus:border-amber outline-none"
          />
        </div>
      </div>

      {/* Right actions */}
      <div className="flex shrink-0 items-center gap-3">
        <button
          onClick={onNewCase ?? (() => navigate("/cases/new"))}
          className="flex items-center gap-2 whitespace-nowrap rounded-sm bg-amber px-4 py-2 text-sm font-medium text-ink transition-colors hover:bg-amber-hover"
        >
          + New Case
        </button>

        {/* Bell */}
        <button className="relative flex h-9 w-9 items-center justify-center rounded-full border border-hairline text-ash hover:border-amber hover:text-amber transition-colors">
          🔔
          <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-danger text-[10px] font-bold text-paper">3</span>
        </button>

        {/* Plugin drawer toggle */}
        <button
          type="button"
          onClick={toggle}
          aria-label="Toggle plugins panel"
          className={`flex h-9 w-9 items-center justify-center rounded-full border transition-colors ${
            open ? "border-amber text-amber" : "border-hairline text-ash hover:border-amber hover:text-amber"
          }`}
        >
          ···
        </button>
      </div>
    </div>
  );
}
