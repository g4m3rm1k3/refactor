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
