// frontend/js/main.js

import { formatDate } from "./utils/helpers.js";
import { getConfig, getFiles } from "./api/service.js";
// NEW: Import our state management functions
import { setState, subscribe, getState } from "./state/store.js";

// --- RENDER FUNCTION ---
// This function will be responsible for updating the UI. For now, it just logs to the console.
// It receives the complete, up-to-date state as its only argument.
function render(state) {
  console.log("🚀 Render triggered! The new state is:", state);
  // In the next steps, we will add code here to update the DOM.
}

// --- INITIALIZATION LOGIC ---
async function initialize() {
  console.log("DOM fully loaded. Initializing app...");
  try {
    const config = await getConfig();
    console.log("✅ Config loaded:", config);

    // Use setState to update our central store with the config info.
    setState({
      isConfigured: config.has_token,
      currentUser: config.username,
      isAdmin: config.is_admin,
    });

    if (config.has_token) {
      const filesData = await getFiles();
      console.log("✅ Files loaded:", filesData);
      // Use setState again to update the files in our store.
      // This will automatically trigger our 'render' function!
      setState({ groupedFiles: filesData });
    }
  } catch (error) {
    console.error("❌ Initialization failed:", error.message);
  }
}

// --- APP START ---

// 1. Subscribe our render function to state changes.
// From now on, ANY call to setState() anywhere in the app will cause `render()` to run.
subscribe(render);

// 2. Start the application initialization process when the DOM is ready.
document.addEventListener("DOMContentLoaded", initialize);
