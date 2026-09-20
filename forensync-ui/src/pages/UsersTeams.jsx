import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import api from "../utils/api";
import { getUser } from "../utils/auth";
import LoadingOverlay from "../components/LoadingOverlay";

// =======
// import PluginDrawer from "../components/PluginDrawer";
// import { PluginDrawerProvider } from "../components/PluginDrawerContext";
// import InvestigatorDetailModal from "../components/InvestigatorDetailModal";

// const mockUsers = [
//   { initials: "AR", name: "Aditi Rao", id: "INV-2291", role: "Head of Team", cases: 4, status: "Active" },
//   { initials: "VK", name: "Vikram Kumar", id: "INV-2287", role: "Investigator", cases: 3, status: "Active" },
//   { initials: "RS", name: "Rahul Sharma", id: "INV-2285", role: "Investigator", cases: 2, status: "Active" },
//   { initials: "AP", name: "Ananya Patel", id: "INV-2280", role: "Investigator", cases: 1, status: "Active" },
//   { initials: "NK", name: "Nikhil Kapoor", id: "INV-2278", role: "Investigator", cases: 2, status: "Inactive" },
//   { initials: "SM", name: "Sneha Mishra", id: "INV-2275", role: "Investigator", cases: 3, status: "Active" },
// ];
// >>>>>>> e6df4523764d0f9d3635c2f6b4733f789d7fa3e3

export default function UsersTeams() {
  const user = getUser();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const [openMenuId, setOpenMenuId] = useState(null);
  const [error, setError] = useState("");

  const fetchUsers = () => {
    if (!user?.orgId) return;
    api
      .get("/users", { params: { orgId: user.orgId } })
      .then(({ data }) => setUsers(data.data.users))
      .catch(() => setError("Could not load users."))
      .finally(() => setLoading(false));
  };

  useEffect(fetchUsers, []);

  const filtered = users.filter(
// =======
//   const [selectedInvestigator, setSelectedInvestigator] = useState(null);
  
//   const filtered = mockUsers.filter(
// >>>>>>> e6df4523764d0f9d3635c2f6b4733f789d7fa3e3
    (u) =>
      u.name.toLowerCase().includes(search.toLowerCase()) ||
      u.id.toLowerCase().includes(search.toLowerCase())
  );

  const handleToggleStatus = async (targetUser) => {
    const newStatus = targetUser.status === "Active" ? "Inactive" : "Active";
    try {
      await api.patch(`/users/${targetUser.id}/status`, { orgId: user.orgId, status: newStatus });
      setOpenMenuId(null);
      fetchUsers();
    } catch {
      setError("Failed to update status.");
    }
  };

  return (
    <div className="relative flex h-screen bg-ink">
      {loading && <LoadingOverlay label="Loading users…" />}
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto px-8 py-6">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h1 className="font-display text-lg font-medium text-paper">Users &amp; Teams</h1>
              <p className="mt-0.5 text-sm text-ash">{users.length} members in your organization</p>
            </div>
          </div>

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

          {error && <p className="mb-4 text-sm text-danger">{error}</p>}
          {loading && <p className="text-sm text-ash">Loading…</p>}

          {!loading && (
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
                        <button
                          onClick={() => setSelectedInvestigator(u)}
                          className="flex items-center gap-3 hover:text-amber transition-colors cursor-pointer text-left w-full"
                        >
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-amber bg-amber/10 font-mono text-xs font-medium text-amber">
                            {u.initials}
                          </div>
                          <span className="text-paper hover:text-amber transition-colors">{u.name}</span>
                        </button>
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
                      <td className="px-5 py-3.5 relative">
                        {u.role !== "Head of Team" && (
                          <>
                            <button
                              onClick={() => setOpenMenuId(openMenuId === u.id ? null : u.id)}
                              className="text-xs text-ash hover:text-amber transition-colors"
                            >
                              ···
                            </button>
                            {openMenuId === u.id && (
                              <div className="absolute right-5 top-8 z-20 w-40 overflow-hidden rounded-sm border border-hairline bg-panel shadow-2xl">
                                <button
                                  onClick={() => handleToggleStatus(u)}
                                  className="block w-full px-3 py-2 text-left text-sm text-paper hover:bg-raised transition-colors"
                                >
                                  {u.status === "Active" ? "Deactivate" : "Reactivate"}
                                </button>
                              </div>
                            )}
                          </>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

          )}
        </main>
{/* =======
          </main>
        </div>
        <PluginDrawer />
        {selectedInvestigator && (
          <InvestigatorDetailModal
            investigator={selectedInvestigator}
            onClose={() => setSelectedInvestigator(null)}
          />
        )}
>>>>>>> e6df4523764d0f9d3635c2f6b4733f789d7fa3e3 */}
      </div>
    </div>
  );
}