// frontend/js/components/FileCard.js
import { formatDate, formatBytes } from "../utils/helpers.js";

// Get the template from the DOM once and reuse it
const template = document.getElementById("file-card-template");

export function createFileCard(file, currentUser, isAdminMode) {
  // Create a fresh copy of the template's content
  const card = template.content.cloneNode(true).firstElementChild;

  // --- Populate the static data ---
  card.dataset.fileId = file.filename;
  card.querySelector('[data-field="filename"]').textContent = file.filename;
  card.querySelector('[data-field="description"]').textContent =
    file.description || "";
  card.querySelector(
    '[data-field="modified_at"]'
  ).textContent = `Modified: ${formatDate(file.modified_at)}`;

  // --- Handle conditional visibility and content ---
  const revisionEl = card.querySelector('[data-field="revision"]');
  if (file.revision) {
    revisionEl.textContent = `REV ${file.revision}`;
    revisionEl.classList.remove("hidden");
  } else {
    revisionEl.classList.add("hidden");
  }

  const sizeContainer = card.querySelector('[data-field="size-container"]');
  if (file.is_link) {
    sizeContainer.classList.add("hidden");
  } else {
    card.querySelector(
      '[data-field="size"]'
    ).textContent = `Size: ${formatBytes(file.size)}`;
    sizeContainer.classList.remove("hidden");
  }

  // --- Handle complex state: Status Badge and Lock Info ---
  const statusEl = card.querySelector('[data-field="status"]');
  const lockInfoEl = card.querySelector('[data-field="lock-info"]');

  statusEl.className = "text-xs font-semibold px-2.5 py-1 rounded-full"; // Reset classes
  lockInfoEl.innerHTML = "";

  if (file.is_link) {
    statusEl.classList.add(
      "bg-purple-100",
      "text-purple-900",
      "dark:bg-purple-900",
      "dark:text-purple-200"
    );
    statusEl.innerHTML = `<i class="fa-solid fa-link mr-1"></i>Links to ${file.master_file}`;
  } else {
    switch (file.status) {
      case "unlocked":
        statusEl.classList.add(
          "bg-green-100",
          "text-green-900",
          "dark:bg-green-900",
          "dark:text-green-200"
        );
        statusEl.textContent = "Available";
        break;
      case "locked":
        statusEl.classList.add(
          "bg-red-100",
          "text-red-900",
          "dark:bg-red-900",
          "dark:text-red-200"
        );
        statusEl.textContent = `Locked by ${file.locked_by}`;
        lockInfoEl.innerHTML = `<i class="fa-solid fa-lock text-red-500"></i><span>Locked by: <strong>${
          file.locked_by
        }</strong> at ${formatDate(file.locked_at)}</span>`;
        break;
      case "checked_out_by_user":
        statusEl.classList.add(
          "bg-blue-100",
          "text-blue-900",
          "dark:bg-blue-900",
          "dark:text-blue-200"
        );
        statusEl.textContent = "Checked out by you";
        lockInfoEl.innerHTML = `<i class="fa-solid fa-lock-open text-blue-500"></i><span>You checked this out at ${formatDate(
          file.locked_at
        )}</span>`;
        break;
    }
  }

  // --- Generate Action Buttons ---
  // For now, we'll keep this logic here. In a more advanced setup,
  // buttons could even be their own components!
  const buttonsContainer = card.querySelector('[data-field="action-buttons"]');
  buttonsContainer.innerHTML = getActionButtons(file, currentUser, isAdminMode);

  return card;
}

// This function can stay here for now as a helper for the FileCard component.
function getActionButtons(file, currentUser, isAdminMode) {
  // NOTE: This is the same `getActionButtons` function from your original script.
  // Copy the full function here. For brevity, I've added a placeholder.
  return `<button class="btn btn-secondary js-history-btn" data-filename="${file.filename}">History</button>`;
}
