// backend/static/js/main.js

import { getConfig, getFiles } from "./api/service.js";
import { setState, subscribe, getState } from "./state/store.js";
import { createFileCard } from "./components/FileCard.js";
import { setupConfigPanel } from "./components/ConfigPanel.js";
import { connectWebSocket } from "./services/websocket.js";
import { showAuthDialog } from "./components/LoginModal.js";
import { checkSession, checkPasswordExists } from "./services/auth.js";
import { showDashboardDialog } from "./components/DashboardModal.js";
import { showNewUploadDialog } from "./components/NewUploadModal.js";
import { showNotification } from "./utils/helpers.js";
import { toggleTooltips, initTooltipSystem } from "./utils/tooltips.js";

const fileListEl = document.getElementById("fileList");
let appState = {}; // Keep a local copy of state to compare old vs. new

function render(state) {
  appState = state; // Update our local copy for the subscribe function to use

  // --- Header Updates ---
  const currentUserEl = document.getElementById("currentUser");
  if (currentUserEl) {
    currentUserEl.textContent = state.currentUser || "Not Logged In";
  }
  const statusIndicators = document.getElementById("status-indicators");
  if (statusIndicators) {
    statusIndicators.style.display = state.isAuthenticated ? "flex" : "none";
  }

  // --- Admin Mode Toggle Button ---
  const adminActionsContainer = document.getElementById("adminActionsContainer");
  if (adminActionsContainer && state.isAdmin && state.isAuthenticated) {
    // Show admin mode toggle if user is admin
    if (!document.getElementById("adminModeToggle")) {
      adminActionsContainer.innerHTML = `
        <button
          id="adminModeToggle"
          class="btn btn-secondary"
          title="Toggle Admin Mode"
        >
          <i class="fa-solid fa-shield-halved"></i>
          <span class="hidden lg:inline">Admin</span>
        </button>
      `;
      // Wire up the admin toggle button
      document.getElementById("adminModeToggle")?.addEventListener("click", toggleAdminMode);
    }
    // Update button state based on admin mode
    const toggleBtn = document.getElementById("adminModeToggle");
    if (toggleBtn) {
      if (state.isAdminModeEnabled) {
        toggleBtn.classList.remove("btn-secondary");
        toggleBtn.classList.add("btn-primary", "ring-2", "ring-amber-400");
      } else {
        toggleBtn.classList.add("btn-secondary");
        toggleBtn.classList.remove("btn-primary", "ring-2", "ring-amber-400");
      }
    }
  } else if (adminActionsContainer) {
    adminActionsContainer.innerHTML = "";
  }

  // --- File List Rendering with Subgroups ---

  // Save folder open/closed states BEFORE clearing
  const detailsStates = new Map();
  document.querySelectorAll("#fileList details").forEach((detail) => {
    const summaryText = detail.querySelector("summary")?.textContent || "";
    detailsStates.set(summaryText.trim(), detail.open);
  });

  fileListEl.innerHTML = "";
  if (!state.isConfigured) {
    fileListEl.innerHTML = `<p class="text-center text-gray-500">Application is not configured. Please open the settings panel.</p>`;
    return;
  }
  if (!state.isAuthenticated) {
    fileListEl.innerHTML = `<div class="flex justify-center items-center py-24"><div class="animate-spin rounded-full h-12 w-12 border-4 border-gray-300 border-t-amber-500"></div></div>`;
    return;
  }
  const fileGroups = Object.keys(state.groupedFiles).sort();
  if (fileGroups.length === 0) {
    fileListEl.innerHTML = `<p class="text-center text-gray-500">No files found.</p>`;
    return;
  }

  for (const groupName of fileGroups) {
    const groupFiles = state.groupedFiles[groupName];

    // Group files by subgroup (first 7 digits)
    const subgroups = {};
    for (const file of groupFiles) {
      const subgroupKey = file.subgroup || "other";
      if (!subgroups[subgroupKey]) {
        subgroups[subgroupKey] = [];
      }
      subgroups[subgroupKey].push(file);
    }

    // Create main group container
    const groupDetails = document.createElement("details");
    groupDetails.className = "bg-white dark:bg-gray-800 rounded-lg shadow-md";
    groupDetails.open = false; // Don't auto-expand groups
    groupDetails.innerHTML = `
      <summary class="cursor-pointer p-4 font-semibold text-lg">
        <i class="fa-solid fa-folder mr-2 text-amber-500"></i>${groupName}
        <span class="text-sm text-gray-500 ml-2">(${groupFiles.length} files)</span>
      </summary>
      <div class="p-4 space-y-4"></div>
    `;
    const groupContainer = groupDetails.querySelector(".space-y-4");

    // Render subgroups
    const subgroupKeys = Object.keys(subgroups).sort();

    if (subgroupKeys.length === 1 && subgroupKeys[0] === "other") {
      // No subgroups, render files directly
      for (const file of subgroups["other"]) {
        groupContainer.appendChild(
          createFileCard(file, state.currentUser, state.isAdminModeEnabled || false)
        );
      }
    } else {
      // Has subgroups, create nested structure
      for (const subgroupKey of subgroupKeys) {
        if (subgroupKey === "other") {
          // Files without subgroup go directly in main group
          for (const file of subgroups[subgroupKey]) {
            groupContainer.appendChild(
              createFileCard(file, state.currentUser, state.isAdminModeEnabled || false)
            );
          }
        } else {
          // Create subgroup
          const subgroupDetails = document.createElement("details");
          subgroupDetails.className = "ml-4 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600";
          subgroupDetails.open = false; // Don't auto-expand subgroups
          subgroupDetails.innerHTML = `
            <summary class="cursor-pointer p-3 font-medium text-md">
              <i class="fa-solid fa-folder-tree mr-2 text-blue-500"></i>${subgroupKey}
              <span class="text-xs text-gray-500 ml-2">(${subgroups[subgroupKey].length} files)</span>
            </summary>
            <div class="p-3 space-y-3"></div>
          `;
          const subgroupContainer = subgroupDetails.querySelector(".space-y-3");

          for (const file of subgroups[subgroupKey]) {
            subgroupContainer.appendChild(
              createFileCard(file, state.currentUser, state.isAdminModeEnabled || false)
            );
          }

          groupContainer.appendChild(subgroupDetails);
        }
      }
    }

    fileListEl.appendChild(groupDetails);
  }

  // Restore folder open/closed states AFTER rendering
  document.querySelectorAll("#fileList details").forEach((detail) => {
    const summaryText = detail.querySelector("summary")?.textContent?.trim() || "";
    if (detailsStates.has(summaryText)) {
      detail.open = detailsStates.get(summaryText);
    }
  });

  // Refresh tooltips for dynamic buttons
  import("./utils/tooltips.js").then(({refreshTooltips}) => refreshTooltips());
}

// --- Helper Functions ---
function applyThemePreference() {
  if (
    localStorage.theme === "dark" ||
    (!("theme" in localStorage) &&
      window.matchMedia("(prefers-color-scheme: dark)").matches)
  ) {
    document.documentElement.classList.add("dark");
  } else {
    document.documentElement.classList.remove("dark");
  }
}

function toggleDarkMode() {
  document.documentElement.classList.toggle("dark");
  localStorage.theme = document.documentElement.classList.contains("dark")
    ? "dark"
    : "light";
}

function toggleAdminMode() {
  const state = getState();
  const newAdminModeState = !state.isAdminModeEnabled;

  setState({ isAdminModeEnabled: newAdminModeState });

  showNotification(
    newAdminModeState ? "Admin mode enabled" : "Admin mode disabled",
    newAdminModeState ? "warning" : "info"
  );

  // The setState above will trigger the subscribe callback which calls render()
  // The render() function already handles saving/restoring folder states
}

// --- Main Application Logic ---
async function loadAppData() {
  console.log("Authenticated! Loading app data...");
  connectWebSocket();
  const filesData = await getFiles();
  setState({ groupedFiles: filesData });
}

async function runApp() {
  console.log("DOM fully loaded. Starting application.");

  try {
    // 1. First, try to validate the existing session cookie.
    const sessionUser = await checkSession();
    console.log("✅ Valid session found for user:", sessionUser.username);
    setState({
      currentUser: sessionUser.username,
      isAdmin: sessionUser.is_admin,
      isAuthenticated: true,
      isConfigured: true, // If we have a session, we must be configured
    });
    // The subscribe function will trigger loadAppData() automatically.
  } catch (error) {
    // 2. If session check fails, start the manual login flow.
    console.log("No valid session. Starting login flow.");
    try {
      const config = await getConfig();
      setState({ isConfigured: config.has_token });

      if (!config.has_token) return;

      const has_password = await checkPasswordExists(config.username);
      console.log(`Password check for ${config.username}: has_password=${has_password}`);
      // showAuthDialog now returns true on success, which triggers the subscribe logic
      await showAuthDialog(config.username, has_password);
    } catch (initError) {
      console.error(`❌ Initialization failed: ${initError.message}`);
    }
  }
}

// --- APP START ---
subscribe((newState) => {
  const oldIsAuthenticated = appState.isAuthenticated; // Capture BEFORE render updates it
  const wasNotAuthenticated = !oldIsAuthenticated;

  render(newState); // This updates appState

  // If we just became authenticated, load the files
  if (newState.isAuthenticated && wasNotAuthenticated) {
    console.log("Authentication state changed, loading files...");
    loadAppData();
  }
});

// --- Search Functionality ---
let searchDebounceTimer;
function handleSearch(searchTerm) {
  const term = searchTerm.toLowerCase().trim();
  const clearBtn = document.getElementById("clearSearchBtn");

  // Show/hide clear button
  if (clearBtn) {
    clearBtn.classList.toggle("hidden", !term);
  }

  // Get all file cards
  const allCards = document.querySelectorAll('[data-file-id]');
  const allGroups = document.querySelectorAll('#fileList > details');
  const allSubgroups = document.querySelectorAll('#fileList details details');

  if (!term) {
    // Show everything
    allCards.forEach(card => card.style.display = '');
    allGroups.forEach(group => group.style.display = '');
    allSubgroups.forEach(subgroup => subgroup.style.display = '');
    return;
  }

  // Hide all initially
  allCards.forEach(card => card.style.display = 'none');
  allSubgroups.forEach(subgroup => subgroup.style.display = 'none');
  allGroups.forEach(group => group.style.display = 'none');

  // Show matching cards and their containers
  allCards.forEach(card => {
    const filename = card.dataset.fileId?.toLowerCase() || '';
    const description = card.querySelector('[data-field="description"]')?.textContent?.toLowerCase() || '';

    if (filename.includes(term) || description.includes(term)) {
      card.style.display = '';

      // Show parent subgroup if exists
      let parent = card.closest('details details');
      if (parent) {
        parent.style.display = '';
      }

      // Show parent group
      parent = card.closest('#fileList > details');
      if (parent) {
        parent.style.display = '';
        parent.open = true; // Auto-expand to show results
      }
    }
  });

  // Open all visible subgroups to show results
  allSubgroups.forEach(subgroup => {
    if (subgroup.style.display !== 'none') {
      subgroup.open = true;
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  applyThemePreference();
  initTooltipSystem(); // Initialize tooltips

  // --- Wire up all static UI buttons ---
  setupConfigPanel("configBtn");
  document
    .getElementById("dashboardBtn")
    ?.addEventListener("click", showDashboardDialog);
  document
    .getElementById("newFileBtn")
    ?.addEventListener("click", showNewUploadDialog);
  document
    .getElementById("darkModeBtn")
    ?.addEventListener("click", toggleDarkMode);
  document
    .getElementById("tooltipBtn")
    ?.addEventListener("click", toggleTooltips);
  document
    .getElementById("logoutBtn")
    ?.addEventListener("click", handleLogout);

  const collapseAllBtn = document.getElementById("collapseAllBtn");
  if (collapseAllBtn) {
    collapseAllBtn.addEventListener("click", () => {
      document
        .querySelectorAll("#fileList details[open]")
        .forEach((detailsEl) => {
          detailsEl.open = false;
        });
    });
  }

  // --- Search functionality ---
  const searchInput = document.getElementById("searchInput");
  const clearSearchBtn = document.getElementById("clearSearchBtn");

  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      clearTimeout(searchDebounceTimer);
      searchDebounceTimer = setTimeout(() => {
        handleSearch(e.target.value);
      }, 300); // Debounce for performance
    });
  }

  if (clearSearchBtn) {
    clearSearchBtn.addEventListener("click", () => {
      if (searchInput) {
        searchInput.value = "";
        handleSearch("");
      }
    });
  }

  // Start the main application logic
  runApp();
});

// Logout functionality
async function handleLogout() {
  const { showConfirmDialog } = await import("./components/ConfirmModal.js");
  const confirmed = await showConfirmDialog(
    "Logout",
    "Are you sure you want to logout?"
  );

  if (confirmed) {
    const { logout } = await import("./services/auth.js");
    logout();
    // Reload to show login screen
    window.location.reload();
  }
}
