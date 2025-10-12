// ViewOnlyModal.js - Confirmation modal for view-only downloads

import { Modal } from "./Modal.js";

export function showViewOnlyDialog(filename) {
  return new Promise((resolve) => {
    const content = `
      <div class="panel-bg rounded-xl shadow-lg p-6 w-full max-w-lg">
        <div>
          <h3 class="text-xl font-semibold mb-4">
            <i class="fa-solid fa-eye mr-2 text-amber-500"></i>View-Only Download
          </h3>

          <div class="mb-6">
            <div class="bg-amber-50 dark:bg-amber-900/20 border-l-4 border-amber-500 p-4 mb-4">
              <p class="font-semibold text-amber-800 dark:text-amber-300">
                <i class="fa-solid fa-exclamation-triangle mr-2"></i>Important Notice
              </p>
              <p class="text-sm text-amber-700 dark:text-amber-400 mt-2">
                You are downloading this file for <strong>viewing purposes only</strong>.
              </p>
            </div>

            <div class="space-y-3 text-sm">
              <p class="text-gray-700 dark:text-gray-300">
                <strong>File:</strong> ${filename}
              </p>

              <div class="bg-gray-100 dark:bg-gray-700 p-3 rounded-lg">
                <p class="font-semibold mb-2">What this means:</p>
                <ul class="list-disc list-inside space-y-1 text-gray-700 dark:text-gray-300">
                  <li>You can open and view the file</li>
                  <li>You <strong>cannot</strong> check it back in</li>
                  <li>Any changes you make will <strong>not</strong> be saved</li>
                  <li>To edit, you must checkout the file first</li>
                </ul>
              </div>

              <p class="text-xs text-gray-500 dark:text-gray-400 italic">
                This download is for reference, inspection, or creating derivative works only.
              </p>
            </div>
          </div>

          <div class="flex justify-end space-x-3">
            <button class="btn btn-secondary" data-action="cancel">
              Cancel
            </button>
            <button class="btn btn-primary" data-action="confirm">
              <i class="fa-solid fa-download mr-2"></i>I Understand, Download
            </button>
          </div>
        </div>
      </div>
    `;

    // Create DOM element from HTML string
    const contentElement = document.createRange().createContextualFragment(content).firstElementChild;

    const modal = new Modal(contentElement);
    modal.show();

    // Handle button clicks - attach after modal is shown
    contentElement.querySelector('[data-action="confirm"]')?.addEventListener("click", () => {
      modal.close();
      resolve(true);
    });

    contentElement.querySelector('[data-action="cancel"]')?.addEventListener("click", () => {
      modal.close();
      resolve(false);
    });
  });
}
