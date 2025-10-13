// backend/static/js/components/HistoryModal.js
import { Modal } from "./Modal.js";
import { getFileHistory } from "../api/service.js";
import { formatDate } from "../utils/helpers.js";

export async function showHistoryDialog(filename) {
  const content = document.createElement("div");
  content.className =
    "panel-bg rounded-xl shadow-lg p-6 w-full max-w-2xl flex flex-col max-h-[90vh]";
  content.innerHTML = `
    <div class="flex-shrink-0 flex justify-between items-center pb-4 border-b">
      <h3 class="text-xl font-semibold">Version History - ${filename}</h3>
      <button data-action="close"><i class="fa-solid fa-xmark text-2xl"></i></button>
    </div>
    <div class="flex-shrink-0 p-4 border-b space-y-3">
      <div class="flex items-center space-x-4">
        <label class="text-sm font-medium">Filter by date range:</label>
        <input type="date" id="startDate" class="input-field py-1 px-2 text-sm" />
        <span class="text-sm">to</span>
        <input type="date" id="endDate" class="input-field py-1 px-2 text-sm" />
        <button id="applyFilter" class="btn btn-primary text-sm py-1 px-3">Apply</button>
        <button id="clearFilter" class="btn btn-secondary text-sm py-1 px-3">Clear</button>
      </div>
    </div>
    <div id="historyContainer" class="overflow-y-auto p-6 space-y-4"><i class="fa-solid fa-spinner fa-spin"></i> Loading history...</div>`;

  const modal = new Modal(content);
  modal.show();

  let allHistory = [];

  try {
    const result = await getFileHistory(filename);
    allHistory = result.history;

    renderHistory(allHistory, modal);

    // Wire up filter buttons
    const applyFilterBtn = modal.modalElement.querySelector("#applyFilter");
    const clearFilterBtn = modal.modalElement.querySelector("#clearFilter");
    const startDateInput = modal.modalElement.querySelector("#startDate");
    const endDateInput = modal.modalElement.querySelector("#endDate");

    applyFilterBtn.addEventListener("click", () => {
      const startDate = startDateInput.value ? new Date(startDateInput.value) : null;
      const endDate = endDateInput.value ? new Date(endDateInput.value + "T23:59:59") : null;

      const filtered = allHistory.filter((commit) => {
        const commitDate = new Date(commit.date);
        if (startDate && commitDate < startDate) return false;
        if (endDate && commitDate > endDate) return false;
        return true;
      });

      renderHistory(filtered, modal);
    });

    clearFilterBtn.addEventListener("click", () => {
      startDateInput.value = "";
      endDateInput.value = "";
      renderHistory(allHistory, modal);
    });

  } catch (error) {
    modal.modalElement.querySelector(
      "#historyContainer"
    ).innerHTML = `<p class="text-red-500">Error loading history: ${error.message}</p>`;
  }
}

function renderHistory(history, modal) {
  const historyContainer = modal.modalElement.querySelector("#historyContainer");

  if (history.length === 0) {
    historyContainer.innerHTML = "<p class='text-gray-500'>No commits found in this range.</p>";
    return;
  }

  historyContainer.innerHTML = history
    .map(
      (commit) => `
    <div class="p-4 bg-gray-100 dark:bg-gray-700 rounded-lg">
      <div class="flex justify-between items-start">
        <div class="flex-grow">
          <div class="flex items-center space-x-3 mb-2">
            <p class="text-sm font-mono text-accent">${commit.commit_hash.substring(0, 8)}</p>
            <p class="text-xs text-gray-500">by ${commit.author_name}</p>
            <p class="text-xs text-gray-500">${formatDate(commit.date)}</p>
          </div>
          <p class="text-sm bg-white dark:bg-gray-800 p-2 rounded border border-gray-200 dark:border-gray-600">
            <i class="fa-solid fa-comment-dots mr-1"></i>${commit.message || 'No commit message'}
          </p>
        </div>
        <a href="/files/${modal.modalElement.querySelector('h3').textContent.split(' - ')[1]}/versions/${
        commit.commit_hash
      }" class="btn btn-secondary text-xs ml-3">
          <i class="fa-solid fa-download mr-1"></i>Download
        </a>
      </div>
    </div>
  `
    )
    .join("");
}
