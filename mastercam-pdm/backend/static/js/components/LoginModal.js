// backend/static/js/components/LoginModal.js
import { Modal } from "./Modal.js";
import { login, setupInitialUser } from "../services/auth.js";

export function showAuthDialog(username, hasPassword) {
  // This function now returns a Promise
  return new Promise((resolve) => {
    const template = document.getElementById("template-login-modal");
    const content = template.content.cloneNode(true);
    const modal = new Modal(content, { closable: false });
    modal.show();

    const loginForm = modal.modalElement.querySelector("#loginForm");
    const setupForm = modal.modalElement.querySelector("#setupPasswordForm");
    const switchToLoginBtn = modal.modalElement.querySelector("#switchToLoginBtn");

    const handleSuccess = () => {
      modal.close();
      resolve(true); // Signal that login was successful
    };

    const handleFailure = (err) => {
      alert(`Error: ${err.message}`);
      resolve(false); // Signal that login failed
    };

    // Wire up "Switch to Login" button
    if (switchToLoginBtn) {
      switchToLoginBtn.addEventListener("click", () => {
        setupForm.classList.add("hidden");
        loginForm.classList.remove("hidden");
      });
    }

    if (hasPassword) {
      // --- LOG IN EXISTING USER ---
      loginForm.classList.remove("hidden");
      const usernameInput = loginForm.querySelector("#loginUsername");
      const passwordInput = loginForm.querySelector("#loginPassword");
      usernameInput.value = username;

      loginForm.addEventListener("submit", async (e) => {
        console.log("Login form submitted!"); // <-- ADD THIS LINE
        e.preventDefault();
        try {
          console.log("Attempting login..."); // <-- PROBE 1
          await login(username, passwordInput.value);
          console.log("Login successful! Calling handleSuccess()..."); // <-- PROBE 2
          handleSuccess();
        } catch (error) {
          passwordInput.value = "";
          alert(`Login failed: ${error.message}`);
          // We don't resolve here, allowing the user to try again
        }
      });
    } else {
      // --- SETUP NEW USER PASSWORD ---
      setupForm.classList.remove("hidden");
      const usernameInput = setupForm.querySelector("#setupUsername");
      const tokenInput = setupForm.querySelector("#setupGitlabToken");
      const passwordInput = setupForm.querySelector("#setupPassword");
      const confirmInput = setupForm.querySelector("#confirmPassword");
      usernameInput.value = username;

      setupForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        // Validate passwords match
        if (passwordInput.value !== confirmInput.value) {
          confirmInput.classList.add("border-red-500");
          return alert("Passwords do not match.");
        }

        // Validate password length
        if (passwordInput.value.length < 6) {
          passwordInput.classList.add("border-red-500");
          return alert("Password must be at least 6 characters long.");
        }

        // Validate token is provided
        if (!tokenInput.value.trim()) {
          tokenInput.classList.add("border-red-500");
          return alert("GitLab Personal Access Token is required.");
        }

        try {
          await setupInitialUser(
            username,
            tokenInput.value,
            passwordInput.value
          );
          handleSuccess();
        } catch (error) {
          tokenInput.value = "";
          passwordInput.value = "";
          confirmInput.value = "";
          alert(`Setup failed: ${error.message}`);
          // We don't resolve here, allowing the user to try again
        }
      });
    }
  });
}
