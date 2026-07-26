import { NavLink, useNavigate } from "react-router-dom";
import { mockInvestigator } from "../data/mockData";
import { isOrgHead, logout } from "../utils/auth";

const baseNavItems = [
  { label: "Dashboard", to: "/dashboard", icon: "⊞" },
  { label: "Cases", to: "/cases", icon: "☰" },
  { label: "Parser Plugins", to: "/plugins", icon: "🧩" },
  { label: "Users & Teams", to: "/users", icon: "👥" },
];

const headOnlyNavItems = [
  { label: "System Settings", to: "/settings", icon: "⚙" },
];

const trailingNavItems = [
  { label: "Help & Support", to: "/help", icon: "?" },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const head = isOrgHead();
  const navItems = [...baseNavItems, ...(head ? headOnlyNavItems : []), ...trailingNavItems];

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <aside className="flex h-full w-56 shrink-0 flex-col border-r border-hairline bg-panel">
      <div className="border-b border-hairline px-5 py-5">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-sm bg-amber/20 text-amber text-sm">🔍</div>
          <div>
            <p className="font-display text-base font-semibold text-paper">ForenSync</p>
            <p className="font-mono text-[10px] tracking-wide text-ash">v1.0.0-beta</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4">
        <ul className="space-y-0.5">
          {navItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.to === "/dashboard"}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-sm px-3 py-2 text-sm transition-colors ${
                    isActive
                      ? "bg-amber/10 text-amber border-l-2 border-amber"
                      : "border-l-2 border-transparent text-ash hover:bg-raised hover:text-paper"
                  }`
                }
              >
                <span className="text-base leading-none">{item.icon}</span>
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="border-t border-hairline px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-amber bg-amber/10 font-mono text-xs font-medium text-amber">
            {mockInvestigator.name.split(" ").map((n) => n[0]).join("")}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm text-paper">{mockInvestigator.name}</p>
            <p className="truncate font-mono text-[11px] text-ash">
              {head ? "Head of Team" : mockInvestigator.investigatorId}
            </p>
          </div>
          <button
            onClick={handleLogout}
            className="shrink-0 text-xs text-ash hover:text-danger"
            aria-label="Logout"
            title="Logout"
          >
            ⏏
          </button>
        </div>
      </div>
    </aside>
  );
}
