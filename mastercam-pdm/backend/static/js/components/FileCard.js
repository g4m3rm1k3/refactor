// backend/static/js/components/FileCard.js

import { formatDate, formatBytes, showNotification } from "../utils/helpers.js";
import { showCheckinDialog } from "./CheckinModal.js";
import { showHistoryDialog } from "./HistoryModal.js";
import { showConfirmDialog } from "./ConfirmModal.js";
import { showCheckoutDialog } from "./CheckoutModal.js";
import { showStatusDialog } from "./StatusModal.js";
import { showViewOnlyDialog } from "./ViewOnlyModal.js";
import {
  getFiles,
  cancelCheckout,
  deleteFile,
  overrideLock,
} from "../api/service.js";
import { setState } from "../state/store.js";
import { attachTooltipToDynamicElement, refreshTooltips } from "../utils/tooltips.js";

/**
 * Creates the full HTML for all action buttons based on the file's state.
 * This is your complete and correct function.
 */
function getActionButtons(file, currentUser, isAdmin) {
  const btnBase = "btn";
  let buttons = "";

  if (file.is_link) {
    buttons += `<button class="${btnBase} file-btn-link js-view-master-btn" data-master-file="${file.master_file}" data-tooltip-key="viewMasterBtn"><i class="fa-solid fa-link"></i><span>View Master</span></button>`;
    // NO history button for links
    if (isAdmin) {
      buttons += `<button class="${btnBase} file-btn-delete js-delete-btn" data-tooltip-key="deleteLinkBtn"><i class="fa-solid fa-trash-can"></i><span>Remove Link</span></button>`;
    }
    return buttons;
  }

  // Download button - always allow downloading (view-only if not checked out)
  const downloadLabel = file.status === "checked_out_by_user" ? "Download" : "View (Read-Only)";
  const downloadBtn = `<button class="${btnBase} file-btn-download js-download-btn" data-tooltip-key="downloadBtn"><i class="fa-solid fa-file-arrow-down"></i><span>${downloadLabel}</span></button>`;

  switch (file.status) {
    case "unlocked":
      buttons += `<button class="${btnBase} file-btn-checkout js-checkout-btn" data-tooltip-key="checkoutBtn"><i class="fa-solid fa-download"></i><span>Checkout</span></button>`;
      break;
    case "checked_out_by_user":
      buttons += `<button class="${btnBase} file-btn-checkin js-checkin-btn" data-tooltip-key="checkinBtn"><i class="fa-solid fa-upload"></i><span>Check In</span></button>`;
      buttons += `<button class="${btnBase} file-btn-cancel js-cancel-checkout-btn" data-tooltip-key="cancelBtn"><i class="fa-solid fa-times"></i><span>Cancel</span></button>`;
      break;
    case "locked":
      // Show STATUS button instead of checkout when locked by another user
      buttons += `<button class="${btnBase} file-btn-status js-status-btn" data-tooltip-key="statusBtn"><i class="fa-solid fa-info-circle"></i><span>View Status</span></button>`;
      if (isAdmin) {
        buttons += `<button class="${btnBase} file-btn-override js-override-btn" data-tooltip-key="overrideBtn"><i class="fa-solid fa-unlock"></i><span>Override Lock</span></button>`;
      }
      break;
  }

  buttons += downloadBtn;
  buttons += `<button class="${btnBase} file-btn-history js-history-btn" data-tooltip-key="historyBtn"><i class="fa-solid fa-history"></i><span>History</span></button>`;
  if (isAdmin) {
    buttons += `<button class="${btnBase} file-btn-delete js-delete-btn" data-tooltip-key="deleteBtn"><i class="fa-solid fa-trash-can"></i><span>Delete</span></button>`;
  }
  return buttons;
}

export function createFileCard(file, currentUser, isAdmin) {
  const template = document.getElementById("file-card-template");
  const card = template.content.cloneNode(true).firstElementChild;

  // --- Populate Card Data (Your complete logic) ---
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

        // Show checkout message if available
        let lockInfoHtml = `<i class="fa-solid fa-lock text-red-500"></i><span>Locked by: <strong>${file.locked_by}</strong> at ${formatDate(file.locked_at)}`;
        if (file.checkout_message) {
          lockInfoHtml += ` - <em>"${file.checkout_message}"</em>`;
        }
        lockInfoHtml += `</span>`;
        lockInfoEl.innerHTML = lockInfoHtml;
        break;
      case "checked_out_by_user":
        statusEl.classList.add(
          "bg-blue-100",
          "text-blue-900",
          "dark:bg-blue-900",
          "dark:text-blue-200"
        );
        statusEl.textContent = "Checked out by you";

        // Show your checkout message
        let yourLockInfoHtml = `<i class="fa-solid fa-lock-open text-blue-500"></i><span>You checked this out at ${formatDate(file.locked_at)}`;
        if (file.checkout_message) {
          yourLockInfoHtml += ` - <em>"${file.checkout_message}"</em>`;
        }
        yourLockInfoHtml += `</span>`;
        lockInfoEl.innerHTML = yourLockInfoHtml;
        break;
    }
  }

  // --- Add Buttons and Event Listeners ---
  const buttonsContainer = card.querySelector('[data-field="action-buttons"]');
  buttonsContainer.innerHTML = getActionButtons(file, currentUser, isAdmin);

  // Tooltips will be attached after rendering via refreshTooltips()

  card.addEventListener("click", async (e) => {
    const button = e.target.closest("button, a");
    if (!button) return;

    const refreshFiles = async () => {
      try {
        const filesData = await getFiles();
        setState({ groupedFiles: filesData });
      } catch (error) {
        alert(`Failed to refresh file list: ${error.message}`);
      }
    };

    let confirmed;

    e.preventDefault(); // Prevent default action for all buttons initially

    switch (true) {
      case button.classList.contains("js-checkout-btn"):
        // Show checkout modal with required message
        showCheckoutDialog(file);
        break;
      case button.classList.contains("js-status-btn"):
        // Show status modal with checkout message
        showStatusDialog(file);
        break;
      case button.classList.contains("js-checkin-btn"):
        showCheckinDialog(file);
        break;
      case button.classList.contains("js-history-btn"):
        showHistoryDialog(file.filename);
        break;
      case button.classList.contains("js-cancel-checkout-btn"):
        confirmed = await showConfirmDialog(
          "Cancel Checkout",
          `Are you sure? Any local changes to <strong>${file.filename}</strong> will be lost.`
        );
        if (confirmed) {
          try {
            showNotification("Canceling checkout...", "info");
            await cancelCheckout(file.filename, currentUser);
            showNotification(`Checkout canceled for ${file.filename}`, "success");
            await refreshFiles();
          } catch (error) {
            showNotification(`Failed to cancel checkout: ${error.message}`, "error");
          }
        }
        break;
      case button.classList.contains("js-delete-btn"):
        confirmed = await showConfirmDialog(
          "Delete File",
          `Are you sure you want to permanently delete <strong>${file.filename}</strong>?`
        );
        if (confirmed) {
          try {
            showNotification(`Deleting ${file.filename}...`, "info");
            await deleteFile(file.filename, currentUser);
            showNotification(`${file.filename} deleted successfully`, "success");
            await refreshFiles();
          } catch (error) {
            showNotification(`Failed to delete file: ${error.message}`, "error");
          }
        }
        break;
      case button.classList.contains("js-override-btn"):
        confirmed = await showConfirmDialog(
          "Override Lock",
          `Are you sure you want to forcibly unlock <strong>${file.filename}</strong>?`
        );
        if (confirmed) {
          try {
            showNotification(`Overriding lock on ${file.filename}...`, "warning");
            await overrideLock(file.filename, currentUser);
            showNotification(`Lock overridden for ${file.filename}`, "success");
            await refreshFiles();
          } catch (error) {
            showNotification(`Failed to override lock: ${error.message}`, "error");
          }
        }
        break;
      case button.classList.contains("js-download-btn"):
        // Show view-only modal if not checked out
        if (file.status !== "checked_out_by_user") {
          const proceed = await showViewOnlyDialog(file.filename);
          if (!proceed) break;
        }
        // Download file
        showNotification(`Downloading ${file.filename}...`, "info");
        window.location.href = `/files/${file.filename}/download`;
        break;
      case button.classList.contains("js-view-master-btn"):
        // Navigate to the master file that this link points to
        const masterFile = button.dataset.masterFile;
        if (masterFile) {
          // Find the master file card
          const masterCard = document.querySelector(`[data-file-id="${masterFile}"]`);

          if (masterCard) {
            showNotification(`Navigating to ${masterFile}`, "info");
            // Open ONLY the parent folders of this specific card
            let parent = masterCard.closest('details');
            while (parent) {
              parent.open = true;
              parent = parent.parentElement.closest('details');
            }

            // Small delay for DOM update
            setTimeout(() => {
              // Scroll to and highlight the master file card
              masterCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
              // Highlight with animation
              masterCard.style.boxShadow = '0 0 20px 5px rgba(245, 158, 11, 0.5)';
              setTimeout(() => {
                masterCard.style.boxShadow = '';
              }, 2000);
            }, 100);
          } else {
            showNotification(`Master file "${masterFile}" not found`, "error");
          }
        }
        break;
      case button.tagName === "A" && button.href.includes("/download"):
        // This is a direct download link for a file you have checked out. Let it proceed.
        window.location.href = button.href;
        break;
    }
  });

  return card;
}
