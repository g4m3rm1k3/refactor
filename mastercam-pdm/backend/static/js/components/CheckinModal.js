// frontend/js/components/CheckinModal.js

import { Modal } from "./Modal.js";

export function showCheckinDialog(file) {
  const template = document.getElementById("template-checkin-modal");
  const content = template.content.cloneNode(true);

  // Populate the title with the filename
  content.querySelector(
    "#checkinModalTitle"
  ).textContent = `Check In: ${file.filename}`;

  const modal = new Modal(content);

  // Add the specific logic for this form
  const form = modal.modalElement.querySelector("#checkinForm");
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    // TODO: Add logic to call the API service to check in the file.
    console.log(`Submitting check-in for ${file.filename}`);
    modal.close();
  });

  modal.show();
}
