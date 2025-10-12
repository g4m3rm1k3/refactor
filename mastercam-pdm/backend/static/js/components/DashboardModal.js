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
    // Fetch both stats and activity feed
    const [statsData, activityData] = await Promise.all([
      getDashboardStats(),
      getActivityFeed(20, 0) // Get last 20 activities
    ]);

    const checkoutsHtml = renderActiveCheckouts(statsData.active_checkouts);
    const activityHtml = renderActivityFeed(activityData.activities);

    dashboardContentEl.innerHTML = `
      <div class="md:w-1/2 flex flex-col">${checkoutsHtml}</div>
      <div class="md:w-1/2 flex flex-col mt-6 md:mt-0 md:border-l md:pl-6 border-gray-200 dark:border-gray-700">${activityHtml}</div>
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

function renderActivityFeed(activities) {
  if (!activities || activities.length === 0) {
    return `
      <h4 class="text-lg font-semibold mb-4">Recent Activity</h4>
      <p class="text-gray-500 text-sm">No recent activity.</p>
    `;
  }

  // Map event types to icons and colors
  const eventIcons = {
    checkin: { icon: "fa-check-circle", color: "text-green-500" },
    checkout: { icon: "fa-lock", color: "text-amber-500" },
    cancel_checkout: { icon: "fa-unlock", color: "text-blue-500" },
    delete: { icon: "fa-trash", color: "text-red-500" },
    commit: { icon: "fa-code-commit", color: "text-gray-500" },
  };

  const items = activities
    .map((activity) => {
      const eventConfig = eventIcons[activity.event_type] || eventIcons.commit;
      const timeAgo = formatDate(activity.timestamp);

      return `
        <div class="flex items-start space-x-3 p-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 rounded-lg transition-colors">
          <i class="fa-solid ${eventConfig.icon} ${eventConfig.color} text-lg mt-1"></i>
          <div class="flex-grow min-w-0">
            <p class="text-sm font-medium truncate">${activity.filename}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              ${activity.user} • ${timeAgo}
            </p>
            ${activity.revision ? `<span class="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded">Rev ${activity.revision}</span>` : ""}
          </div>
        </div>
      `;
    })
    .join("");

  return `
    <h4 class="text-lg font-semibold mb-4 flex-shrink-0">Recent Activity</h4>
    <div class="flex-grow overflow-y-auto space-y-1">
      ${items}
    </div>
  `;
}
