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
    <div class="overflow-y-auto p-6 space-y-4"><i class="fa-solid fa-spinner fa-spin"></i> Loading history...</div>`;

  const modal = new Modal(content);
  modal.show();

  try {
    const result = await getFileHistory(filename);
    const historyContainer =
      modal.modalElement.querySelector(".overflow-y-auto");

    if (result.history.length === 0) {
      historyContainer.innerHTML = "<p>No version history found.</p>";
      return;
    }

    historyContainer.innerHTML = result.history
      .map(
        (commit) => `
      <div class="p-4 bg-gray-100 dark:bg-gray-700 rounded-lg">
        <div class="flex justify-between items-start">
          <div>
            <p class="text-sm font-mono text-accent">${commit.commit_hash.substring(
              0,
              8
            )}</p>
            <p class="text-sm">${commit.message}</p>
            <p class="text-xs text-gray-500 mt-1">by ${
              commit.author_name
            } on ${formatDate(commit.date)}</p>
          </div>
          <a href="/files/${filename}/versions/${
          commit.commit_hash
        }" class="btn btn-secondary text-xs">Download</a>
        </div>
      </div>
    `
      )
      .join("");
  } catch (error) {
    modal.modalElement.querySelector(
      ".overflow-y-auto"
    ).innerHTML = `<p class="text-red-500">Error loading history: ${error.message}</p>`;
  }
}
