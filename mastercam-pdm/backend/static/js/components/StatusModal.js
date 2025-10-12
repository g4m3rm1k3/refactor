// StatusModal.js - Display checkout status and message for locked files

import { Modal } from "./Modal.js";
import { formatDate } from "../utils/helpers.js";

export function showStatusDialog(file) {
  const content = `
    <div class="panel-bg rounded-xl shadow-lg p-6 w-full max-w-lg">
      <div>
        <h3 class="text-xl font-semibold mb-4">
          <i class="fa-solid fa-info-circle mr-2 text-blue-500"></i>File Status
        </h3>

        <div class="mb-6">
          <div class="bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 p-4 mb-4">
            <p class="font-semibold text-blue-800 dark:text-blue-300">
              ${file.filename}
            </p>
            <p class="text-sm text-blue-700 dark:text-blue-400 mt-1">
              ${file.description || 'No description'}
            </p>
          </div>

          <div class="space-y-3">
            <div>
              <p class="text-sm font-semibold text-gray-700 dark:text-gray-300">Status:</p>
              <p class="text-sm">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                  <i class="fa-solid fa-lock mr-1"></i>
                  Checked out by ${file.locked_by}
                </span>
              </p>
            </div>

            <div>
              <p class="text-sm font-semibold text-gray-700 dark:text-gray-300">Checked out:</p>
              <p class="text-sm text-gray-600 dark:text-gray-400">
                ${formatDate(file.locked_at)}
              </p>
            </div>

            ${file.checkout_message ? `
              <div>
                <p class="text-sm font-semibold text-gray-700 dark:text-gray-300">Reason:</p>
                <div class="mt-1 p-3 bg-gray-100 dark:bg-gray-700 rounded-lg">
                  <p class="text-sm italic text-gray-800 dark:text-gray-200">
                    "${file.checkout_message}"
                  </p>
                </div>
              </div>
            ` : `
              <div>
                <p class="text-sm text-gray-500 italic">No reason provided</p>
              </div>
            `}
          </div>
        </div>

        <div class="flex justify-end">
          <button class="btn btn-secondary" data-action="close">
            Close
          </button>
        </div>
      </div>
    </div>
  `;

  const contentElement = document.createRange().createContextualFragment(content).firstElementChild;
  const modal = new Modal(contentElement);
  modal.show();
}
