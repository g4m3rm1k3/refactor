// backend/static/js/components/HistoryModal.js
import { Modal } from "./Modal.js";
import { getFileHistoryRevisions } from "../api/service.js";

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
        <label class="text-sm font-medium">Filter by revision range:</label>
        <input type="text" id="startRevision" placeholder="e.g., 1.0" class="input-field py-1 px-2 text-sm w-24" />
        <span class="text-sm">to</span>
        <input type="text" id="endRevision" placeholder="e.g., 20.5" class="input-field py-1 px-2 text-sm w-24" />
        <button id="applyFilter" class="btn btn-primary text-sm py-1 px-3">Apply</button>
        <button id="clearFilter" class="btn btn-secondary text-sm py-1 px-3">Clear</button>
      </div>
      <div id="revisionSummary" class="text-sm text-gray-600 dark:text-gray-400"></div>
    </div>
    <div id="historyContainer" class="overflow-y-auto p-6 space-y-4"><i class="fa-solid fa-spinner fa-spin"></i> Loading history...</div>`;

  const modal = new Modal(content);
  modal.show();

  let allHistory = [];
  let fullRevisionRange = "";

  try {
    const result = await getFileHistoryRevisions(filename);
    allHistory = result.revisions || [];
    fullRevisionRange = result.revision_range || "";

    // Update the summary
    const summaryEl = modal.modalElement.querySelector("#revisionSummary");
    if (summaryEl && result.total_revisions) {
      summaryEl.textContent = `Total Revisions: ${result.total_revisions} | Full Range: ${fullRevisionRange}`;
    }

    renderHistory(allHistory, modal, filename);

    // Wire up filter buttons
    const applyFilterBtn = modal.modalElement.querySelector("#applyFilter");
    const clearFilterBtn = modal.modalElement.querySelector("#clearFilter");
    const startRevInput = modal.modalElement.querySelector("#startRevision");
    const endRevInput = modal.modalElement.querySelector("#endRevision");

    applyFilterBtn.addEventListener("click", async () => {
      const startRev = startRevInput.value.trim() || null;
      const endRev = endRevInput.value.trim() || null;

      try {
        const historyContainer = modal.modalElement.querySelector("#historyContainer");
        historyContainer.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Loading filtered history...';

        const result = await getFileHistoryRevisions(filename, startRev, endRev);
        const filtered = result.revisions || [];

        // Update summary to show filtered range
        if (summaryEl) {
          const filteredRange = result.revision_range || "";
          summaryEl.textContent = `Total Revisions: ${result.total_revisions} | Showing: ${filteredRange} ${result.filtered ? '(filtered)' : ''}`;
        }

        renderHistory(filtered, modal, filename);
      } catch (error) {
        const historyContainer = modal.modalElement.querySelector("#historyContainer");
        historyContainer.innerHTML = `<p class="text-red-500">Error filtering history: ${error.message}</p>`;
      }
    });

    clearFilterBtn.addEventListener("click", () => {
      startRevInput.value = "";
      endRevInput.value = "";

      // Reload full history
      if (summaryEl && result.total_revisions) {
        summaryEl.textContent = `Total Revisions: ${result.total_revisions} | Full Range: ${fullRevisionRange}`;
      }
      renderHistory(allHistory, modal, filename);
    });

  } catch (error) {
    modal.modalElement.querySelector(
      "#historyContainer"
    ).innerHTML = `<p class="text-red-500">Error loading history: ${error.message}</p>`;
  }
}

function renderHistory(history, modal, filename) {
  const historyContainer = modal.modalElement.querySelector("#historyContainer");

  if (history.length === 0) {
    historyContainer.innerHTML = "<p class='text-gray-500'>No revisions found in this range.</p>";
    return;
  }

  historyContainer.innerHTML = history
    .map(
      (commit) => {
        const revisionDisplay = commit.revision || commit.commit_hash.substring(0, 8);
        const authorDisplay = commit.author || 'Unknown';
        const messageDisplay = commit.message || 'No commit message';
        const dateDisplay = commit.timestamp || commit.date;

        return `
    <div class="p-4 bg-gray-100 dark:bg-gray-700 rounded-lg">
      <div class="flex justify-between items-start">
        <div class="flex-grow">
          <div class="flex items-center space-x-3 mb-2">
            <p class="text-base font-bold text-accent">Rev ${revisionDisplay}</p>
            <p class="text-xs text-gray-500">by ${authorDisplay}</p>
            ${dateDisplay ? `<p class="text-xs text-gray-400">${formatSimpleDate(dateDisplay)}</p>` : ''}
          </div>
          <p class="text-sm bg-white dark:bg-gray-800 p-2 rounded border border-gray-200 dark:border-gray-600">
            <i class="fa-solid fa-comment-dots mr-1"></i>${messageDisplay}
          </p>
          ${commit.commit_hash ? `<p class="text-xs text-gray-400 mt-1 font-mono">Commit: ${commit.commit_hash.substring(0, 8)}</p>` : ''}
        </div>
        <a href="/files/${encodeURIComponent(filename)}/versions/${commit.commit_hash}"
           class="btn btn-secondary text-xs ml-3 flex-shrink-0">
          <i class="fa-solid fa-download mr-1"></i>Download
        </a>
      </div>
    </div>
  `;
      }
    )
    .join("");
}

/**
 * Format date in simple readable format (only shown as secondary info)
 */
function formatSimpleDate(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;

  // Fall back to simple date format
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}
