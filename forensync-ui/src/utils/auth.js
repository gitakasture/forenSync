// Simple mock auth/role helper — replace with real session/JWT handling
// once the backend exists. Role is set at login and read anywhere in the app.

const ROLE_KEY = "forensync_role";

export function setRole(role) {
  localStorage.setItem(ROLE_KEY, role);
}

export function getRole() {
  return localStorage.getItem(ROLE_KEY) || "investigator";
}

export function isOrgHead() {
  return getRole() === "head";
}

export function logout() {
  localStorage.removeItem(ROLE_KEY);
}
