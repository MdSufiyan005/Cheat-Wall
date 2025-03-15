/**
 * Test Detail page JavaScript
 */

document.addEventListener("DOMContentLoaded", function () {
  // Handle confirmation for activating/deactivating tests
  const toggleButton = document.querySelector(
    'form[action*="toggle-activation"] button'
  );
  if (toggleButton) {
    toggleButton.addEventListener("click", function (event) {
      const action = toggleButton.classList.contains("btn-danger")
        ? "deactivate"
        : "activate";
      if (!confirm(`Are you sure you want to ${action} this test?`)) {
        event.preventDefault();
      }
    });
  }

  // Calculate real-time durations for active sessions
  const activeDurations = document.querySelectorAll(
    "#active-sessions .session-duration"
  );
  if (activeDurations.length > 0) {
    // Update duration every minute
    function updateDurations() {
      activeDurations.forEach((element) => {
        const startTime = new Date(element.dataset.startTime);
        const now = new Date();
        const durationMinutes = Math.floor((now - startTime) / (1000 * 60));
        element.textContent = `${durationMinutes} min`;
      });
    }

    // Initial update
    updateDurations();

    // Update every minute
    setInterval(updateDurations, 60000);
  }

  // Handle pagination of session tables if they're long
  const sessionTables = document.querySelectorAll(".table");
  sessionTables.forEach((table) => {
    const rows = table.querySelectorAll("tbody tr");
    const maxRowsPerPage = 10;

    if (rows.length > maxRowsPerPage) {
      // TODO: Implement pagination if needed
      // For now, all rows are shown
    }
  });

  // Set up refresh button to update active session data
  const refreshButton = document.getElementById("refresh-data");
  if (refreshButton) {
    refreshButton.addEventListener("click", function () {
      location.reload();
    });
  }
});
