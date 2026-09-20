import { NavLink } from "react-router-dom";
import { isOrgHead } from "../utils/auth";

const baseNavItems = [
  { label: "Cases", to: "/cases", icon: "☰" },
];

const investigatorOnlyNavItems = [
  { label: "Parser Plugins", to: "/plugins", icon: "🧩" },
];

const headOnlyNavItems = [];

const sharedNavItems = [
  { label: "Users & Teams", to: "/users", icon: "👥" },
];

const trailingNavItems = [
  { label: "Help & Support", to: "/help", icon: "?" },
];

export default function Sidebar() {
  const head = isOrgHead();

  const dashboardItem = {
    label: "Dashboard",
    to: head ? "/head-dashboard" : "/investigator-dashboard",
    icon: "⊞",
  };

  // Settings item only for heads - investigators access via profile dropdown
  const settingsItem = head ? {
    label: "System Settings",
    to: "/settings",
    icon: "⚙",
  } : null;

  const navItems = [
    dashboardItem,
    ...baseNavItems,
    ...(head ? [] : investigatorOnlyNavItems),
    ...sharedNavItems,
    ...(head ? headOnlyNavItems : []),
    ...(settingsItem ? [settingsItem] : []),
    ...trailingNavItems,
  ];

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
                end={item.to === "/head-dashboard" || item.to === "/investigator-dashboard"}
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
    </aside>
  );
}