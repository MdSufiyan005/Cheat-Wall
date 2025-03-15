/**
 * Completed Tests Dashboard JavaScript
 */

document.addEventListener("DOMContentLoaded", function () {
  // Initialize tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Table filtering functionality
  const testFilter = document.getElementById("testFilter");
  const riskFilter = document.getElementById("riskFilter");
  const searchFilter = document.getElementById("searchFilter");
  const tableRows = document.querySelectorAll("#completedSessionsTable tbody tr");

  function applyFilters() {
    const testValue = testFilter.value;
    const riskValue = riskFilter.value;
    const searchValue = searchFilter.value.toLowerCase();

    tableRows.forEach((row) => {
      const testMatch = testValue === "all" || row.dataset.testId === testValue;

      // Risk filter
      let riskMatch = true;
      const riskScore = parseFloat(row.dataset.risk);
      if (riskValue === "high") {
        riskMatch = riskScore >= 0.7;
      } else if (riskValue === "medium") {
        riskMatch = riskScore >= 0.3 && riskScore < 0.7;
      } else if (riskValue === "low") {
        riskMatch = riskScore < 0.3;
      }

      // Search filter
      const studentName = row.dataset.student.toLowerCase();
      const studentId = row.dataset.id.toLowerCase();
      const searchMatch = studentName.includes(searchValue) || studentId.includes(searchValue);

      if (testMatch && riskMatch && searchMatch) {
        row.classList.remove("d-none");
      } else {
        row.classList.add("d-none");
      }
    });

    updateCharts();
    updateSummary();
  }

  // Add event listeners
  if (testFilter) testFilter.addEventListener("change", applyFilters);
  if (riskFilter) riskFilter.addEventListener("change", applyFilters);
  if (searchFilter) searchFilter.addEventListener("input", applyFilters);

  // Export to CSV functionality
  const exportBtn = document.getElementById("exportCSV");
  if (exportBtn) {
    exportBtn.addEventListener("click", function () {
      // Get visible rows
      const visibleRows = Array.from(tableRows).filter(
        (row) => !row.classList.contains("d-none")
      );

      // Prepare CSV content
      let csvContent = "Student,Enrollment Number,Test,Completion Time,Duration,Risk Score\n";

      visibleRows.forEach((row) => {
        const cells = row.querySelectorAll("td");
        const student = cells[0].textContent.trim();
        const enrollment = cells[1].textContent.trim();
        const test = cells[2].textContent.trim();
        const completion = cells[3].textContent.trim();
        const duration = cells[4].textContent.trim();
        const riskScore = row.dataset.risk * 100 + "%";

        csvContent += `"${student}","${enrollment}","${test}","${completion}","${duration}","${riskScore}"\n`;
      });

      // Create download link
      const encodedUri = encodeURI("data:text/csv;charset=utf-8," + csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", "completed_tests_export.csv");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Show success message
      showToast("CSV file downloaded successfully!", "success");
    });
  }

  // Generate report buttons
  document.querySelectorAll(".generate-report-btn").forEach((btn) => {
    btn.addEventListener("click", function () {
      const sessionId = this.dataset.sessionId;
      
      // Show loading indicator
      this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
      this.disabled = true;
      
      // Simulate report generation (replace with actual AJAX call)
      setTimeout(() => {
        // Reset button
        this.innerHTML = '<i class="fas fa-file-pdf"></i>';
        this.disabled = false;
        
        // Show success message
        showToast(`Report for session ${sessionId} has been generated!`, "success");
        
        // In a real implementation, you would:
        // 1. Make an AJAX call to a backend endpoint
        // 2. Generate PDF on server
        // 3. Return a download link or open in new tab
      }, 1500);
    });
  });

  // Highlight rows on hover
  tableRows.forEach((row) => {
    row.addEventListener("mouseenter", function () {
      this.classList.add("table-active");
    });
    row.addEventListener("mouseleave", function () {
      this.classList.remove("table-active");
    });
  });

  // Setup chart objects
  let riskChart;
  let testChart;

  // Update charts based on filtered data
  function updateCharts() {
    // Only proceed if charts container exists
    if (!document.getElementById("riskDistributionChart")) return;

    // Get visible rows
    const visibleRows = Array.from(tableRows).filter(
      (row) => !row.classList.contains("d-none")
    );

    // Count risk levels
    let lowRisk = 0;
    let mediumRisk = 0;
    let highRisk = 0;

    // Count by test
    const testCounts = {};

    visibleRows.forEach((row) => {
      const riskScore = parseFloat(row.dataset.risk);
      if (riskScore < 0.3) {
        lowRisk++;
      } else if (riskScore < 0.7) {
        mediumRisk++;
      } else {
        highRisk++;
      }

      const testId = row.dataset.testId;
      const testName = row.querySelector("td:nth-child(3)").textContent.trim();

      if (!testCounts[testId]) {
        testCounts[testId] = {
          count: 0,
          name: testName,
        };
      }
      testCounts[testId].count++;
    });

    // Risk Distribution Chart
    const riskCtx = document.getElementById("riskDistributionChart").getContext("2d");
    
    if (riskChart) {
      // Update existing chart
      riskChart.data.datasets[0].data = [lowRisk, mediumRisk, highRisk];
      riskChart.update();
    } else {
      // Create new chart
      riskChart = new Chart(riskCtx, {
        type: "pie",
        data: {
          labels: ["Low Risk (<30%)", "Medium Risk (30-70%)", "High Risk (>70%)"],
          datasets: [
            {
              data: [lowRisk, mediumRisk, highRisk],
              backgroundColor: [
                "rgba(40, 167, 69, 0.7)", // green
                "rgba(255, 193, 7, 0.7)", // yellow
                "rgba(220, 53, 69, 0.7)", // red
              ],
              borderColor: [
                "rgba(40, 167, 69, 1)",
                "rgba(255, 193, 7, 1)",
                "rgba(220, 53, 69, 1)",
              ],
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              position: "bottom",
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  const label = context.label || '';
                  const value = context.raw || 0;
                  const total = context.dataset.data.reduce((a, b) => a + b, 0);
                  const percentage = Math.round((value / total) * 100);
                  return `${label}: ${value} (${percentage}%)`;
                }
              }
            }
          },
        },
      });
    }

    // Sessions by Test Chart
    const testCtx = document.getElementById("testDistributionChart").getContext("2d");
    
    // Prepare test chart data
    const testLabels = [];
    const testData = [];

    Object.values(testCounts).forEach((test) => {
      testLabels.push(test.name);
      testData.push(test.count);
    });

    if (testChart) {
      // Update existing chart
      testChart.data.labels = testLabels;
      testChart.data.datasets[0].data = testData;
      testChart.update();
    } else {
      // Create new chart
      testChart = new Chart(testCtx, {
        type: "bar",
        data: {
          labels: testLabels,
          datasets: [
            {
              label: "Completed Sessions",
              data: testData,
              backgroundColor: "rgba(23, 162, 184, 0.7)",
              borderColor: "rgba(23, 162, 184, 1)",
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          scales: {
            y: {
              beginAtZero: true,
              precision: 0,
              ticks: {
                stepSize: 1
              }
            }
          },
        },
      });
    }
  }

  // Add summary stats at the top of the page
  function updateSummary() {
    const summaryContainer = document.getElementById("dashboard-summary");
    if (!summaryContainer) return;

    // Get visible rows
    const visibleRows = Array.from(tableRows).filter(
      (row) => !row.classList.contains("d-none")
    );

    // Calculate average risk score
    let totalRisk = 0;
    let highRiskCount = 0;

    visibleRows.forEach((row) => {
      const riskScore = parseFloat(row.dataset.risk);
      totalRisk += riskScore;
      if (riskScore >= 0.7) highRiskCount++;
    });

    const avgRisk = visibleRows.length > 0 ? totalRisk / visibleRows.length : 0;
    
    // Update summary elements
    document.getElementById("session-count").textContent = visibleRows.length;
    document.getElementById("avg-risk").textContent = (avgRisk * 100).toFixed(1) + "%";
    document.getElementById("high-risk-count").textContent = highRiskCount;
  }

  // Initialize charts and summary
  updateCharts();
  updateSummary();
}); 