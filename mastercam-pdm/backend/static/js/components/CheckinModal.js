// backend/static/js/components/CheckinModal.js
import { Modal } from "./Modal.js";
// We'll need to add a checkinFile function to our api/service.js
// import { checkinFile } from '../api/service.js';

export function showCheckinDialog(file) {
  const template = document.getElementById("template-checkin-modal");
  const content = template.content.cloneNode(true);

  const modal = new Modal(content);
  modal.show(); // Show the modal FIRST

  // NOW we can safely find elements inside the live modal
  const form = modal.modalElement.querySelector("#checkinForm");
  const title = modal.modalElement.querySelector("#checkinModalTitle");
  title.textContent = `Check In: ${file.filename}`;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    // TODO: Call the checkinFile API service function
    alert(
      `Submitting check-in for ${file.filename}. (This needs to be wired up in api/service.js)`
    );
    modal.close();
  });
}
