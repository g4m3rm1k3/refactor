// frontend/js/components/NewUploadModal.js

import { Modal } from "./Modal.js";
import { getState } from "../state/store.js";

export function showNewUploadDialog() {
  const template = document.getElementById("template-new-upload-modal");
  const content = template.content.cloneNode(true);

  const modal = new Modal(content);
  modal.show();

  // Get references to elements inside the modal
  const form = modal.modalElement.querySelector("#newUploadForm");
  const fileContainer = modal.modalElement.querySelector(
    "#fileUploadContainer"
  );
  const linkContainer = modal.modalElement.querySelector(
    "#linkCreateContainer"
  );
  const uploadTypeRadios = modal.modalElement.querySelectorAll(
    'input[name="uploadType"]'
  );

  // Function to toggle between File/Link views
  function updateUploadTypeView() {
    const selectedValue = modal.modalElement.querySelector(
      'input[name="uploadType"]:checked'
    ).value;
    if (selectedValue === "link") {
      fileContainer.classList.add("hidden");
      linkContainer.classList.remove("hidden");
      // TODO: Populate master file list
    } else {
      fileContainer.classList.remove("hidden");
      linkContainer.classList.add("hidden");
    }
  }

  // Add event listeners for the radio buttons
  uploadTypeRadios.forEach((radio) => {
    radio.addEventListener("change", updateUploadTypeView);
  });

  // Handle form submission
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    // TODO: Add form validation and call API service
    console.log("Submitting new upload form...");
    modal.close();
  });
}
