// frontend/js/utils/helpers.js

export function formatBytes(bytes) {
  if (!bytes || bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

class NotificationManager {
  constructor() {
    this.container = document.getElementById("notification-container");
    this.queue = [];
    this.currentNotification = null;
  }

  show(message, type = "info", duration = 4000) {
    if (this.currentNotification) {
      this.queue.push({ message, type, duration });
    } else {
      this._display(message, type, duration);
    }
  }

  _display(message, type, duration) {
    if (!this.container) return;

    const notification = document.createElement("div");
    notification.className = `p-4 rounded-lg shadow-lg transform transition-all duration-300 translate-x-full flex items-start space-x-3`;

    // Icon mapping
    const iconMap = {
      success: "fa-check-circle",
      error: "fa-exclamation-circle",
      warning: "fa-exclamation-triangle",
      info: "fa-info-circle",
    };

    const icon = iconMap[type] || iconMap.info;

    // Color mapping with inline styles to ensure they work
    let bgColor, textColor;
    switch (type) {
      case "success":
        bgColor = "#16a34a"; // green-600
        textColor = "#ffffff";
        break;
      case "error":
        bgColor = "#dc2626"; // red-600
        textColor = "#ffffff";
        break;
      case "warning":
        bgColor = "#fbbf24"; // amber-400
        textColor = "#1f2937"; // gray-900
        break;
      default:
        bgColor = "#3b82f6"; // blue-500
        textColor = "#ffffff";
    }

    notification.style.backgroundColor = bgColor;
    notification.style.color = textColor;

    notification.innerHTML = `
      <div class="flex-shrink-0 pt-0.5">
        <i class="fa-solid ${icon}"></i>
      </div>
      <div class="flex-1 text-sm font-medium">${message}</div>
      <button class="flex-shrink-0 ml-2 text-current opacity-70 hover:opacity-100" onclick="this.closest('div').remove()">
        <i class="fa-solid fa-times"></i>
      </button>
    `;

    this.currentNotification = notification;
    this.container.appendChild(notification);

    // Animate in
    setTimeout(() => notification.classList.remove("translate-x-full"), 50);

    // Auto-dismiss
    const dismissTimer = setTimeout(() => {
      this._dismiss(notification);
    }, duration);

    // Manual dismiss
    notification.querySelector("button").addEventListener("click", () => {
      clearTimeout(dismissTimer);
      this._dismiss(notification);
    });
  }

  _dismiss(notification) {
    notification.classList.add("translate-x-full");
    notification.addEventListener("transitionend", () => {
      notification.remove();
      this.currentNotification = null;

      // Show next notification in queue
      if (this.queue.length > 0) {
        const next = this.queue.shift();
        this._display(next.message, next.type, next.duration);
      }
    });
  }
}

// Initialize global notification manager
const notificationManager = new NotificationManager();

export function showNotification(message, type = "info", duration = 4000) {
  console.log(`Notification (${type}): ${message}`);
  notificationManager.show(message, type, duration);
}

export function debounce(func, delay) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), delay);
  };
}

export function formatDate(dateString) {
  if (!dateString) return "Unknown";
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return "Invalid Date";
    const options = {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    };
    return date.toLocaleString(undefined, options);
  } catch (error) {
    console.error("Error formatting date:", dateString, error);
    return "Date Error";
  }
}

export function formatDuration(totalSeconds) {
  if (totalSeconds < 60) {
    return `${Math.round(totalSeconds)}s`;
  }
  const days = Math.floor(totalSeconds / 86400);
  totalSeconds %= 86400;
  const hours = Math.floor(totalSeconds / 3600);
  totalSeconds %= 3600;
  const minutes = Math.floor(totalSeconds / 60);

  let parts = [];
  if (days > 0) parts.push(`${days}d`);
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);

  return parts.join(" ") || "0m";
}
