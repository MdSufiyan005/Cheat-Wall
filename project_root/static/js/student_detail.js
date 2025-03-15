/**
 * Student Detail page JavaScript
 */

document.addEventListener("DOMContentLoaded", function () {
  // Get carousel element
  const carousel = document.getElementById("screenshotCarousel");
  const carouselInstance = new bootstrap.Carousel(carousel, {
    interval: false, // Don't auto-slide
  });

  // Track current screenshot index
  let currentIndex = 0;
  const screenshots = document.querySelectorAll(".carousel-item");
  const totalScreenshots = screenshots.length;

  // Update screenshot counter
  const screenshotCounter = document.getElementById("screenshot-counter");
  function updateCounter() {
    if (screenshotCounter) {
      screenshotCounter.textContent = `${
        currentIndex + 1
      } / ${totalScreenshots}`;
    }
  }

  // Load screenshot when it becomes active
  carousel.addEventListener("slide.bs.carousel", function (event) {
    currentIndex = Array.from(screenshots).indexOf(event.relatedTarget);
    updateCounter();
    loadScreenshot(event.relatedTarget);
    updateScreenshotDetails(event.relatedTarget);
  });

  // Initialize with first screenshot
  if (screenshots.length > 0) {
    loadScreenshot(screenshots[0]);
    updateScreenshotDetails(screenshots[0]);
    updateCounter();
  }

  // Function to load a screenshot
  function loadScreenshot(slideElement) {
    const screenshotId = slideElement.dataset.id;
    const loadingSpinner = document.getElementById(`loading-${screenshotId}`);
    const imgElement = slideElement.querySelector(".screenshot-img");
    const openLinkBtn = slideElement.querySelector(".open-image-link");
    const openLinkAnchor = openLinkBtn ? openLinkBtn.querySelector("a") : null;
    const maxRetries = 2;
    let retryCount = 0;

    // Check if already loaded
    if (!imgElement.classList.contains("d-none")) {
      return;
    }

    // Fetch screenshot from the API
    fetch(`/api/screenshot/${screenshotId}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Failed to load screenshot: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        if (data.success) {
          // Set the image source based on whether it's a link or base64 data
          if (data.is_link) {
            // Direct link to image
            imgElement.src = data.image_link;
            
            // Show and set up the open in new tab button
            if (openLinkBtn && openLinkAnchor) {
              openLinkAnchor.href = data.image_link;
              openLinkBtn.classList.remove("d-none");
            }
          } else {
            // Base64 encoded image
            imgElement.src = `data:image/jpeg;base64,${data.image_data}`;
            
            // Hide the link button for base64 images
            if (openLinkBtn) {
              openLinkBtn.classList.add("d-none");
            }
          }

          // Show the image once loaded
          imgElement.onload = function () {
            loadingSpinner.classList.add("d-none");
            imgElement.classList.remove("d-none");
          };
          
          // Handle image loading errors - especially for external links
          imgElement.onerror = function() {
            // Try to retry loading the image a few times
            if (data.is_link && retryCount < maxRetries) {
              retryCount++;
              console.log(`Retrying image load (${retryCount}/${maxRetries}): ${data.image_link}`);
              
              // Add cache-busting parameter to force reload
              const cacheBuster = `?cb=${Date.now()}`;
              imgElement.src = data.image_link + cacheBuster;
              return;
            }
            
            // After retries or for non-link images, show error
            loadingSpinner.classList.add("d-none");
            
            const errorDiv = document.createElement("div");
            errorDiv.className = "alert alert-danger mt-2";
            
            if (data.is_link) {
              errorDiv.innerHTML =
                '<i class="fas fa-exclamation-circle me-2"></i>Failed to load image from external link';
            } else {
              errorDiv.innerHTML =
                '<i class="fas fa-exclamation-circle me-2"></i>Failed to load screenshot image';
            }
            
            slideElement
              .querySelector(".screenshot-container")
              .appendChild(errorDiv);
          };
        }
      })
      .catch((error) => {
        console.error("Error loading screenshot:", error);
        loadingSpinner.classList.add("d-none");
        // Show error message
        const errorDiv = document.createElement("div");
        errorDiv.className = "alert alert-danger mt-2";
        errorDiv.innerHTML =
          '<i class="fas fa-exclamation-circle me-2"></i>Failed to load screenshot data';
        slideElement
          .querySelector(".screenshot-container")
          .appendChild(errorDiv);
      });
  }

  // Function to update screenshot details panel
  function updateScreenshotDetails(slideElement) {
    const timestamp = new Date(slideElement.dataset.timestamp);
    const riskScore = parseFloat(slideElement.dataset.risk);

    // Update details
    document.getElementById("screenshot-time").textContent =
      timestamp.toLocaleString();
    document.getElementById("screenshot-risk").textContent = `${(
      riskScore * 100
    ).toFixed(0)}%`;

    // Update progress bar
    const riskBar = document.getElementById("screenshot-risk-bar");
    riskBar.style.width = `${riskScore * 100}%`;
    riskBar.textContent = `${(riskScore * 100).toFixed(0)}%`;

    // Update bar color
    riskBar.className = "progress-bar";
    if (riskScore < 0.3) {
      riskBar.classList.add("bg-success");
    } else if (riskScore < 0.7) {
      riskBar.classList.add("bg-warning");
    } else {
      riskBar.classList.add("bg-danger");
    }

    // Update analysis text
    const analysisElement = document.getElementById("screenshot-analysis");
    analysisElement.className = "alert mt-2";

    if (riskScore < 0.3) {
      analysisElement.classList.add("alert-success");
      analysisElement.innerHTML =
        '<i class="fas fa-check-circle me-2"></i>No suspicious activity detected.';
    } else if (riskScore < 0.7) {
      analysisElement.classList.add("alert-warning");
      analysisElement.innerHTML =
        '<i class="fas fa-exclamation-circle me-2"></i>Potential suspicious activity detected. Review recommended.';
    } else {
      analysisElement.classList.add("alert-danger");
      analysisElement.innerHTML =
        '<i class="fas fa-exclamation-triangle me-2"></i>High risk activity detected! Immediate review required.';
    }
  }

  // Slideshow functionality
  let slideshowInterval;
  const playButton = document.getElementById("play-slideshow");
  const pauseButton = document.getElementById("pause-slideshow");

  if (playButton && pauseButton) {
    playButton.addEventListener("click", function () {
      // Start slideshow with 2 second intervals
      slideshowInterval = setInterval(() => {
        carouselInstance.next();
      }, 2000);

      // Toggle buttons
      playButton.classList.add("d-none");
      pauseButton.classList.remove("d-none");
    });

    pauseButton.addEventListener("click", function () {
      // Stop slideshow
      clearInterval(slideshowInterval);

      // Toggle buttons
      pauseButton.classList.add("d-none");
      playButton.classList.remove("d-none");
    });
  }

  // Keyboard navigation for screenshots
  document.addEventListener("keydown", function (event) {
    if (event.key === "ArrowLeft") {
      carouselInstance.prev();
    } else if (event.key === "ArrowRight") {
      carouselInstance.next();
    }
  });
});
