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
          class="btn btn-secondary !px-3"
          title="Toggle Admin Mode"
        >
          <i class="fa-solid fa-shield-halved"></i>
        </button>
      `;
      // Wire up the admin toggle button
      document.getElementById("adminModeToggle")?.addEventListener("click", toggleAdminMode);
    }
  } else if (adminActionsContainer) {
    adminActionsContainer.innerHTML = "";
  }

  // --- File List Rendering ---
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
    const groupDetails = document.createElement("details");
    groupDetails.className = "bg-white dark:bg-gray-800 rounded-lg shadow-md";
    groupDetails.open = true;
    groupDetails.innerHTML = `<summary class="cursor-pointer p-4 font-semibold text-lg"><i class="fa-solid fa-folder mr-2 text-amber-500"></i>${groupName}</summary><div class="p-4 space-y-4"></div>`;
    const filesContainer = groupDetails.querySelector(".space-y-4");
    for (const file of state.groupedFiles[groupName]) {
      filesContainer.appendChild(
        createFileCard(file, state.currentUser, state.isAdminModeEnabled || false)
      );
    }
    fileListEl.appendChild(groupDetails);
  }
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

  // Update button appearance
  const toggleBtn = document.getElementById("adminModeToggle");
  if (toggleBtn) {
    if (newAdminModeState) {
      toggleBtn.classList.remove("btn-secondary");
      toggleBtn.classList.add("btn-primary");
      toggleBtn.classList.add("ring-2", "ring-amber-400");
    } else {
      toggleBtn.classList.add("btn-secondary");
      toggleBtn.classList.remove("btn-primary");
      toggleBtn.classList.remove("ring-2", "ring-amber-400");
    }
  }

  showNotification(
    newAdminModeState ? "Admin mode enabled" : "Admin mode disabled",
    newAdminModeState ? "warning" : "info"
  );

  // Re-render file cards with new admin mode state
  const fileGroups = Object.keys(state.groupedFiles || {});
  for (const groupName of fileGroups) {
    const groupDetails = Array.from(fileListEl.querySelectorAll("details")).find(
      (el) => el.querySelector("summary").textContent.includes(groupName)
    );
    if (groupDetails) {
      const filesContainer = groupDetails.querySelector(".space-y-4");
      filesContainer.innerHTML = "";
      for (const file of state.groupedFiles[groupName]) {
        filesContainer.appendChild(
          createFileCard(file, state.currentUser, newAdminModeState)
        );
      }
    }
  }
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

      const { has_password } = await checkPasswordExists(config.username);
      // showAuthDialog now returns true on success, which triggers the subscribe logic
      await showAuthDialog(config.username, has_password);
    } catch (initError) {
      console.error(`❌ Initialization failed: ${initError.message}`);
    }
  }
}

// --- APP START ---
subscribe((newState) => {
  const oldIsAuthenticated = appState.isAuthenticated;
  render(newState);
  if (newState.isAuthenticated && !oldIsAuthenticated) {
    loadAppData();
  }
});

document.addEventListener("DOMContentLoaded", () => {
  applyThemePreference();

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

  // Start the main application logic
  runApp();
});
