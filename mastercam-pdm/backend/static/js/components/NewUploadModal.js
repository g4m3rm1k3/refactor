// frontend/js/components/NewUploadModal.js

import { Modal } from "./Modal.js";
import { getState } from "../state/store.js";
import { uploadNewFile } from "../api/service.js";
import { showNotification } from "../utils/helpers.js";

export function showNewUploadDialog() {
  const template = document.getElementById("template-new-upload-modal");
  const content = template.content.cloneNode(true);

  const modal = new Modal(content);
  modal.show();

  // Get references to elements inside the modal
  const form = modal.modalElement.querySelector("#newUploadForm");
  const fileContainer = modal.modalElement.querySelector("#fileUploadContainer");
  const linkContainer = modal.modalElement.querySelector("#linkCreateContainer");
  const uploadTypeRadios = modal.modalElement.querySelectorAll('input[name="uploadType"]');
  const submitBtn = modal.modalElement.querySelector('button[type="submit"]');
  const submitText = modal.modalElement.querySelector("#submitBtnText");
  const submitSpinner = modal.modalElement.querySelector("#submitSpinner");

  // Function to toggle between File/Link views
  function updateUploadTypeView() {
    const selectedValue = modal.modalElement.querySelector(
      'input[name="uploadType"]:checked'
    ).value;

    if (selectedValue === "link") {
      fileContainer.classList.add("hidden");
      linkContainer.classList.remove("hidden");
      populateMasterFileList();
    } else {
      fileContainer.classList.remove("hidden");
      linkContainer.classList.add("hidden");
    }
  }

  // Populate master file list for link creation
  function populateMasterFileList() {
    const datalist = document.getElementById("masterFileList");
    if (!datalist) return;

    datalist.innerHTML = "";

    const state = getState();
    if (!state.groupedFiles || Object.keys(state.groupedFiles).length === 0) {
      return;
    }

    // Get all physical files (not links)
    const physicalFiles = Object.values(state.groupedFiles)
      .flat()
      .filter((file) => !file.is_link);

    // Get unique filenames
    const uniqueFilenames = new Set(physicalFiles.map((file) => file.filename));

    // Add options to datalist
    uniqueFilenames.forEach((filename) => {
      const option = document.createElement("option");
      option.value = filename;
      datalist.appendChild(option);
    });
  }

  // Add event listeners for the radio buttons
  uploadTypeRadios.forEach((radio) => {
    radio.addEventListener("change", updateUploadTypeView);
  });

  // Handle form submission
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const state = getState();
    const currentUser = state.currentUser;

    if (!currentUser) {
      showNotification("You must be logged in to upload files.", "error");
      return;
    }

    const formData = new FormData();
    formData.append("user", currentUser);

    const description = modal.modalElement
      .querySelector("#newFileDescription")
      .value.trim();
    const rev = modal.modalElement.querySelector("#newFileRev").value.trim();
    const uploadType = modal.modalElement.querySelector(
      'input[name="uploadType"]:checked'
    ).value;

    // Validation
    if (!description || !rev) {
      showNotification(
        "Please fill out the Description and Revision fields.",
        "error"
      );
      return;
    }

    // Validate revision format
    if (!/^\d+\.\d+$/.test(rev)) {
      showNotification(
        "Revision must be in format X.Y (e.g., 1.0)",
        "error"
      );
      return;
    }

    if (uploadType === "link") {
      // Link creation
      const newLinkFilename = modal.modalElement
        .querySelector("#newLinkFilename")
        .value.trim();
      const linkToMaster = modal.modalElement
        .querySelector("#linkToMaster")
        .value.trim();

      if (!newLinkFilename || !linkToMaster) {
        showNotification(
          "Please provide both a new link name and a master file.",
          "error"
        );
        return;
      }

      formData.append("is_link_creation", "true");
      formData.append("new_link_filename", newLinkFilename);
      formData.append("link_to_master", linkToMaster);
    } else {
      // File upload
      const fileInput = modal.modalElement.querySelector("#newFileUpload");
      if (fileInput.files.length === 0) {
        showNotification("Please select a file to upload.", "error");
        return;
      }
      formData.append("is_link_creation", "false");
      formData.append("file", fileInput.files[0]);
    }

    formData.append("description", description);
    formData.append("rev", rev);

    // Show loading state
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.classList.add("opacity-75", "cursor-not-allowed");
      if (submitText) submitText.textContent = "Creating...";
      if (submitSpinner) submitSpinner.classList.remove("hidden");
    }

    try {
      const result = await uploadNewFile(formData);

      showNotification(
        result.message || "File/Link created successfully!",
        "success"
      );

      // Close modal on success
      modal.close();

      // Reload the file list to show the new file
      // The main app should handle this via state change
      window.location.reload();

    } catch (error) {
      let displayError = error.message;

      if (error.message.includes("409")) {
        displayError = `File or link already exists. ${displayError}`;
      } else if (error.message.includes("404")) {
        displayError = `Master file not found. ${displayError}`;
      } else if (error.message.includes("400")) {
        displayError = `Invalid input. ${displayError}`;
      }

      showNotification(displayError, "error");

      // Reset loading state
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.classList.remove("opacity-75", "cursor-not-allowed");
        if (submitText) submitText.textContent = "Create";
        if (submitSpinner) submitSpinner.classList.add("hidden");
      }
    }
  });

  // Initialize the view
  updateUploadTypeView();
}
