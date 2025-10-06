// backend/static/js/components/Modal.js

export class Modal {
  constructor(contentElement, options = { closable: true }) {
    this.contentElement = contentElement;
    this.options = options;
    this.modalElement = null;
  }

  show() {
    const modalHtml = `<div class="fixed inset-0 bg-gray-900 bg-opacity-75 flex items-center justify-center p-4 z-50"></div>`;
    const modalFragment = document
      .createRange()
      .createContextualFragment(modalHtml);
    this.modalElement = modalFragment.firstElementChild;

    this.modalElement.appendChild(this.contentElement);

    this.modalElement.addEventListener("click", (e) => {
      if (
        this.options.closable &&
        (e.target === this.modalElement ||
          e.target.closest('[data-action="close"]'))
      ) {
        this.close();
      }
    });

    document.body.appendChild(this.modalElement);
  }

  close() {
    console.log("Attempting to close modal...", this.modalElement); // Our debug probe
    if (this.modalElement) {
      // These are the crucial lines that were missing
      this.modalElement.remove();
      this.modalElement = null;
      console.log("Modal element successfully removed from DOM."); // Our debug probe
    }
  }
}
