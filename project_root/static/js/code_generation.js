/**
 * Code Generation specific JavaScript
 * Enhanced with better validation, error handling, and UX
 */

document.addEventListener("DOMContentLoaded", function () {
  // Get form and add submit event listener
  const form = document.getElementById("code-generation-form");
  if (form) {
    // Initialize validation state
    setupFormValidation(form);

    // Add real-time validation for datetime fields
    setupDateTimeValidation(form);

    // Handle form submission
    form.addEventListener("submit", function (e) {
      // Clear previous validation messages
      clearValidationMessages(form);

      // Validate form and show specific error messages
      if (!validateForm(form)) {
        e.preventDefault();
        showToast("Please correct the errors in the form", "warning");
        return false;
      }

      // Show loading state
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn) {
        // Store original button content for error state recovery
        submitBtn.dataset.originalHtml = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML =
          '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
      }

      // Enable progress tracking
      localStorage.setItem("codeGenerationSubmitted", "true");
      localStorage.setItem("codeGenerationTime", Date.now().toString());

      return true;
    });
  }

  // Set up real-time validation for the form
  function setupFormValidation(form) {
    // Add input event listeners to fields for real-time validation
    const requiredFields = form.querySelectorAll(
      "input[required], select[required], textarea[required]"
    );
    requiredFields.forEach((field) => {
      field.addEventListener("input", function () {
        validateField(this);
      });

      field.addEventListener("blur", function () {
        validateField(this, true);
      });
    });

    // Add validation for process selection and custom processes
    const customProcesses = form.querySelector("#custom_processes");
    const processCheckboxes = form.querySelectorAll(
      'input[name="whitelisted_processes"]'
    );

    if (customProcesses && processCheckboxes.length > 0) {
      // When custom processes change, check if we need process checkboxes
      customProcesses.addEventListener("input", function () {
        validateProcessSelection(form);
      });

      // When checkboxes change, update validation
      processCheckboxes.forEach((checkbox) => {
        checkbox.addEventListener("change", function () {
          validateProcessSelection(form);
        });
      });
    }
  }

  // Set up real-time validation for datetime fields
  function setupDateTimeValidation(form) {
    const startTimeField = form.querySelector("#start_time");
    const endTimeField = form.querySelector("#end_time");

    if (startTimeField && endTimeField) {
      // Validate dates when either changes
      [startTimeField, endTimeField].forEach((field) => {
        field.addEventListener("change", function () {
          validateDateTimeRange(startTimeField, endTimeField);
        });
      });

      // Initial validation
      validateDateTimeRange(startTimeField, endTimeField);
    }
  }

  // Validate the entire form
  function validateForm(form) {
    let isValid = true;

    // Validate all required fields
    const requiredFields = form.querySelectorAll(
      "input[required], select[required], textarea[required]"
    );
    requiredFields.forEach((field) => {
      if (!validateField(field, true)) {
        isValid = false;
      }
    });

    // Validate process selection
    if (!validateProcessSelection(form, true)) {
      isValid = false;
    }

    // Validate date range
    const startTime = form.querySelector("#start_time");
    const endTime = form.querySelector("#end_time");
    if (startTime && endTime) {
      if (!validateDateTimeRange(startTime, endTime, true)) {
        isValid = false;
      }
    }

    // Validate test title - must be at least 3 characters
    const titleField = form.querySelector("#title");
    if (titleField && titleField.value.trim().length < 3) {
      showValidationError(
        titleField,
        "Test title must be at least 3 characters"
      );
      isValid = false;
    }

    return isValid;
  }

  // Validate individual field
  function validateField(field, showError = false) {
    // Skip validation if field is not required and empty
    if (!field.required && !field.value.trim()) {
      clearValidationMessage(field);
      return true;
    }

    let isValid = true;
    let errorMessage = "";

    // Check if field is empty when required
    if (field.required && !field.value.trim()) {
      isValid = false;
      errorMessage = "This field is required";
    }

    // Additional validation based on field type
    switch (field.type) {
      case "email":
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (field.value.trim() && !emailPattern.test(field.value.trim())) {
          isValid = false;
          errorMessage = "Please enter a valid email address";
        }
        break;

      case "select-one":
        if (field.required && (!field.value || field.value === "")) {
          isValid = false;
          errorMessage = "Please select an option";
        }
        break;
    }

    // Show or clear validation message
    if (!isValid && showError) {
      showValidationError(field, errorMessage);
    } else if (isValid) {
      clearValidationMessage(field);
    }

    return isValid;
  }

  // Validate process selection
  function validateProcessSelection(form, showError = false) {
    const checkboxes = form.querySelectorAll(
      'input[name="whitelisted_processes"]:checked'
    );
    const customProcesses = form.querySelector("#custom_processes");
    const processSection =
      form.querySelector(".process-selection-section") ||
      form.querySelector("#process-selection-container");

    let isValid = true;

    // Either checkboxes or custom processes must be provided
    if (
      checkboxes.length === 0 &&
      (!customProcesses || !customProcesses.value.trim())
    ) {
      isValid = false;

      if (showError && processSection) {
        showValidationError(
          processSection,
          "Please select at least one process or add custom processes",
          "process-selection-error"
        );
      }
    } else if (processSection) {
      clearValidationMessage(processSection, "process-selection-error");
    }

    return isValid;
  }

  // Validate date-time range
  function validateDateTimeRange(startField, endField, showError = false) {
    if (!startField || !endField) return true;

    const startTime = new Date(startField.value);
    const endTime = new Date(endField.value);
    const now = new Date();

    let isValid = true;

    // Check if dates are valid
    if (isNaN(startTime.getTime()) || isNaN(endTime.getTime())) {
      isValid = false;
      if (showError) {
        if (isNaN(startTime.getTime())) {
          showValidationError(startField, "Please enter a valid start time");
        }
        if (isNaN(endTime.getTime())) {
          showValidationError(endField, "Please enter a valid end time");
        }
      }
    }
    // Check if end is after start
    else if (endTime <= startTime) {
      isValid = false;
      if (showError) {
        showValidationError(endField, "End time must be after start time");
      }
    }
    // Warn if start time is in the past
    else if (startTime < now) {
      // This is a warning, not an error
      if (showError && now - startTime > 1000 * 60 * 5) {
        // More than 5 minutes in the past
        showValidationError(
          startField,
          "Start time is in the past",
          null,
          "warning"
        );
      }
    } else {
      // Clear messages if valid
      clearValidationMessage(startField);
      clearValidationMessage(endField);
    }

    return isValid;
  }

  // Show validation error message
  function showValidationError(
    element,
    message,
    customId = null,
    type = "error"
  ) {
    // Clear any existing message first
    clearValidationMessage(element, customId);

    // Create error message
    const errorId = customId || `${element.id}-error`;
    const errorDiv = document.createElement("div");
    errorDiv.id = errorId;
    errorDiv.className =
      type === "error"
        ? "invalid-feedback d-block mt-1"
        : "text-warning small mt-1";
    errorDiv.textContent = message;

    // Add error styling to the element
    if (type === "error") {
      element.classList.add("is-invalid");
    }

    // Find the right place to insert the error
    const formGroup =
      element.closest(".form-group") || element.closest(".mb-3");
    if (formGroup) {
      formGroup.appendChild(errorDiv);
    } else {
      // If no form group, insert after the element
      element.parentNode.insertBefore(errorDiv, element.nextSibling);
    }
  }

  // Clear validation message for a field
  function clearValidationMessage(element, customId = null) {
    // Remove is-invalid class
    element.classList.remove("is-invalid");

    // Remove error message if it exists
    const errorId = customId || `${element.id}-error`;
    const errorElement = document.getElementById(errorId);
    if (errorElement) {
      errorElement.remove();
    }
  }

  // Clear all validation messages in a form
  function clearValidationMessages(form) {
    // Remove is-invalid class from all elements
    form.querySelectorAll(".is-invalid").forEach((element) => {
      element.classList.remove("is-invalid");
    });

    // Remove all error messages
    form
      .querySelectorAll(".invalid-feedback, .text-warning.small")
      .forEach((element) => {
        element.remove();
      });
  }

  // Add functionality for "Select All" processes button
  const selectAllBtn = document.getElementById("select-all-processes");
  if (selectAllBtn) {
    selectAllBtn.addEventListener("click", function () {
      const checkboxes = form.querySelectorAll(
        'input[name="whitelisted_processes"]'
      );
      const allChecked = Array.from(checkboxes).every((cb) => cb.checked);

      // Toggle all checkboxes
      checkboxes.forEach((checkbox) => {
        checkbox.checked = !allChecked;
      });

      // Update button text
      this.innerHTML = allChecked ? "Select All" : "Deselect All";

      // Validate process selection
      validateProcessSelection(form);
    });
  }

  // If encrypted code is shown, enhance UX for copying
  const encryptedCodeArea = document.getElementById("encrypted-code");
  if (encryptedCodeArea) {
    // Add click to select all in textarea
    encryptedCodeArea.addEventListener("click", function () {
      this.select();
    });

    // Highlight that it can be copied
    encryptedCodeArea.title = "Click to select all text";
  }

  // Add auto-scaling functionality to textareas
  const autoResizeTextareas = document.querySelectorAll("textarea.auto-resize");
  autoResizeTextareas.forEach((textarea) => {
    textarea.addEventListener("input", function () {
      this.style.height = "auto";
      this.style.height = this.scrollHeight + "px";
    });

    // Initial resize
    textarea.dispatchEvent(new Event("input"));
  });

  // If form was just submitted (and we got redirected back)
  if (localStorage.getItem("codeGenerationSubmitted") === "true") {
    // Check if the code is now generated
    if (encryptedCodeArea && encryptedCodeArea.value) {
      showToast(
        "Code generated successfully! Copy it to share with students.",
        "success"
      );

      // Focus the textarea for easier copying
      setTimeout(() => {
        encryptedCodeArea.focus();
        encryptedCodeArea.select();
      }, 500);
    }

    // Clear the submission state
    localStorage.removeItem("codeGenerationSubmitted");
    localStorage.removeItem("codeGenerationTime");
  }
});
