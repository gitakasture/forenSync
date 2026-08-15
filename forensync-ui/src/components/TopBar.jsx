import { useNavigate } from "react-router-dom";
// import { mockInvestigator } from "../data/mockData";
import { getUser, isOrgHead } from "../utils/auth";
import { usePluginDrawer } from "./PluginDrawerContext";
// import { isOrgHead } from "../utils/auth";
import { useState, useEffect } from "react";
import api from "../utils/api";

export default function TopBar({ onNewCase }) {
  const navigate = useNavigate();
  const { open, toggle } = usePluginDrawer();
  const head = isOrgHead();
  const user = getUser();

  const [notifOpen, setNotifOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);

  const fetchNotifications = () => {
    if (!user?.orgId || !user?.investigatorId) return;
    api
      .get("/notifications", { params: { orgId: user.orgId, userId: user.investigatorId } })
      .then(({ data }) => setNotifications(data.data.notifications))
      .catch(() => {});
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const handleConfirm = async (notificationId) => {
    try {
      await api.post(`/notifications/${notificationId}/confirm`, {
        orgId: user.orgId,
        userId: user.investigatorId,
      });
      fetchNotifications();
    } catch {
      // silently ignore for now
    }
  };

  return (
    <div className="flex items-center justify-between gap-4 border-b border-hairline bg-panel px-6 py-3">
      {/* Welcome */}
      <div className="shrink-0">
        <p className="text-xs text-ash">Welcome back,</p>
        <p className="font-display text-lg font-semibold text-paper leading-tight">{user?.name || "Unknown User"}</p>
        <p className="text-xs text-ash">{head ? "Head of Team" : user?.investigatorId}</p>
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
        {head && (
          <button
            onClick={onNewCase ?? (() => navigate("/cases/new"))}
            className="flex items-center gap-2 whitespace-nowrap rounded-sm bg-amber px-4 py-2 text-sm font-medium text-ink transition-colors hover:bg-amber-hover"
          >
            + New Case
          </button>
        )}

        {/* Bell */}
        <div className="relative">
          <button
            onClick={() => setNotifOpen((o) => !o)}
            className="relative flex h-9 w-9 items-center justify-center rounded-full border border-hairline text-ash hover:border-amber hover:text-amber transition-colors"
          >
            🔔
            {unreadCount > 0 && (
              <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-danger text-[10px] font-bold text-paper">
                {unreadCount}
              </span>
            )}
          </button>

          {notifOpen && (
            <div className="absolute right-0 top-11 z-50 w-80 rounded-sm border border-hairline bg-panel p-3 shadow-2xl">
              <p className="mb-2 text-sm font-medium text-paper">Notifications</p>
              {notifications.length === 0 && <p className="text-xs text-ash">No notifications.</p>}
              <div className="space-y-2">
                {notifications.map((n) => (
                  <div key={n.id} className="rounded-sm border border-hairline bg-ink p-3">
                    <p className="text-sm text-paper">{n.text}</p>
                    {!n.is_read && (
                      <button
                        onClick={() => handleConfirm(n.id)}
                        className="mt-2 rounded-sm bg-amber px-3 py-1 text-xs font-medium text-ink hover:bg-amber-hover"
                      >
                        Confirm
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

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
