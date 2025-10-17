// backend/static/js/api/service.js

const BASE_URL = "";

export async function handleResponse(response) {
  if (response.ok) {
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return response.json();
    }
    return { status: "success" };
  } else {
    const errorData = await response.json();
    throw new Error(
      errorData.detail || `Request failed with status ${response.status}`
    );
  }
}

export async function getConfig() {
  const response = await fetch(`${BASE_URL}/config`, {
    credentials: "include",
  });
  return handleResponse(response);
}

export async function getFiles() {
  const response = await fetch(`${BASE_URL}/files`, {
    credentials: "include",
  });
  return handleResponse(response);
}

export async function checkoutFile(filename, user) {
  const response = await fetch(`${BASE_URL}/files/${filename}/checkout`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user: user }),
    credentials: "include",
  });
  return handleResponse(response);
}

export async function saveConfig(configData) {
  const response = await fetch(`${BASE_URL}/config/gitlab`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(configData),
    credentials: "include",
  });
  return handleResponse(response);
}

export async function getDashboardStats() {
  const response = await fetch(`${BASE_URL}/dashboard/stats`, {
    credentials: "include",
  });
  return handleResponse(response);
}

export async function getActivityFeed(limit = 50, offset = 0) {
  const response = await fetch(
    `${BASE_URL}/dashboard/activity?limit=${limit}&offset=${offset}`,
    {
      credentials: "include",
    }
  );
  return handleResponse(response);
}

// THIS IS THE MISSING FUNCTION
export async function getFileHistory(filename) {
  const response = await fetch(`${BASE_URL}/files/${filename}/history`, {
    credentials: "include",
  });
  return handleResponse(response);
}

export async function cancelCheckout(filename, user) {
  const response = await fetch(`/files/${filename}/cancel_checkout`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user }),
    credentials: "include",
  });
  return handleResponse(response);
}

export async function deleteFile(filename, adminUser) {
  const response = await fetch(`/admin/files/${filename}/delete`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ admin_user: adminUser }),
    credentials: "include",
  });
  return handleResponse(response);
}

export async function overrideLock(filename, adminUser) {
  const response = await fetch(`/admin/files/${filename}/override`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ admin_user: adminUser }),
    credentials: "include",
  });
  return handleResponse(response);
}

export async function uploadNewFile(formData) {
  const response = await fetch(`${BASE_URL}/files/new_upload`, {
    method: "POST",
    body: formData,
    credentials: "include",
  });
  return handleResponse(response);
}

export async function checkinFile(filename, file, commitMessage, user, revType = "minor", newMajorRev = null) {
  const formData = new FormData();
  formData.append("user", user);
  formData.append("file", file);
  formData.append("commit_message", commitMessage);
  formData.append("rev_type", revType);
  if (newMajorRev) {
    formData.append("new_major_rev", newMajorRev);
  }

  const response = await fetch(`${BASE_URL}/files/${filename}/checkin`, {
    method: "POST",
    body: formData,
    credentials: "include",
  });
  return handleResponse(response);
}

// ====================
// Admin Configuration API
// ====================

export async function getAdminConfig() {
  const response = await fetch(`${BASE_URL}/admin/config/`, {
    credentials: "include",
  });
  return handleResponse(response);
}

export async function updateAdminConfig(config, adminUser) {
  const response = await fetch(`${BASE_URL}/admin/config/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ config, admin_user: adminUser }),
    credentials: "include",
  });
  return handleResponse(response);
}

export async function getFilenamePatterns() {
  const response = await fetch(`${BASE_URL}/admin/config/patterns`, {
    credentials: "include",
  });
  return handleResponse(response);
}

export async function addFilenamePattern(pattern) {
  const response = await fetch(`${BASE_URL}/admin/config/patterns`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(pattern),
    credentials: "include",
  });
  return handleResponse(response);
}

export async function getRepositories() {
  const response = await fetch(`${BASE_URL}/admin/config/repositories`, {
    credentials: "include",
  });
  return handleResponse(response);
}

export async function addRepository(repository) {
  const response = await fetch(`${BASE_URL}/admin/config/repositories`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(repository),
    credentials: "include",
  });
  return handleResponse(response);
}

export async function getUserAccess() {
  const response = await fetch(`${BASE_URL}/admin/config/user-access`, {
    credentials: "include",
  });
  return handleResponse(response);
}

export async function updateUserAccess(userAccess) {
  const response = await fetch(`${BASE_URL}/admin/config/user-access`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(userAccess),
    credentials: "include",
  });
  return handleResponse(response);
}

export async function deleteUserAccess(username) {
  const response = await fetch(`${BASE_URL}/admin/config/user-access/${username}`, {
    method: "DELETE",
    credentials: "include",
  });
  return handleResponse(response);
}

export async function getMyRepositories() {
  const response = await fetch(`${BASE_URL}/admin/config/my-repositories`, {
    credentials: "include",
  });
  return handleResponse(response);
}

export async function getFileHistoryRevisions(filename, startRevision = null, endRevision = null, limit = 50) {
  let url = `${BASE_URL}/files/${filename}/history/revisions?limit=${limit}`;
  if (startRevision) url += `&start_revision=${startRevision}`;
  if (endRevision) url += `&end_revision=${endRevision}`;

  const response = await fetch(url, {
    credentials: "include",
  });
  return handleResponse(response);
}

export const apiService = {
  getConfig,
  saveConfig,
  getFiles,
  getFileHistory,
  getFileHistoryRevisions,
  checkoutFile,
  cancelCheckout,
  checkinFile,
  uploadNewFile,
  deleteFile,
  overrideLock,
  getDashboardStats,
  getActivityFeed,
  // Admin Config
  getAdminConfig,
  updateAdminConfig,
  getFilenamePatterns,
  addFilenamePattern,
  getRepositories,
  addRepository,
  getUserAccess,
  updateUserAccess,
  deleteUserAccess,
  getMyRepositories,
};

export async function deletePattern(patternName) {
  const response = await fetch(`${BASE_URL}/admin/config/patterns/${patternName}`, {
    method: "DELETE",
    credentials: "include",
  });
  return handleResponse(response);
}

export async function deleteRepository(repoId) {
  const response = await fetch(`${BASE_URL}/admin/config/repositories/${repoId}`, {
    method: "DELETE",
    credentials: "include",
  });
  return handleResponse(response);
}
