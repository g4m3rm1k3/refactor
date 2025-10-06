// frontend/js/main.js

// Import functions from our new modules!
import { formatDate } from "./utils/helpers.js";
import { getConfig, getFiles } from "./api/service.js";

console.log("Application main.js loaded!");
console.log("Current date formatted:", formatDate(new Date()));

document.addEventListener("DOMContentLoaded", async function () {
  console.log("DOM fully loaded. Initializing app...");

  try {
    // Use our new API service to fetch initial data
    const config = await getConfig();
    console.log("✅ Config loaded successfully:", config);

    // For now, we'll assume the user is authenticated for this test
    if (config.has_token) {
      const files = await getFiles();
      console.log("✅ Files loaded successfully:", files);
    } else {
      console.log("🏃 App is not configured. Skipping file load.");
    }
  } catch (error) {
    console.error("❌ Initialization failed:", error.message);
  }

  // The rest of our app initialization logic will go here.
});
