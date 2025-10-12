// frontend/js/components/ConfigPanel.js

import { Modal } from "./Modal.js";
import { saveConfig, getConfig } from "../api/service.js";
import { showNotification } from "../utils/helpers.js";
import { getState } from "../state/store.js";

let panelElement = null;

function closePanel() {
  if (panelElement) {
    panelElement.classList.add("translate-x-full");
    panelElement.addEventListener(
      "transitionend",
      () => {
        panelElement.remove();
        panelElement = null;
      },
      { once: true }
    );
  }
}

function switchTab(tabName) {
  if (!panelElement) return;

  // Hide all content sections
  panelElement.querySelectorAll(".config-tab-content").forEach((content) => {
    content.classList.add("hidden");
  });

  // Deactivate all tabs
  panelElement.querySelectorAll(".config-tab").forEach((tab) => {
    tab.classList.remove("active");
  });

  // Show selected content
  const contentId = `${tabName}Content`;
  const content = panelElement.querySelector(`#${contentId}`);
  if (content) {
    content.classList.remove("hidden");
  }

  // Activate selected tab
  const tab = panelElement.querySelector(`#${tabName}Tab`);
  if (tab) {
    tab.classList.add("active");
  }

  // Load specific tab content
  if (tabName === "health") {
    loadHealthStatus();
  } else if (tabName === "users") {
    loadUserManagement();
  }
}

async function handleConfigFormSubmit(event) {
  event.preventDefault();
  const form = event.target;

  const configData = {
    base_url: form.querySelector("#gitlabUrl").value,
    project_id: form.querySelector("#projectId").value,
    username: form.querySelector("#username").value,
    token: form.querySelector("#token").value,
    allow_insecure_ssl: form.querySelector("#allowInsecureSsl").checked,
  };

  try {
    const result = await saveConfig(configData);
    showNotification(
      "Configuration saved! Please restart the application for changes to take effect.",
      "success"
    );
    closePanel();
  } catch (error) {
    showNotification(`Error saving configuration: ${error.message}`, "error");
  }
}

// Admin actions handlers
async function handleCreateBackup() {
  if (!confirm("Create a backup of the repository?")) return;

  try {
    const response = await fetch("/admin/create_backup", {
      method: "POST",
      credentials: "include",
    });

    if (!response.ok) throw new Error("Backup failed");

    const data = await response.json();
    showNotification(
      `Backup created successfully at: ${data.backup_path}`,
      "success"
    );
  } catch (error) {
    showNotification(`Backup failed: ${error.message}`, "error");
  }
}

async function handleCleanupLFS() {
  if (!confirm("Clean up old LFS files? This may take a few minutes.")) return;

  try {
    showNotification("LFS cleanup in progress...", "info");
    const response = await fetch("/admin/cleanup_lfs", {
      method: "POST",
      credentials: "include",
    });

    if (!response.ok) throw new Error("Cleanup failed");

    const data = await response.json();
    showNotification("LFS cleanup completed successfully", "success");
  } catch (error) {
    showNotification(`Cleanup failed: ${error.message}`, "error");
  }
}

async function handleExportRepo() {
  try {
    showNotification("Preparing repository export...", "info");
    const response = await fetch("/admin/export_repository", {
      method: "POST",
      credentials: "include",
    });

    if (!response.ok) throw new Error("Export failed");

    // Download the file
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `mastercam_export_${new Date().getTime()}.zip`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    showNotification("Repository exported successfully", "success");
  } catch (error) {
    showNotification(`Export failed: ${error.message}`, "error");
  }
}

async function handleResetRepo() {
  if (
    !confirm(
      "⚠️ WARNING: This will DELETE your local repository and re-clone from GitLab.\n\nAll local changes will be LOST!\n\nAre you absolutely sure?"
    )
  ) {
    return;
  }

  if (
    !confirm("Last chance! This action cannot be undone. Continue with reset?")
  ) {
    return;
  }

  try {
    showNotification("Resetting repository...", "warning");
    const response = await fetch("/admin/reset_repository", {
      method: "POST",
      credentials: "include",
    });

    if (!response.ok) throw new Error("Reset failed");

    showNotification(
      "Repository reset successfully. Please refresh the page.",
      "success"
    );

    // Refresh page after 2 seconds
    setTimeout(() => {
      window.location.reload();
    }, 2000);
  } catch (error) {
    showNotification(`Reset failed: ${error.message}`, "error");
  }
}

async function loadHealthStatus() {
  const healthContent = panelElement.querySelector("#healthContent");
  if (!healthContent) return;

  healthContent.innerHTML = `
    <div class="space-y-4">
      <div class="health-card">
        <div class="flex justify-between items-center">
          <span class="font-semibold">GitLab Connection</span>
          <span class="health-status checking">Checking...</span>
        </div>
      </div>
      <div class="health-card">
        <div class="flex justify-between items-center">
          <span class="font-semibold">Local Repository</span>
          <span class="health-status checking">Checking...</span>
        </div>
      </div>
      <div class="health-card">
        <div class="flex justify-between items-center">
          <span class="font-semibold">Git LFS</span>
          <span class="health-status checking">Checking...</span>
        </div>
      </div>
    </div>
  `;

  // TODO: Implement actual health checks via API
  // For now, show as OK
  setTimeout(() => {
    healthContent.querySelectorAll(".health-status").forEach((el) => {
      el.textContent = "OK";
      el.classList.remove("checking");
      el.classList.add("ok");
    });
  }, 500);
}

async function loadUserManagement() {
  const usersContent = panelElement.querySelector("#usersContent");
  if (!usersContent) return;

  try {
    const response = await fetch("/admin/users", {
      credentials: "include",
    });

    if (!response.ok) throw new Error("Failed to load users");

    const data = await response.json();
    const users = data.users || [];

    usersContent.innerHTML = `
      <div class="space-y-4">
        <div class="flex justify-between items-center">
          <h4 class="text-lg font-semibold">System Users</h4>
          <button id="addUserBtn" class="btn btn-primary btn-sm">
            <i class="fa-solid fa-user-plus"></i> Add User
          </button>
        </div>
        <div class="space-y-2">
          ${
            users.length === 0
              ? '<p class="text-gray-500">No users found</p>'
              : users
                  .map(
                    (user) => `
            <div class="p-3 border border-gray-300 dark:border-gray-600 rounded-lg flex justify-between items-center">
              <div>
                <p class="font-semibold">${user.username}</p>
                <p class="text-xs text-gray-500">${user.is_admin ? "Admin" : "User"}</p>
              </div>
              <div class="space-x-2">
                <button class="btn btn-sm btn-secondary" onclick="resetUserPassword('${user.username}')">
                  Reset Password
                </button>
                ${
                  !user.is_admin
                    ? `<button class="btn btn-sm bg-red-600 text-white" onclick="deleteUser('${user.username}')">Delete</button>`
                    : ""
                }
              </div>
            </div>
          `
                  )
                  .join("")
          }
        </div>
      </div>
    `;

    // TODO: Add event listeners for add/delete/reset user actions
  } catch (error) {
    usersContent.innerHTML = `<p class="text-red-500">Error loading users: ${error.message}</p>`;
  }
}

async function loadConfigStatus() {
  try {
    const config = await getConfig();
    const statusText = panelElement.querySelector("#configStatusText");
    const repoText = panelElement.querySelector("#configRepoText");

    if (statusText) {
      statusText.textContent = config.has_token ? "✅ Configured" : "❌ Not Configured";
    }

    if (repoText) {
      repoText.textContent = config.repo_path || "Not set";
    }

    // Pre-fill form with current values
    const form = panelElement.querySelector("#configForm");
    if (form && config) {
      form.querySelector("#gitlabUrl").value = config.gitlab_url || "";
      form.querySelector("#projectId").value = config.project_id || "";
      form.querySelector("#username").value = config.username || "";
      // Don't pre-fill token for security
    }
  } catch (error) {
    console.error("Failed to load config status:", error);
  }
}

function openPanel() {
  if (panelElement) return;

  const template = document.getElementById("template-config-panel");
  const content = template.content.cloneNode(true);
  panelElement = content.firstElementChild;

  // Add event listeners for closing
  panelElement
    .querySelector('[data-action="close"]')
    .addEventListener("click", closePanel);

  // Add event listeners for tab switching
  panelElement.querySelectorAll(".config-tab").forEach((tabButton) => {
    tabButton.addEventListener("click", () => {
      const tabName = tabButton.id.replace("Tab", "");
      switchTab(tabName);
    });
  });

  // Show/hide admin and users tabs based on user role
  const state = getState();
  if (state.isAdmin) {
    panelElement.querySelector("#adminTab")?.classList.remove("hidden");
    panelElement.querySelector("#usersTab")?.classList.remove("hidden");
  }

  // Add event listener for the config form submission
  const configForm = panelElement.querySelector("#configForm");
  if (configForm) {
    configForm.addEventListener("submit", handleConfigFormSubmit);
  }

  // Add event listeners for admin actions
  panelElement.querySelector("#createBackupBtn")?.addEventListener("click", handleCreateBackup);
  panelElement.querySelector("#cleanupLfsBtn")?.addEventListener("click", handleCleanupLFS);
  panelElement.querySelector("#exportRepoBtn")?.addEventListener("click", handleExportRepo);
  panelElement.querySelector("#resetRepoBtn")?.addEventListener("click", handleResetRepo);

  document.body.appendChild(panelElement);

  // Load initial config status
  loadConfigStatus();

  requestAnimationFrame(() => {
    panelElement.classList.remove("translate-x-full");
  });
}

export function setupConfigPanel(triggerButtonId) {
  const triggerButton = document.getElementById(triggerButtonId);
  if (triggerButton) {
    triggerButton.addEventListener("click", openPanel);
  }
}
