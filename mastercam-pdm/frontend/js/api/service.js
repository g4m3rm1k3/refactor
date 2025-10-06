// frontend/js/api/service.js

const BASE_URL = ""; // The API is on the same origin, so we don't need a base URL.

/**
 * A helper function to handle the response from a fetch call.
 * It checks if the response was successful and throws an error with details if not.
 * @param {Response} response The fetch Response object.
 * @returns {Promise<any>} The JSON data from the response.
 */
async function handleResponse(response) {
  if (response.ok) {
    // If the response has content, parse it as JSON. Otherwise, return success.
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return response.json();
    }
    return { status: "success" };
  } else {
    // If the server returned an error, parse the error detail and throw it.
    const errorData = await response.json();
    throw new Error(
      errorData.detail || `Request failed with status ${response.status}`
    );
  }
}

/**
 * Gets the current authentication token.
 * Later, we will get this from our state store, but localStorage is fine for now.
 * @returns {string|null} The auth token.
 */
function getAuthToken() {
  return localStorage.getItem("auth_token");
}

/**
 * Fetches the current application configuration summary.
 */
export async function getConfig() {
  const response = await fetch(`${BASE_URL}/config`);
  return handleResponse(response);
}

/**
 * Fetches the complete, grouped list of files.
 */
export async function getFiles() {
  const token = getAuthToken();
  const response = await fetch(`${BASE_URL}/files`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return handleResponse(response);
}

/**
 * Sends a request to check out (lock) a file.
 * @param {string} filename The name of the file to check out.
 * @param {string} user The user checking out the file.
 */
export async function checkoutFile(filename, user) {
  const token = getAuthToken();
  const response = await fetch(`${BASE_URL}/files/${filename}/checkout`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ user: user }),
  });
  return handleResponse(response);
}

// We will add more functions here for checkin, login, etc., as we need them.
export async function getDashboardStats() {
  const token = getAuthToken();
  const response = await fetch(`${BASE_URL}/dashboard/stats`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse(response);
}
export async function getActivityFeed(limit = 50, offset = 0) {
  const token = getAuthToken();
  const response = await fetch(
    `${BASE_URL}/dashboard/activity?limit=${limit}&offset=${offset}`,
    {
      headers: { Authorization: `Bearer ${token}` },
    }
  );
  return handleResponse(response);
}
