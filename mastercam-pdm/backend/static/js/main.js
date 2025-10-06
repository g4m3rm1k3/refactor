// backend/static/js/main.js

import { getConfig, getFiles } from "./api/service.js";
import { setState, subscribe, getState } from "./state/store.js";
import { createFileCard } from "./components/FileCard.js";
import { setupConfigPanel } from "./components/ConfigPanel.js";
import { connectWebSocket } from "./services/websocket.js";
import { showAuthDialog } from "./components/LoginModal.js";
import { checkPasswordExists } from "./services/auth.js";
import { showDashboardDialog } from "./components/DashboardModal.js";
import { checkSession, checkPasswordExists } from "./services/auth.js";

const fileListEl = document.getElementById("fileList");

// --- Main Render Function ---
function render(state) {
  // --- Header Updates ---
  const currentUserEl = document.getElementById("currentUser");
  if (currentUserEl) {
    currentUserEl.textContent = state.currentUser || "Not Logged In";
  }
  const statusIndicators = document.getElementById("status-indicators");
  if (state.isAuthenticated) {
    statusIndicators.classList.remove("hidden");
  }

  // --- File List Updates ---
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
        createFileCard(file, state.currentUser, state.isAdmin)
      );
    }
    fileListEl.appendChild(groupDetails);
  }
}

// --- Dark Mode Logic ---
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
    const config = await getConfig();
    setState({ isConfigured: config.has_token });

    if (!config.has_token) return;

    const hasPassword = await checkPasswordExists(config.username);
    const loginSuccess = await showAuthDialog(config.username, hasPassword);

    if (loginSuccess) {
      await loadAppData();
    }
  } catch (error) {
    console.error(`❌ Initialization failed: ${error.message}`);
  }
}

// --- APP START ---
subscribe(render);

document.addEventListener("DOMContentLoaded", () => {
  applyThemePreference();

  // --- Wire up all static UI buttons ---
  setupConfigPanel("configBtn");
  document
    .getElementById("dashboardBtn")
    ?.addEventListener("click", showDashboardDialog);
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
