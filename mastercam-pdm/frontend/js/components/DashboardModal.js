// frontend/js/components/DashboardModal.js

import { Modal } from "./Modal.js";
import { getDashboardStats, getActivityFeed } from "../api/service.js";
import { formatDate, formatDuration } from "../utils/helpers.js";

export async function showDashboardDialog() {
  const template = document.getElementById("template-dashboard-modal");
  const content = template.content.cloneNode(true);
  const modal = new Modal(content);
  modal.show();

  const dashboardContentEl =
    modal.modalElement.querySelector("#dashboardContent");
  dashboardContentEl.innerHTML = `<div class="flex justify-center items-center w-full h-full"><i class="fa-solid fa-spinner fa-spin text-4xl text-accent"></i></div>`;

  try {
    const statsData = await getDashboardStats();
    // We can fetch activity feed data here too if needed

    const checkoutsHtml = renderActiveCheckouts(statsData.active_checkouts);

    // In a full implementation, we'd render the activity feed as well
    dashboardContentEl.innerHTML = `
      <div class="md:w-1/2 flex flex-col">${checkoutsHtml}</div>
      <div class="md:w-1/2 flex flex-col mt-6 md:mt-0 md:border-l md:pl-6 border-gray-200 dark:border-gray-700">
         <h4 class="text-lg font-semibold mb-4">Recent Activity</h4>
         <p class="text-gray-500 text-sm">Activity feed rendering is pending refactor.</p>
      </div>
    `;
  } catch (error) {
    dashboardContentEl.innerHTML = `<p class="text-red-500">Error loading dashboard: ${error.message}</p>`;
  }
}

function renderActiveCheckouts(checkouts) {
  if (checkouts.length === 0) {
    return `<h4 class="text-lg font-semibold mb-4">Active Checkouts</h4><p>No files are currently checked out.</p>`;
  }

  const rows = checkouts
    .map(
      (item) => `
    <tr>
      <td class="px-4 py-3 text-sm font-medium">${item.filename}</td>
      <td class="px-4 py-3 text-sm">${item.locked_by}</td>
      <td class="px-4 py-3 text-sm">${formatDuration(
        item.duration_seconds
      )}</td>
    </tr>
  `
    )
    .join("");

  return `
    <h4 class="text-lg font-semibold mb-4 flex-shrink-0">Active Checkouts</h4>
    <div class="overflow-x-auto flex-grow">
      <table class="min-w-full">
        <thead class="bg-gray-50 dark:bg-gray-700">
          <tr>
            <th class="px-4 py-2 text-left text-xs font-medium uppercase">File</th>
            <th class="px-4 py-2 text-left text-xs font-medium uppercase">User</th>
            <th class="px-4 py-2 text-left text-xs font-medium uppercase">Duration</th>
          </tr>
        </thead>
        <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">${rows}</tbody>
      </table>
    </div>
  `;
}
