import { usePluginDrawer } from "./PluginDrawerContext";
import { currentPlugin } from "../data/mockData";

export default function PluginDrawer() {
  const { open, close } = usePluginDrawer();

  if (!open) return null;

  return (
    <>
      {/* backdrop */}
      <div
        className="fixed inset-0 z-30 bg-black/40"
        onClick={close}
        aria-hidden="true"
      />

      {/* drawer */}
      <aside className="fixed right-0 top-0 z-40 flex h-full w-72 flex-col border-l border-hairline bg-panel shadow-xl">
        {/* header */}
        <div className="flex items-center justify-between border-b border-hairline px-5 py-4">
          <p className="font-display text-sm font-medium text-paper">Plugins</p>
          <button
            type="button"
            onClick={close}
            aria-label="Close plugins panel"
            className="text-ash transition-colors hover:text-amber"
          >
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-6">
          {/* Current Plugin */}
          <section>
            <p className="mb-2 text-[11px] uppercase tracking-wide text-ash">Current Plugin</p>
            {currentPlugin ? (
              <div className="rounded-sm border border-hairline bg-ink p-3">
                <p className="text-sm font-medium text-paper">{currentPlugin.name}</p>
                <p className="mt-0.5 font-mono text-[11px] text-ash">
                  Added {currentPlugin.addedOn}
                </p>
              </div>
            ) : (
              <p className="text-sm text-ash italic">No active plugin</p>
            )}
          </section>

          {/* Add New Plugin */}
          <section>
            <p className="mb-2 text-[11px] uppercase tracking-wide text-ash">Add New Plugin</p>
            <button
              type="button"
              className="w-full rounded-sm border border-hairline py-2 text-sm text-ash transition-colors hover:border-amber hover:text-amber"
            >
              + Add New Plugin
            </button>
          </section>
        </div>
      </aside>
    </>
  );
}
