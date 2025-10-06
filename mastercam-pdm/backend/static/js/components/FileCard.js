// backend/static/js/components/FileCard.js

import { formatDate, formatBytes } from "../utils/helpers.js";
import { showCheckinDialog } from "./CheckinModal.js";
import { showHistoryDialog } from "./HistoryModal.js"; // NEW IMPORT
// We will need to create and import these functions for other buttons later
// import { checkoutFile, cancelCheckout, viewFileHistory } from '../api/service.js';

/**
 * Creates the full HTML for all action buttons based on the file's state.
 * @param {object} file The file object from the state.
 * @param {string} currentUser The currently logged-in user.
 * @param {boolean} isAdmin Is the current user an admin?
 * @returns {string} The HTML string for the buttons.
 */
function getActionButtons(file, currentUser, isAdmin) {
  const btnClass =
    "flex items-center space-x-2 px-4 py-2 rounded-md transition-all text-sm font-semibold border-2";
  let buttons = "";

  // Handle link files
  if (file.is_link) {
    buttons += `<button class="${btnClass} bg-purple-600 border-purple-800 text-white hover:bg-purple-700 js-view-master-btn" data-master-file="${file.master_file}"><i class="fa-solid fa-link"></i><span>View Master</span></button>`;
    buttons += `<button class="${btnClass} bg-gray-200 border-gray-400 text-gray-800 hover:bg-gray-300 js-history-btn" data-filename="${file.filename}"><i class="fa-solid fa-history"></i><span>History</span></button>`;
    if (isAdmin) {
      buttons += `<button class="${btnClass} bg-red-600 border-red-800 text-white hover:bg-red-700 js-delete-btn" data-filename="${file.filename}"><i class="fa-solid fa-trash-can"></i><span>Remove Link</span></button>`;
    }
    return buttons;
  }

  // Handle regular files
  switch (file.status) {
    case "unlocked":
      buttons += `<button class="${btnClass} bg-green-600 border-green-800 text-white hover:bg-green-700 js-checkout-btn" data-filename="${file.filename}"><i class="fa-solid fa-download"></i><span>Checkout</span></button>`;
      buttons += `<button class="${btnClass} bg-gray-200 border-gray-400 text-gray-800 hover:bg-gray-300 js-download-btn" data-filename="${file.filename}"><i class="fa-solid fa-file-arrow-down"></i><span>Download</span></button>`;
      break;
    case "checked_out_by_user":
      buttons += `<button class="${btnClass} bg-blue-600 border-blue-800 text-white hover:bg-blue-700 js-checkin-btn" data-filename="${file.filename}"><i class="fa-solid fa-upload"></i><span>Check In</span></button>`;
      buttons += `<button class="${btnClass} bg-yellow-600 border-yellow-800 text-white hover:bg-yellow-700 js-cancel-checkout-btn" data-filename="${file.filename}"><i class="fa-solid fa-times"></i><span>Cancel</span></button>`;
      break;
    case "locked":
      if (isAdmin) {
        buttons += `<button class="${btnClass} bg-orange-500 border-orange-700 text-white hover:bg-orange-600 js-override-btn" data-filename="${file.filename}"><i class="fa-solid fa-unlock"></i><span>Override</span></button>`;
      }
      buttons += `<button class="${btnClass} bg-gray-200 border-gray-400 text-gray-800 hover:bg-gray-300 js-download-btn" data-filename="${file.filename}"><i class="fa-solid fa-eye"></i><span>View</span></button>`;
      break;
  }

  buttons += `<button class="${btnClass} bg-gray-200 border-gray-400 text-gray-800 hover:bg-gray-300 js-history-btn" data-filename="${file.filename}"><i class="fa-solid fa-history"></i><span>History</span></button>`;

  if (isAdmin) {
    buttons += `<button class="${btnClass} bg-red-600 border-red-800 text-white hover:bg-red-700 js-delete-btn" data-filename="${file.filename}"><i class="fa-solid fa-trash-can"></i><span>Delete</span></button>`;
  }

  return buttons;
}

export function createFileCard(file, currentUser, isAdmin) {
  const template = document.getElementById("file-card-template");
  const card = template.content.cloneNode(true).firstElementChild;

  card.dataset.fileId = file.filename;
  card.querySelector('[data-field="filename"]').textContent = file.filename;
  card.querySelector('[data-field="description"]').textContent =
    file.description || "";
  card.querySelector(
    '[data-field="modified_at"]'
  ).textContent = `Modified: ${formatDate(file.modified_at)}`;

  const revisionEl = card.querySelector('[data-field="revision"]');
  if (file.revision) {
    revisionEl.textContent = `REV ${file.revision}`;
    revisionEl.style.display = "inline-block";
  } else {
    revisionEl.style.display = "none";
  }

  const sizeContainer = card.querySelector('[data-field="size-container"]');
  if (file.is_link) {
    sizeContainer.style.display = "none";
  } else {
    card.querySelector(
      '[data-field="size"]'
    ).textContent = `Size: ${formatBytes(file.size)}`;
    sizeContainer.style.display = "flex";
  }

  const statusEl = card.querySelector('[data-field="status"]');
  const lockInfoEl = card.querySelector('[data-field="lock-info"]');

  statusEl.className = "text-xs font-semibold px-2.5 py-1 rounded-full";
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

  const buttonsContainer = card.querySelector('[data-field="action-buttons"]');
  buttonsContainer.innerHTML = getActionButtons(file, currentUser, isAdmin);

  // Add event listeners for the new buttons
  // Inside the "Add Event Listeners" section at the bottom
  const historyBtn = buttonsContainer.querySelector(".js-history-btn");
  if (historyBtn) {
    historyBtn.addEventListener("click", () => {
      showHistoryDialog(file.filename);
    });

    const checkinBtn = buttonsContainer.querySelector(".js-checkin-btn");
    if (checkinBtn) {
      checkinBtn.addEventListener("click", () => {
        showCheckinDialog(file);
      });
    }

    // We can add the rest of the button event listeners here later,
    // calling functions from our api/service.js file.

    return card;
  }
}
