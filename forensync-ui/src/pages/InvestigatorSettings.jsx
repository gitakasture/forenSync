import { useState } from "react";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import PluginDrawer from "../components/PluginDrawer";
import { PluginDrawerProvider } from "../components/PluginDrawerContext";
import { getUser } from "../utils/auth";
import { useTheme } from "../utils/theme.jsx";

export default function InvestigatorSettings() {
  const user = getUser();
  const { theme, toggleTheme } = useTheme();
  
  // Profile change request state
  const [showChangeRequest, setShowChangeRequest] = useState(false);
  const [changeRequest, setChangeRequest] = useState({
    field: "",
    currentValue: "",
    requestedValue: "",
    reason: "",
  });
  const [requestSubmitted, setRequestSubmitted] = useState(false);

  // Notification preferences state (frontend-only for now)
  const [notificationPreferences, setNotificationPreferences] = useState({
    caseAssignments: true,
    fileUploadReminders: true,
    timelineGeneration: true,
  });

  const handleSubmitRequest = () => {
    // In a real implementation, this would call a backend API
    // For now, we'll just store it in local state and show confirmation
    console.log("Profile change request submitted:", changeRequest);
    setRequestSubmitted(true);
    
    // Reset form after 3 seconds
    setTimeout(() => {
      setShowChangeRequest(false);
      setRequestSubmitted(false);
      setChangeRequest({
        field: "",
        currentValue: "",
        requestedValue: "",
        reason: "",
      });
    }, 3000);
  };

  const toggleNotification = (key) => {
    setNotificationPreferences(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
    // TODO: When backend is ready, persist to API
    // api.post("/notification-preferences", { ...notificationPreferences, [key]: !notificationPreferences[key] });
  };

  const isFormValid = 
    changeRequest.field && 
    changeRequest.requestedValue && 
    changeRequest.reason;

  return (
    <PluginDrawerProvider>
      <div className="relative flex h-screen bg-ink">
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <TopBar />
          <main className="flex-1 overflow-y-auto px-8 py-6">
            <div className="mx-auto max-w-3xl space-y-6">
              <div>
                <h1 className="font-display text-xl font-medium text-paper">Settings</h1>
                <p className="mt-1 text-sm text-ash">Manage your preferences and profile</p>
              </div>

              {/* Appearance Settings */}
              <section className="rounded-sm border border-hairline bg-panel p-6">
                <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-ash">
                  Appearance
                </h2>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-paper">Theme</p>
                    <p className="text-xs text-ash">
                      Switch between light and dark mode
                    </p>
                  </div>
                  <button
                    onClick={toggleTheme}
                    className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors ${
                      theme === "dark" ? "bg-amber" : "bg-ash"
                    }`}
                  >
                    <span
                      className={`inline-block h-6 w-6 transform rounded-full bg-paper transition-transform ${
                        theme === "dark" ? "translate-x-7" : "translate-x-1"
                      }`}
                    />
                  </button>
                </div>
              </section>

              {/* Profile Information */}
              <section className="rounded-sm border border-hairline bg-panel p-6">
                <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-ash">
                  Profile Information
                </h2>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">
                        Name
                      </label>
                      <input
                        type="text"
                        value={user?.name || ""}
                        disabled
                        className="w-full cursor-not-allowed rounded-sm border border-hairline bg-raised px-3 py-2 text-sm text-ash"
                      />
                    </div>
                    <div>
                      <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">
                        Investigator ID
                      </label>
                      <input
                        type="text"
                        value={user?.investigatorId || ""}
                        disabled
                        className="w-full cursor-not-allowed rounded-sm border border-hairline bg-raised px-3 py-2 font-mono text-sm text-ash"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">
                        Role
                      </label>
                      <input
                        type="text"
                        value={user?.role || "Investigator"}
                        disabled
                        className="w-full cursor-not-allowed rounded-sm border border-hairline bg-raised px-3 py-2 text-sm text-ash"
                      />
                    </div>
                    <div>
                      <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">
                        Organization
                      </label>
                      <input
                        type="text"
                        value={user?.orgId || ""}
                        disabled
                        className="w-full cursor-not-allowed rounded-sm border border-hairline bg-raised px-3 py-2 font-mono text-sm text-ash"
                      />
                    </div>
                  </div>

                  {!showChangeRequest && (
                    <button
                      onClick={() => setShowChangeRequest(true)}
                      className="mt-2 w-full rounded-sm border border-amber bg-amber/10 py-2 text-sm text-amber transition-colors hover:bg-amber/20"
                    >
                      Request Profile Change
                    </button>
                  )}
                </div>
              </section>

              {/* Profile Change Request Form */}
              {showChangeRequest && (
                <section className="rounded-sm border border-amber/30 bg-amber/5 p-6">
                  <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-amber">
                    Request Profile Change
                  </h2>

                  {requestSubmitted ? (
                    <div className="rounded-sm border border-teal/40 bg-teal/10 p-4 text-center">
                      <p className="text-sm font-medium text-teal">
                        ✓ Request Submitted Successfully
                      </p>
                      <p className="mt-1 text-xs text-ash">
                        Your request will be reviewed by the organization head.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div>
                        <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">
                          Field to Change
                        </label>
                        <select
                          value={changeRequest.field}
                          onChange={(e) => {
                            const field = e.target.value;
                            let currentValue = "";
                            if (field === "name") currentValue = user?.name || "";
                            else if (field === "email") currentValue = user?.email || "";
                            else if (field === "phone") currentValue = user?.phone || "";
                            
                            setChangeRequest({
                              ...changeRequest,
                              field,
                              currentValue,
                            });
                          }}
                          className="w-full rounded-sm border border-hairline bg-ink px-3 py-2 text-sm text-paper focus:border-amber outline-none"
                        >
                          <option value="">Select a field...</option>
                          <option value="name">Name</option>
                          <option value="email">Email Address</option>
                          <option value="phone">Phone Number</option>
                          <option value="other">Other</option>
                        </select>
                      </div>

                      {changeRequest.field && (
                        <>
                          <div>
                            <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">
                              Current Value
                            </label>
                            <input
                              type="text"
                              value={changeRequest.currentValue}
                              onChange={(e) =>
                                setChangeRequest({
                                  ...changeRequest,
                                  currentValue: e.target.value,
                                })
                              }
                              placeholder="Current value (if any)"
                              className="w-full rounded-sm border border-hairline bg-ink px-3 py-2 text-sm text-paper placeholder:text-ash/60 focus:border-amber outline-none"
                            />
                          </div>

                          <div>
                            <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">
                              Requested New Value *
                            </label>
                            <input
                              type="text"
                              value={changeRequest.requestedValue}
                              onChange={(e) =>
                                setChangeRequest({
                                  ...changeRequest,
                                  requestedValue: e.target.value,
                                })
                              }
                              placeholder="Enter the new value you'd like"
                              className="w-full rounded-sm border border-hairline bg-ink px-3 py-2 text-sm text-paper placeholder:text-ash/60 focus:border-amber outline-none"
                            />
                          </div>

                          <div>
                            <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">
                              Reason for Change *
                            </label>
                            <textarea
                              value={changeRequest.reason}
                              onChange={(e) =>
                                setChangeRequest({
                                  ...changeRequest,
                                  reason: e.target.value,
                                })
                              }
                              placeholder="Please explain why this change is needed"
                              rows={3}
                              className="w-full rounded-sm border border-hairline bg-ink px-3 py-2 text-sm text-paper placeholder:text-ash/60 focus:border-amber outline-none resize-none"
                            />
                          </div>

                          <div className="flex gap-2">
                            <button
                              onClick={handleSubmitRequest}
                              disabled={!isFormValid}
                              className="flex-1 rounded-sm bg-amber px-4 py-2 text-sm font-medium text-ink transition-colors hover:bg-amber-hover disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              Submit Request
                            </button>
                            <button
                              onClick={() => {
                                setShowChangeRequest(false);
                                setChangeRequest({
                                  field: "",
                                  currentValue: "",
                                  requestedValue: "",
                                  reason: "",
                                });
                              }}
                              className="rounded-sm border border-hairline px-4 py-2 text-sm text-ash hover:border-amber hover:text-amber transition-colors"
                            >
                              Cancel
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  )}
                </section>
              )}

              {/* Notifications */}
              <section className="rounded-sm border border-hairline bg-panel p-6">
                <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-ash">
                  Notifications
                </h2>
                <div className="space-y-3">
                  <div className="flex items-center justify-between rounded-sm border border-hairline bg-ink px-4 py-3">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-paper">Case Assignments</p>
                      <p className="text-xs text-ash">
                        Notify when assigned to new cases
                      </p>
                    </div>
                    <button
                      onClick={() => toggleNotification('caseAssignments')}
                      className={`ml-4 rounded-sm px-4 py-1.5 text-xs font-medium transition-colors ${
                        notificationPreferences.caseAssignments
                          ? 'bg-amber text-ink hover:bg-amber-hover'
                          : 'border border-hairline bg-raised text-ash hover:border-amber hover:text-amber'
                      }`}
                    >
                      {notificationPreferences.caseAssignments ? 'Enabled' : 'Disabled'}
                    </button>
                  </div>
                  <div className="flex items-center justify-between rounded-sm border border-hairline bg-ink px-4 py-3">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-paper">File Upload Reminders</p>
                      <p className="text-xs text-ash">
                        Remind to upload case files
                      </p>
                    </div>
                    <button
                      onClick={() => toggleNotification('fileUploadReminders')}
                      className={`ml-4 rounded-sm px-4 py-1.5 text-xs font-medium transition-colors ${
                        notificationPreferences.fileUploadReminders
                          ? 'bg-amber text-ink hover:bg-amber-hover'
                          : 'border border-hairline bg-raised text-ash hover:border-amber hover:text-amber'
                      }`}
                    >
                      {notificationPreferences.fileUploadReminders ? 'Enabled' : 'Disabled'}
                    </button>
                  </div>
                  <div className="flex items-center justify-between rounded-sm border border-hairline bg-ink px-4 py-3">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-paper">Timeline Generation</p>
                      <p className="text-xs text-ash">
                        Notify when timeline is ready
                      </p>
                    </div>
                    <button
                      onClick={() => toggleNotification('timelineGeneration')}
                      className={`ml-4 rounded-sm px-4 py-1.5 text-xs font-medium transition-colors ${
                        notificationPreferences.timelineGeneration
                          ? 'bg-amber text-ink hover:bg-amber-hover'
                          : 'border border-hairline bg-raised text-ash hover:border-amber hover:text-amber'
                      }`}
                    >
                      {notificationPreferences.timelineGeneration ? 'Enabled' : 'Disabled'}
                    </button>
                  </div>
                </div>
              </section>
            </div>
          </main>
        </div>
        <PluginDrawer />
      </div>
    </PluginDrawerProvider>
  );
}
