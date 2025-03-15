/**
 * Dashboard specific JavaScript
 */

document.addEventListener("DOMContentLoaded", function () {
  // Active sessions count
  const activeSessions = document.querySelector(".active-sessions");
  if (activeSessions) {
    // If we have live updates, this could be implemented
    // For now, it's just static from server data
  }

  // Risk score progress bars
  const progressBars = document.querySelectorAll(".progress-bar");
  progressBars.forEach((bar) => {
    const value = parseFloat(bar.getAttribute("aria-valuenow"));

    // Animate progress bars
    let currentWidth = 0;
    const targetWidth = value;
    const duration = 1000; // 1 second animation
    const interval = 10; // Update every 10ms
    const step = targetWidth / (duration / interval);

    const animation = setInterval(() => {
      currentWidth += step;
      if (currentWidth >= targetWidth) {
        currentWidth = targetWidth;
        clearInterval(animation);
      }
      bar.style.width = `${currentWidth}%`;
    }, interval);
  });

  // Handle card hover effects
  const cards = document.querySelectorAll(".card");
  cards.forEach((card) => {
    card.addEventListener("mouseenter", function () {
      card.classList.add("shadow-lg");
    });

    card.addEventListener("mouseleave", function () {
      card.classList.remove("shadow-lg");
    });
  });
});
