// backend/static/js/services/auth.js
import { setState } from "../state/store.js";
import { handleResponse } from "../api/service.js";

export async function login(username, password) {
  const formData = new FormData();
  formData.append("username", username);
  formData.append("password", password);

  const response = await fetch("/auth/login", {
    method: "POST",
    body: formData,
    credentials: "include", // Tell fetch to send/receive cookies
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Login failed");
  }

  const result = await response.json();
  // The browser has the cookie. We just update the app's state.
  setState({
    currentUser: result.username,
    isAdmin: result.is_admin,
    isAuthenticated: true,
  });
  return result;
}

export async function setupInitialUser(username, gitlabToken, password) {
  const response = await fetch("/auth/setup-initial-user", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: username,
      gitlab_token: gitlabToken,
      new_password: password,
    }),
    credentials: "include", // Tell fetch to send/receive cookies
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Account setup failed");
  }

  const result = await response.json();
  // The browser handles the cookie. We just update the state.
  setState({
    currentUser: result.username,
    isAdmin: result.is_admin,
    isAuthenticated: true,
  });
  return result;
}

export async function checkPasswordExists(username) {
  const formData = new FormData();
  formData.append("username", username);
  const response = await fetch("/auth/check_password", {
    method: "POST",
    body: formData,
  });
  const data = await response.json();
  return data.has_password;
}

export function logout() {
  // A proper logout would call a /logout endpoint on the backend
  // to invalidate the cookie, but for now, a reload works.
  window.location.reload();
}

export async function checkSession() {
  // This function will either succeed and return user data (if the cookie is valid)
  // or fail with a 401 error (if the cookie is missing or invalid).
  const response = await fetch("/auth/me", { credentials: "include" });
  return handleResponse(response); // We need to add handleResponse to this file
}
