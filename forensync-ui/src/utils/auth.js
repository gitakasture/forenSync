// Simple mock auth/role helper — replace with real session/JWT handling
// once the backend exists. Role is set at login and read anywhere in the app.

// const ROLE_KEY = "forensync_role";

// export function setRole(role) {
//   localStorage.setItem(ROLE_KEY, role);
// }

// export function getRole() {
//   return localStorage.getItem(ROLE_KEY) || "investigator";
// }

// export function isOrgHead() {
//   return getRole() === "head";
// }

// export function logout() {
//   localStorage.removeItem(ROLE_KEY);
// }


// Simple mock auth/role helper — replace with real session/JWT handling
// once the backend exists. Role is set at login and read anywhere in the app.

const USER_KEY = "forensync_user";

export function setUser(userData) {
  localStorage.setItem(USER_KEY, JSON.stringify(userData));
}

export function getUser() {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

export function setRole(role) {
  // kept for backward compatibility with existing calls
  const current = getUser() || {};
  setUser({ ...current, role });
}

export function getRole() {
  return getUser()?.role || "investigator";
}

export function isOrgHead() {
  return getRole() === "head";
}

export function logout() {
  localStorage.removeItem(USER_KEY);
}