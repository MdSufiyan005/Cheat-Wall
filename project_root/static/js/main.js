/**
 * Main JavaScript for the Proctoring Admin System
 */

// Function to copy text to clipboard
function copyToClipboard(elementId) {
  const element = document.getElementById(elementId);
  if (!element) {
    console.error(`Element with ID '${elementId}' not found`);
    return false;
  }

  // Get the text to copy
  let textToCopy = "";
  if (element.tagName === "TEXTAREA" || element.tagName === "INPUT") {
    textToCopy = element.value;
  } else {
    textToCopy = element.textContent;
  }

  // Check if text is empty
  if (!textToCopy.trim()) {
    console.warn(`Element with ID '${elementId}' has no content to copy`);
    showToast("No content to copy", "warning");
    return false;
  }

  // Try using the modern clipboard API first
  if (navigator.clipboard && window.isSecureContext) {
    try {
      navigator.clipboard
        .writeText(textToCopy)
        .then(() => {
          showCopySuccess(elementId);
          console.log("Text copied using Clipboard API");
        })
        .catch((err) => {
          console.error("Clipboard API error:", err);
          fallbackCopyMethod(textToCopy, elementId);
        });
      return true;
    } catch (err) {
      console.error("Clipboard API error:", err);
      // Fall back to execCommand method
      return fallbackCopyMethod(textToCopy, elementId);
    }
  } else {
    // Fall back to execCommand method
    return fallbackCopyMethod(textToCopy, elementId);
  }
}

// Fallback copy method for older browsers
function fallbackCopyMethod(text, elementId) {
  let textarea;
  let result = false;

  try {
    // Create temporary element
    textarea = document.createElement("textarea");
    textarea.value = text;

    // Make it invisible but ensure it's in the viewport
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.left = "0";
    textarea.style.top = "0";
    textarea.style.opacity = "0";
    textarea.style.pointerEvents = "none";

    document.body.appendChild(textarea);

    // Select the text
    textarea.focus();
    textarea.select();

    // Copy the text
    result = document.execCommand("copy");

    if (result) {
      showCopySuccess(elementId);
      console.log("Text copied using execCommand method");
    } else {
      showToast("Failed to copy to clipboard", "danger");
      console.error("execCommand copy failed");
    }
  } catch (err) {
    console.error("Fallback copy method error:", err);
    showToast("Failed to copy to clipboard: " + err.message, "danger");
  } finally {
    // Clean up
    if (textarea) {
      document.body.removeChild(textarea);
    }
  }

  return result;
}

// Show success indication on the button
function showCopySuccess(elementId) {
  const btn = document.querySelector(
    `[onclick="copyToClipboard('${elementId}')"]`
  );
  if (btn) {
    const originalHtml = btn.innerHTML;
    const originalClasses = btn.className;

    // Add success styling
    btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
    btn.className = originalClasses
      .replace("btn-primary", "btn-success")
      .replace("btn-secondary", "btn-success");

    // Reset after 2 seconds
    setTimeout(() => {
      btn.innerHTML = originalHtml;
      btn.className = originalClasses;
    }, 2000);
  } else {
    // If no button found, show a toast
    showToast("Copied to clipboard!", "success");
  }
}

// Show a toast notification
function showToast(message, type = "info") {
  // Check if toast container exists, if not create it
  let toastContainer = document.getElementById("toast-container");
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.id = "toast-container";
    toastContainer.className = "position-fixed bottom-0 end-0 p-3";
    toastContainer.style.zIndex = "5";
    document.body.appendChild(toastContainer);
  }

  // Create toast element
  const toastId = "toast-" + Date.now();
  const toast = document.createElement("div");
  toast.className = `toast align-items-center text-white bg-${type} border-0`;
  toast.id = toastId;
  toast.setAttribute("role", "alert");
  toast.setAttribute("aria-live", "assertive");
  toast.setAttribute("aria-atomic", "true");

  // Toast content
  toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

  // Add toast to container
  toastContainer.appendChild(toast);

  // Initialize and show the toast
  const bsToast = new bootstrap.Toast(toast, { autohide: true, delay: 3000 });
  bsToast.show();

  // Remove toast from DOM after it's hidden
  toast.addEventListener("hidden.bs.toast", function () {
    toast.remove();
  });
}

document.addEventListener("DOMContentLoaded", function () {
  // Enable all tooltips
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Format datetime-local inputs to current time
  const datetimeInputs = document.querySelectorAll(
    'input[type="datetime-local"]'
  );
  if (datetimeInputs.length > 0) {
    // Format current date and future date (in 2 hours) for the datetime inputs
    const now = new Date();
    const twoHoursLater = new Date(now.getTime() + 2 * 60 * 60 * 1000);

    const formatDatetimeLocal = (date) => {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, "0");
      const day = String(date.getDate()).padStart(2, "0");
      const hours = String(date.getHours()).padStart(2, "0");
      const minutes = String(date.getMinutes()).padStart(2, "0");

      return `${year}-${month}-${day}T${hours}:${minutes}`;
    };

    // Set default values for start and end time
    datetimeInputs.forEach((input) => {
      if (input.id === "start_time" && !input.value) {
        input.value = formatDatetimeLocal(now);
      } else if (input.id === "end_time" && !input.value) {
        input.value = formatDatetimeLocal(twoHoursLater);
      }
    });
  }

  // Handle auto-dismiss of alerts after 5 seconds
  const alerts = document.querySelectorAll(".alert");
  alerts.forEach((alert) => {
    setTimeout(() => {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 5000);
  });
});
