/**
 * Test Management specific JavaScript
 */

document.addEventListener("DOMContentLoaded", function () {
  // Get filter buttons and table rows
  const showAllBtn = document.getElementById("show-all-btn");
  const showActiveBtn = document.getElementById("show-active-btn");
  const showInactiveBtn = document.getElementById("show-inactive-btn");
  const tableRows = document.querySelectorAll("#test-table tbody tr");

  // Filter function to show/hide rows based on status
  function filterTests(status) {
    tableRows.forEach((row) => {
      if (status === "all" || row.dataset.status === status) {
        row.classList.remove("d-none");
      } else {
        row.classList.add("d-none");
      }
    });
  }

  // Add click event listeners to filter buttons
  if (showAllBtn) {
    showAllBtn.addEventListener("click", function () {
      filterTests("all");
      updateActiveButton(this);
    });
  }

  if (showActiveBtn) {
    showActiveBtn.addEventListener("click", function () {
      filterTests("active");
      updateActiveButton(this);
    });
  }

  if (showInactiveBtn) {
    showInactiveBtn.addEventListener("click", function () {
      filterTests("inactive");
      updateActiveButton(this);
    });
  }

  // Function to update active button styles
  function updateActiveButton(activeBtn) {
    const buttons = [showAllBtn, showActiveBtn, showInactiveBtn];
    buttons.forEach((btn) => {
      if (btn === activeBtn) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });
  }

  // Handle confirmation for activating/deactivating tests
  const toggleButtons = document.querySelectorAll(
    'form[action*="toggle-activation"] button'
  );
  toggleButtons.forEach((button) => {
    button.addEventListener("click", function (event) {
      const action = button.classList.contains("btn-danger")
        ? "deactivate"
        : "activate";
      if (!confirm(`Are you sure you want to ${action} this test?`)) {
        event.preventDefault();
      }
    });
  });
});
