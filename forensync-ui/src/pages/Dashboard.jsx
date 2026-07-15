import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import CaseTable from "../components/CaseTable";
import PluginDrawer from "../components/PluginDrawer";
import { PluginDrawerProvider } from "../components/PluginDrawerContext";
import { mockCases } from "../data/mockData";

export default function Dashboard() {
  return (
    <PluginDrawerProvider>
      <div className="relative flex h-screen bg-ink">
        <Sidebar />

        <div className="flex flex-1 flex-col overflow-hidden">
          <TopBar />

          <main className="flex-1 overflow-y-auto px-8 py-6">
            <div className="mb-4 flex items-center justify-between">
              <h1 className="font-display text-lg font-medium text-paper">Active Cases</h1>
              <p className="font-mono text-xs text-ash">{mockCases.length} cases</p>
            </div>

            <CaseTable cases={mockCases} />
          </main>
        </div>

        <PluginDrawer />
      </div>
    </PluginDrawerProvider>
  );
}
