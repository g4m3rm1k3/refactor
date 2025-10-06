// backend/static/js/components/ConfirmModal.js
import { Modal } from "./Modal.js";

/**
 * Shows a confirmation dialog and returns a Promise that resolves to true or false.
 * @param {string} title - The title of the modal.
 * @param {string} message - The confirmation message (can be HTML).
 * @returns {Promise<boolean>} - True if confirmed, false if canceled.
 */
export function showConfirmDialog(title, message) {
  return new Promise((resolve) => {
    const content = document.createElement("div");
    content.className = "panel-bg rounded-xl shadow-lg p-6 w-full max-w-md";
    content.innerHTML = `
      <h3 class="text-xl font-semibold mb-4">${title}</h3>
      <p class="text-gray-700 dark:text-gray-300 mb-6">${message}</p>
      <div class="flex justify-end space-x-3">
        <button id="confirm-cancel" class="btn btn-secondary">Cancel</button>
        <button id="confirm-ok" class="btn bg-red-600 hover:bg-red-700 text-white">Confirm</button>
      </div>
    `;

    const modal = new Modal(content, { closable: true });
    modal.show();

    const confirmBtn = modal.modalElement.querySelector("#confirm-ok");
    const cancelBtn = modal.modalElement.querySelector("#confirm-cancel");

    const handleResolve = (value) => {
      modal.close();
      resolve(value);
    };

    confirmBtn.addEventListener("click", () => handleResolve(true));
    cancelBtn.addEventListener("click", () => handleResolve(false));
  });
}
