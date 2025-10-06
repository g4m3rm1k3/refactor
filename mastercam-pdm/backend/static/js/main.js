// frontend/js/main.js

import { formatDate } from "./utils/helpers.js";
import { getConfig, getFiles } from "./api/service.js";
import { setState, subscribe, getState } from "./state/store.js";
import { createFileCard } from "./components/FileCard.js";
import { showNewUploadDialog } from "./components/NewUploadModal.js"; // NEW
import { showDashboardDialog } from "./components/DashboardModal.js";
import { setupConfigPanel } from "./components/ConfigPanel.js"; // NEW IMPORT
import { connectWebSocket } from "./services/websocket.js"; // NEW IMPORT

const fileListEl = document.getElementById("fileList");

// --- RENDER FUNCTION ---
function render(state) {
  console.log("🚀 Render triggered!", state);
  fileListEl.innerHTML = "";

  if (!state.isConfigured) {
    fileListEl.innerHTML = `<p class="text-center text-gray-500">Application is not configured.</p>`;
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

    groupDetails.innerHTML = `
      <summary class="cursor-pointer p-4 font-semibold text-lg">
        <i class="fa-solid fa-folder mr-2 text-amber-500"></i>${groupName}
      </summary>
      <div class="p-4 space-y-4"></div>
    `;

    const filesContainer = groupDetails.querySelector(".space-y-4");
    for (const file of state.groupedFiles[groupName]) {
      const fileCardElement = createFileCard(
        file,
        state.currentUser,
        state.isAdmin
      );
      filesContainer.appendChild(fileCardElement);
    }
    fileListEl.appendChild(groupDetails);
  }
}

// --- INITIALIZATION LOGIC ---
async function initialize() {
  console.log("Initializing app...");
  try {
    const config = await getConfig();
    console.log("✅ Config loaded:", config);

    setState({
      isConfigured: config.has_token,
      currentUser: config.username,
      isAdmin: config.is_admin,
    });

    if (config.has_token) {
      connectWebSocket(); // NEW
      const filesData = await getFiles();
      console.log("✅ Files loaded:", filesData);
      setState({ groupedFiles: filesData });
    }
  } catch (error) {
    console.error("❌ Initialization failed:", error.message);
  }
}

// --- APP START ---
subscribe(render);

document.addEventListener("DOMContentLoaded", function () {
  console.log("DOM fully loaded and parsed.");

  // NEW: ADD EVENT LISTENERS FOR STATIC BUTTONS
  const newFileBtn = document.getElementById("newFileBtn");
  if (newFileBtn) {
    newFileBtn.addEventListener("click", showNewUploadDialog);
  }
  // We will add more listeners for other header buttons here later.
  // NEW: Add listener for the dashboard button
  document
    .getElementById("dashboardBtn")
    ?.addEventListener("click", showDashboardDialog);
  // NEW: Set up the config panel and connect it to its trigger button
  setupConfigPanel("configBtn");

  // Now, run the main initialization logic
  initialize();
});
