// frontend/js/components/Modal.js

export class Modal {
  constructor(contentElement) {
    this.contentElement = contentElement;
    this.modalElement = null;
  }

  show() {
    const modalHtml = `
      <div class="fixed inset-0 bg-gray-900 bg-opacity-75 flex items-center justify-center p-4 z-50">
      </div>
    `;
    const modalFragment = document
      .createRange()
      .createContextualFragment(modalHtml);
    this.modalElement = modalFragment.firstElementChild;

    // Append the user-provided content into our modal panel
    this.modalElement.appendChild(this.contentElement);

    // Add event listeners for closing the modal
    this.modalElement.addEventListener("click", (e) => {
      if (
        e.target === this.modalElement ||
        e.target.closest('[data-action="close"]')
      ) {
        this.close();
      }
    });

    document.body.appendChild(this.modalElement);
  }

  close() {
    if (this.modalElement) {
      this.modalElement.remove();
      this.modalElement = null;
    }
  }
}
