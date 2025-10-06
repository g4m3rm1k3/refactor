// frontend/js/components/ConfigPanel.js

let panelElement = null; // This will hold the live DOM element for the panel

function closePanel() {
  if (panelElement) {
    panelElement.classList.add("translate-x-full");
    // Remove the element from the DOM after the transition is complete
    panelElement.addEventListener(
      "transitionend",
      () => {
        panelElement.remove();
        panelElement = null;
      },
      { once: true }
    );
  }
}

function openPanel() {
  if (panelElement) return; // Already open

  const template = document.getElementById("template-config-panel");
  const content = template.content.cloneNode(true);
  panelElement = content.firstElementChild;

  // Add event listeners for closing
  panelElement
    .querySelector('[data-action="close"]')
    .addEventListener("click", closePanel);

  // Add event listeners for tab switching
  panelElement.querySelectorAll(".config-tab").forEach((tabButton) => {
    tabButton.addEventListener("click", () => {
      const tabName = tabButton.id.replace("Tab", "");
      switchTab(tabName);
    });
  });

  document.body.appendChild(panelElement);

  // Trigger the slide-in animation
  requestAnimationFrame(() => {
    panelElement.classList.remove("translate-x-full");
  });
}

function switchTab(tabName) {
  if (!panelElement) return;

  // Update tab buttons
  panelElement.querySelectorAll(".config-tab").forEach((btn) => {
    btn.classList.toggle("active", btn.id === `${tabName}Tab`);
  });

  // Update tab content
  panelElement.querySelectorAll(".config-tab-content").forEach((content) => {
    content.classList.toggle("hidden", content.id !== `${tabName}Content`);
  });

  // Load data if switching to a data-heavy tab
  if (tabName === "health") {
    // TODO: Call a function to refresh health status
    console.log("Switched to Health tab. Need to load data.");
  }
}

// This is the main function we will export.
// It attaches the openPanel function to a trigger button.
export function setupConfigPanel(triggerButtonId) {
  const triggerButton = document.getElementById(triggerButtonId);
  if (triggerButton) {
    triggerButton.addEventListener("click", openPanel);
  }
}
