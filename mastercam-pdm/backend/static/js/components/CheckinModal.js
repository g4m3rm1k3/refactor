// backend/static/js/components/CheckinModal.js
import { Modal } from "./Modal.js";
import { checkinFile } from "../api/service.js";
import { showNotification } from "../utils/helpers.js";
import { setState, getState } from "../state/store.js";
import { getFiles } from "../api/service.js";

export function showCheckinDialog(file) {
  const template = document.getElementById("template-checkin-modal");
  const content = template.content.cloneNode(true);

  const modal = new Modal(content);
  modal.show(); // Show the modal FIRST

  // NOW we can safely find elements inside the live modal
  const form = modal.modalElement.querySelector("#checkinForm");
  const title = modal.modalElement.querySelector("#checkinModalTitle");
  const fileInput = modal.modalElement.querySelector("#checkinFileUpload");
  const messageInput = modal.modalElement.querySelector("#commitMessage");

  title.textContent = `Check In: ${file.filename}`;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const state = getState();
    const user = state.currentUser;

    // Validate file is selected
    if (!fileInput.files || fileInput.files.length === 0) {
      showNotification("Please select a file to upload", "error");
      return;
    }

    // Validate filename matches
    const uploadedFile = fileInput.files[0];
    if (uploadedFile.name !== file.filename) {
      showNotification(
        `Error: Uploaded file name "${uploadedFile.name}" must match the original file name "${file.filename}"`,
        "error"
      );
      return;
    }

    // Validate commit message
    const commitMessage = messageInput.value.trim();
    if (!commitMessage) {
      showNotification("Please enter a commit message", "error");
      return;
    }

    try {
      showNotification("Checking in file...", "info");

      await checkinFile(
        file.filename,
        uploadedFile,
        commitMessage,
        user,
        "minor", // Default to minor revision
        null
      );

      showNotification(`Successfully checked in ${file.filename}`, "success");
      modal.close();

      // Refresh file list
      const filesData = await getFiles();
      setState({ groupedFiles: filesData });
    } catch (error) {
      showNotification(`Check-in failed: ${error.message}`, "error");
    }
  });
}
