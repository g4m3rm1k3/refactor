// frontend/js/components/ConfigPanel.js

import { Modal } from "./Modal.js";
import { saveConfig } from "../api/service.js"; // NEW IMPORT
// We'll need our notification system here, which we'll refactor next.
// For now, we'll use a simple alert().

let panelElement = null;

function closePanel() {
  if (panelElement) {
    panelElement.classList.add("translate-x-full");
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

async function handleConfigFormSubmit(event) {
  event.preventDefault();
  const form = event.target;

  const configData = {
    gitlab_url: form.querySelector("#gitlabUrl").value,
    project_id: form.querySelector("#projectId").value,
    username: form.querySelector("#username").value,
    token: form.querySelector("#token").value,
    allow_insecure_ssl: form.querySelector("#allowInsecureSsl").checked,
  };

  try {
    const result = await saveConfig(configData);
    alert(
      "Configuration saved! Please restart the backend server (CTRL+C then `python run.py`)."
    );
    closePanel();
  } catch (error) {
    alert(`Error saving configuration: ${error.message}`);
  }
}

function openPanel() {
  if (panelElement) return;

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
      // switchTab(tabName); // Logic for this is still pending
    });
  });

  // NEW: Add event listener for the form submission
  const configForm = panelElement.querySelector("#configForm");
  if (configForm) {
    configForm.addEventListener("submit", handleConfigFormSubmit);
  }

  document.body.appendChild(panelElement);

  requestAnimationFrame(() => {
    panelElement.classList.remove("translate-x-full");
  });
}

export function setupConfigPanel(triggerButtonId) {
  const triggerButton = document.getElementById(triggerButtonId);
  if (triggerButton) {
    triggerButton.addEventListener("click", openPanel);
  }
}
