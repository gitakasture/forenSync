import { useState } from "react";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import PluginDrawer from "../components/PluginDrawer";
import { PluginDrawerProvider } from "../components/PluginDrawerContext";

const mockUsers = [
  { initials: "AR", name: "Aditi Rao", id: "INV-2291", role: "Head of Team", cases: 4, status: "Active" },
  { initials: "VK", name: "Vikram Kumar", id: "INV-2287", role: "Investigator", cases: 3, status: "Active" },
  { initials: "RS", name: "Rahul Sharma", id: "INV-2285", role: "Investigator", cases: 2, status: "Active" },
  { initials: "AP", name: "Ananya Patel", id: "INV-2280", role: "Investigator", cases: 1, status: "Active" },
  { initials: "NK", name: "Nikhil Kapoor", id: "INV-2278", role: "Investigator", cases: 2, status: "Inactive" },
  { initials: "SM", name: "Sneha Mishra", id: "INV-2275", role: "Investigator", cases: 3, status: "Active" },
];

export default function UsersTeams() {
  const [search, setSearch] = useState("");
  const filtered = mockUsers.filter(
    (u) =>
      u.name.toLowerCase().includes(search.toLowerCase()) ||
      u.id.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <PluginDrawerProvider>
      <div className="relative flex h-screen bg-ink">
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <TopBar />
          <main className="flex-1 overflow-y-auto px-8 py-6">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <h1 className="font-display text-lg font-medium text-paper">Users &amp; Teams</h1>
                <p className="mt-0.5 text-sm text-ash">{mockUsers.length} members in your organization</p>
              </div>
              <button className="flex items-center gap-2 rounded-sm bg-amber px-4 py-2 text-sm font-medium text-ink hover:bg-amber-hover transition-colors">
                + Invite Member
              </button>
            </div>

            {/* search */}
            <div className="relative mb-5 max-w-sm">
              <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ash text-sm">⌕</span>
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by name or ID…"
                className="w-full rounded-sm border border-hairline bg-panel pl-9 pr-3 py-2 text-sm text-paper placeholder:text-ash focus:border-amber outline-none"
              />
            </div>

            <div className="overflow-hidden rounded-sm border border-hairline">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-hairline bg-panel text-xs uppercase tracking-wide text-ash">
                    <th className="px-5 py-3 font-medium">Member</th>
                    <th className="px-5 py-3 font-medium">ID</th>
                    <th className="px-5 py-3 font-medium">Role</th>
                    <th className="px-5 py-3 font-medium">Active Cases</th>
                    <th className="px-5 py-3 font-medium">Status</th>
                    <th className="px-5 py-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((u, i) => (
                    <tr key={u.id} className={`${i !== filtered.length - 1 ? "border-b border-hairline" : ""} bg-ink hover:bg-panel transition-colors`}>
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-3">
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-amber bg-amber/10 font-mono text-xs font-medium text-amber">
                            {u.initials}
                          </div>
                          <span className="text-paper">{u.name}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5 font-mono text-xs text-ash">{u.id}</td>
                      <td className="px-5 py-3.5 text-ash">{u.role}</td>
                      <td className="px-5 py-3.5 text-paper">{u.cases}</td>
                      <td className="px-5 py-3.5">
                        <span className={`rounded-sm border px-2 py-0.5 text-xs ${
                          u.status === "Active"
                            ? "border-teal/40 bg-teal/10 text-teal"
                            : "border-hairline bg-raised text-ash"
                        }`}>
                          {u.status}
                        </span>
                      </td>
                      <td className="px-5 py-3.5">
                        <button className="text-xs text-ash hover:text-amber transition-colors">···</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </main>
        </div>
        <PluginDrawer />
      </div>
    </PluginDrawerProvider>
  );
}
