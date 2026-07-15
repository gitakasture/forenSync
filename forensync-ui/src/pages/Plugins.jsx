import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import PluginDrawer from "../components/PluginDrawer";
import { PluginDrawerProvider } from "../components/PluginDrawerContext";
import { currentPlugin, supportedFormats } from "../data/mockData";

export default function Plugins() {
  return (
    <PluginDrawerProvider>
      <div className="relative flex h-screen bg-ink">
        <Sidebar />

        <div className="flex flex-1 flex-col overflow-hidden">
          <TopBar />

          <main className="flex-1 overflow-y-auto px-8 py-6">
            <h1 className="mb-1 font-display text-lg font-medium text-paper">Plugins</h1>
            <p className="mt-1 text-sm text-ash">
              Manage the log-parsing plugins used to ingest evidence for your cases.
            </p>

            {/* Current plugin card */}
            <div className="mt-6 rounded-sm border border-hairline bg-panel p-5 max-w-md">
              <p className="mb-2 text-[11px] uppercase tracking-wide text-ash">Current Plugin</p>
              {currentPlugin ? (
                <>
                  <p className="text-sm font-medium text-paper">{currentPlugin.name}</p>
                  <p className="mt-0.5 font-mono text-[11px] text-ash">Added {currentPlugin.addedOn}</p>
                </>
              ) : (
                <p className="text-sm text-ash italic">No active plugin installed.</p>
              )}
            </div>

            {/* Available plugins */}
            <div className="mt-6 max-w-md">
              <p className="mb-3 text-[11px] uppercase tracking-wide text-ash">Available Plugins</p>
              <ul className="space-y-2">
                {supportedFormats.map((fmt) => (
                  <li
                    key={fmt.id}
                    className="flex items-center justify-between rounded-sm border border-hairline bg-panel px-4 py-3"
                  >
                    <span className="text-sm text-paper">{fmt.label}</span>
                    <button
                      type="button"
                      className="text-xs text-ash transition-colors hover:text-amber"
                    >
                      Add
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </main>
        </div>

        <PluginDrawer />
      </div>
    </PluginDrawerProvider>
  );
}
