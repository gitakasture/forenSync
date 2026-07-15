import { NavLink, useNavigate } from "react-router-dom";
import { mockInvestigator } from "../data/mockData";
import { isOrgHead, logout } from "../utils/auth";

const baseNavItems = [{ label: "Cases", to: "/dashboard", icon: "▤" }];

const headOnlyNavItems = [
  { label: "System Settings", to: "/settings", icon: "⚙" },
];

const trailingNavItems = [{ label: "Help", to: "/help", icon: "?" }];

export default function Sidebar() {
  const navigate = useNavigate();
  const head = isOrgHead();
  const navItems = [...baseNavItems, ...(head ? headOnlyNavItems : []), ...trailingNavItems];

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r border-hairline bg-panel">
      <div className="border-b border-hairline px-5 py-5">
        <p className="font-display text-lg font-semibold text-paper">ForenSync</p>
        <p className="mt-0.5 font-mono text-[11px] tracking-wide text-ash">v1.0.0-beta</p>
      </div>

      <nav className="flex-1 px-3 py-4">
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-sm border-l-2 px-3 py-2 text-sm transition-colors ${
                    isActive
                      ? "border-amber bg-raised text-paper"
                      : "border-transparent text-ash hover:bg-raised hover:text-paper"
                  }`
                }
              >
                <span className="font-mono text-xs text-ash">{item.icon}</span>
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="border-t border-hairline px-4 py-4">
        <div className="mb-3 flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full border border-hairline bg-ink font-mono text-xs text-amber">
            {mockInvestigator.name.split(" ").map((n) => n[0]).join("")}
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm text-paper">{mockInvestigator.name}</p>
            <p className="truncate font-mono text-[11px] text-ash">
              {head ? "Organization Head" : mockInvestigator.investigatorId}
            </p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full rounded-sm border border-hairline py-1.5 text-xs text-ash transition-colors hover:border-danger hover:text-danger"
        >
          Logout
        </button>
      </div>
    </aside>
  );
}
