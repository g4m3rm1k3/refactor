// CheckoutModal.js - Modal for checking out files with required message

import { Modal } from "./Modal.js";
import { showNotification } from "../utils/helpers.js";
import { setState, getState } from "../state/store.js";
import { getFiles } from "../api/service.js";

let currentFile = null;
let currentModal = null;

export function showCheckoutDialog(file) {
  currentFile = file;

  const content = `
    <div class="panel-bg rounded-xl shadow-lg p-6 w-full max-w-lg">
      <form id="checkoutForm">
        <h3 class="text-xl font-semibold mb-4">
          <i class="fa-solid fa-download mr-2"></i>Checkout File
        </h3>

        <div class="mb-4">
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
            You are about to checkout: <strong>${file.filename}</strong>
          </p>
          <p class="text-xs text-amber-600 dark:text-amber-400 mb-4">
            <i class="fa-solid fa-info-circle mr-1"></i>
            Other users will see why you have this file checked out.
          </p>
        </div>

        <div class="mb-4">
          <label for="checkoutMessage" class="block text-sm font-medium mb-1">
            Why are you checking out this file? <span class="text-red-500">*</span>
          </label>
          <textarea
            id="checkoutMessage"
            name="message"
            rows="3"
            required
            placeholder="e.g., Updating dimensions, Fixing hole pattern, Adding new features..."
            class="input-field w-full"
          ></textarea>
          <p class="text-xs text-gray-500 mt-1">
            Be specific so others know what you're working on.
          </p>
        </div>

        <div class="flex justify-end space-x-3">
          <button type="button" class="btn btn-secondary" data-action="close">
            Cancel
          </button>
          <button type="submit" class="btn btn-primary">
            <i class="fa-solid fa-lock mr-2"></i>Checkout File
          </button>
        </div>
      </form>
    </div>
  `;

  const contentElement = document.createRange().createContextualFragment(content).firstElementChild;
  currentModal = new Modal(contentElement);
  currentModal.show();

  const form = contentElement.querySelector("#checkoutForm");
  if (form) {
    form.addEventListener("submit", handleCheckoutSubmit);
  }
}

async function handleCheckoutSubmit(event) {
  event.preventDefault();
  const form = event.target;

  // Prevent double submission
  const submitBtn = form.querySelector('button[type="submit"]');
  if (submitBtn.disabled) return;
  submitBtn.disabled = true;

  const message = form.querySelector("#checkoutMessage").value.trim();

  if (!message) {
    showNotification("Please enter a reason for checkout", "error");
    submitBtn.disabled = false;
    return;
  }

  const state = getState();
  const user = state.currentUser;

  try {
    const response = await fetch(`/files/${currentFile.filename}/checkout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ user, message }),
    });

    if (!response.ok) {
      const error = await response.json();
      submitBtn.disabled = false;
      throw new Error(error.detail || "Checkout failed");
    }

    showNotification(`Checked out ${currentFile.filename}`, "success");

    // Close modal
    if (currentModal) {
      currentModal.close();
      currentModal = null;
    }

    // Refresh file list
    const filesData = await getFiles();
    setState({ groupedFiles: filesData });
  } catch (error) {
    console.error("Checkout error:", error);
    showNotification(`Checkout failed: ${error.message}`, "error");
    submitBtn.disabled = false;
  }
}
