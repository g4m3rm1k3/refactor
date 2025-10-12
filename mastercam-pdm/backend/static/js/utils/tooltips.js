// Lazy-loaded tooltip system with Intersection Observer

let tooltipsEnabled = false; // Always start disabled, no persistence
const tooltipCache = new Map();
let tooltipObserver = null;

// Tooltip content definitions
const tooltips = {
  // Main UI
  newFileBtn: { title: "New File", text: "Upload a new file or create a link to an existing file" },
  dashboardBtn: { title: "Dashboard", text: "View activity feed, statistics, and recent changes" },
  configBtn: { title: "Settings", text: "Configure GitLab connection, manage users, and system settings" },
  darkModeBtn: { title: "Dark Mode", text: "Toggle between light and dark themes" },
  tooltipBtn: { title: "Help Tooltips", text: "Toggle help tooltips on/off for guided assistance" },
  collapseAllBtn: { title: "Collapse All", text: "Collapse all file groups to save screen space" },
  adminModeToggle: { title: "Admin Mode", text: "Enable admin features like file override and deletion" },
  searchInput: { title: "Search", text: "Search by filename or description. Results update as you type." },

  // File actions
  checkoutBtn: { title: "Checkout", text: "Lock this file for editing. You'll be asked to provide a reason that others can see." },
  checkinBtn: { title: "Check In", text: "Upload your changes and release the lock so others can edit" },
  cancelBtn: { title: "Cancel Checkout", text: "Release the lock without saving changes. Your local edits will be discarded." },
  downloadBtn: { title: "Download", text: "Download file. If not checked out, you can only view it (no check-in allowed)." },
  historyBtn: { title: "History", text: "View version history and previous revisions" },
  deleteBtn: { title: "Delete", text: "Permanently remove this file from the repository (Admin only)" },
  deleteLinkBtn: { title: "Remove Link", text: "Remove this link file (Admin only). The master file will not be affected." },
  overrideBtn: { title: "Override Lock", text: "Forcibly unlock this file (Admin only). Use with caution!" },
  statusBtn: { title: "View Status", text: "See who has this file checked out and why they're working on it" },
  viewMasterBtn: { title: "View Master", text: "Jump to and highlight the master file this link references" },

  // Form fields
  gitlabUrl: { title: "GitLab URL", text: "Full URL to your GitLab project (e.g., https://gitlab.com/group/project)" },
  projectId: { title: "Project ID", text: "Numeric GitLab project ID found in project settings" },
  username: { title: "Username", text: "Your GitLab username" },
  token: { title: "Access Token", text: "Personal Access Token from GitLab with 'api' and 'read_repository' scopes" },

  // Dashboard
  activityFeed: { title: "Recent Activity", text: "Shows latest commits, checkouts, and file operations" },
  activeCheckouts: { title: "Active Checkouts", text: "Files currently locked by users" },
};

function initTooltipSystem() {
  // Create stylesheet
  if (!document.getElementById("tooltip-styles")) {
    const style = document.createElement("style");
    style.id = "tooltip-styles";
    style.textContent = `
      .tooltip {
        position: absolute;
        background: linear-gradient(135deg, #1f2937, #374151);
        color: white;
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 500;
        line-height: 1.4;
        z-index: 9999;
        opacity: 0;
        visibility: hidden;
        transform: scale(0.8);
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
        max-width: 280px;
        word-wrap: break-word;
        pointer-events: none;
      }

      .tooltip.show {
        opacity: 1;
        visibility: visible;
        transform: scale(1);
      }

      .tooltip .tooltip-title {
        font-weight: 600;
        font-size: 14px;
        margin-bottom: 4px;
        color: #fbbf24;
      }

      .tooltip-enabled {
        position: relative;
      }

      input.tooltip-enabled::after,
      textarea.tooltip-enabled::after,
      select.tooltip-enabled::after {
        content: '?';
        position: absolute;
        top: 4px;
        right: 4px;
        background: #fbbf24;
        color: #1f2937;
        border-radius: 50%;
        width: 16px;
        height: 16px;
        font-size: 10px;
        font-weight: bold;
        display: flex;
        align-items: center;
        justify-content: center;
        pointer-events: none;
        opacity: 0.8;
      }
    `;
    document.head.appendChild(style);
  }

  // Setup Intersection Observer for performance
  if (!tooltipObserver && tooltipsEnabled) {
    tooltipObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && entry.target.dataset.tooltipKey) {
            attachTooltipHandlers(entry.target);
          }
        });
      },
      { rootMargin: "50px" } // Load tooltips slightly before element is visible
    );
  }

  updateTooltipVisibility();
}

export function toggleTooltips() {
  tooltipsEnabled = !tooltipsEnabled;
  // NO localStorage - don't persist state

  const toggleBtn = document.getElementById("tooltipBtn");
  if (toggleBtn) {
    if (tooltipsEnabled) {
      toggleBtn.classList.remove("btn-secondary");
      toggleBtn.classList.add("btn-primary");
    } else {
      toggleBtn.classList.add("btn-secondary");
      toggleBtn.classList.remove("btn-primary");
    }
  }

  updateTooltipVisibility();

  // When enabling tooltips, ensure all dynamic elements have handlers attached
  if (tooltipsEnabled) {
    refreshTooltips();
  }

  // Show notification
  const event = new CustomEvent("show-notification", {
    detail: {
      message: tooltipsEnabled ? "Help tooltips enabled" : "Help tooltips disabled",
      type: tooltipsEnabled ? "success" : "info"
    }
  });
  window.dispatchEvent(event);
}

function attachTooltipHandlers(element) {
  if (element.dataset.tooltipAttached === "true") return;

  const tooltipKey = element.dataset.tooltipKey || element.id;
  if (!tooltipKey || !tooltips[tooltipKey]) return;

  element.dataset.tooltipKey = tooltipKey;
  element.addEventListener("mouseenter", showTooltip);
  element.addEventListener("mouseleave", hideTooltip);
  element.classList.add("tooltip-enabled");
  element.dataset.tooltipAttached = "true";
}

function updateTooltipVisibility() {
  // Disconnect observer and remove existing tooltips
  if (tooltipObserver) {
    tooltipObserver.disconnect();
  }

  document.querySelectorAll(".tooltip-enabled").forEach((el) => {
    el.classList.remove("tooltip-enabled");
    el.removeAttribute("data-tooltip-attached");
  });

  if (!tooltipsEnabled) return;

  // Attach tooltips to elements
  Object.keys(tooltips).forEach((elementId) => {
    const element = document.getElementById(elementId);
    if (element) {
      element.dataset.tooltipKey = elementId;
      if (tooltipObserver) {
        tooltipObserver.observe(element);
      } else {
        attachTooltipHandlers(element);
      }
    }
  });
}

function showTooltip(event) {
  const element = event.currentTarget;
  const tooltipKey = element.dataset.tooltipKey || element.classList[0]; // Fallback to class name
  const tooltipData = tooltips[tooltipKey];

  if (!tooltipData || !tooltipsEnabled) return;

  // IMPORTANT: Hide all other tooltips first to prevent stacking
  hideAllTooltips();

  // Check cache
  let tooltip = tooltipCache.get(tooltipKey);

  if (!tooltip) {
    // Create new tooltip
    tooltip = document.createElement("div");
    tooltip.className = "tooltip";
    tooltip.innerHTML = `
      ${tooltipData.title ? `<div class="tooltip-title">${tooltipData.title}</div>` : ''}
      <div>${tooltipData.text}</div>
    `;
    document.body.appendChild(tooltip);
    tooltipCache.set(tooltipKey, tooltip);
  }

  // Position tooltip
  const rect = element.getBoundingClientRect();
  const tooltipRect = tooltip.getBoundingClientRect();

  let top = rect.bottom + 8;
  let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);

  // Keep tooltip on screen
  if (left < 8) left = 8;
  if (left + tooltipRect.width > window.innerWidth - 8) {
    left = window.innerWidth - tooltipRect.width - 8;
  }
  if (top + tooltipRect.height > window.innerHeight - 8) {
    top = rect.top - tooltipRect.height - 8;
  }

  tooltip.style.top = `${top}px`;
  tooltip.style.left = `${left}px`;

  // Show with slight delay
  setTimeout(() => tooltip.classList.add("show"), 10);
}

function hideAllTooltips() {
  tooltipCache.forEach((tooltip) => {
    tooltip.classList.remove("show");
  });
}

function hideTooltip(event) {
  const element = event.currentTarget;
  const tooltipKey = element.dataset.tooltipKey || element.classList[0];
  const tooltip = tooltipCache.get(tooltipKey);

  if (tooltip) {
    tooltip.classList.remove("show");
  }
}

// Export function to attach tooltips to dynamically created elements
export function attachTooltipToDynamicElement(element, tooltipKey) {
  if (!tooltipsEnabled) return;

  // Force attach immediately for dynamic elements
  element.dataset.tooltipKey = tooltipKey;
  attachTooltipHandlers(element);
}

// Export function to refresh tooltips on dynamic content
export function refreshTooltips() {
  // ALWAYS scan and attach handlers, even if tooltips are disabled
  // This way, when user enables tooltips later, they'll already be attached
  document.querySelectorAll('[data-tooltip-key]').forEach(element => {
    if (!element.dataset.tooltipAttached) {
      attachTooltipHandlers(element);
    }
  });
}

// Initialize on load
document.addEventListener("DOMContentLoaded", initTooltipSystem);

export { initTooltipSystem, tooltipsEnabled, refreshTooltips as updateTooltipsForDynamicContent };
