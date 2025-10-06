// frontend/js/main.js

// We use the 'import' keyword to use functions from other modules.
import { formatDate } from "./utils/helpers.js";

console.log("Application main.js loaded!");

// Example of using an imported function:
console.log("Current date formatted:", formatDate(new Date()));

document.addEventListener("DOMContentLoaded", async function () {
  console.log(
    "DOM fully loaded and parsed. App initialization will start here."
  );
  // All the logic from your old 'DOMContentLoaded' will eventually move here.
});
