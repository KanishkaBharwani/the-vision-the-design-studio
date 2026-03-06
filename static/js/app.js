// --- Slideshow Functionality (FINAL, VERIFIED CODE) ---

function startSlideshow() {
    // CRITICAL: Use a document-wide query that is less likely to fail
    const slides = document.querySelectorAll('.slideshow-slide'); 
    
    // Safety check: exit if not enough slides
    if (slides.length < 2) return; 

    let currentSlide = 0;

    // 1. Ensure the very first slide is visible initially
    slides[0].classList.add('active-slide');

    function nextSlide() {
        // Remove active class from the current slide
        slides[currentSlide].classList.remove('active-slide');
        
        // Move to the next slide (circular loop)
        currentSlide = (currentSlide + 1) % slides.length;
        
        // Add active class to the new slide
        slides[currentSlide].classList.add('active-slide');
    }

    // Start the transition interval
    setInterval(nextSlide, 5000); // Change slide every 5 seconds
}

// CRITICAL FIX: Use window.onload to wait for ALL content (including CSS)
window.onload = function() {
    // Only run on pages that have the slideshow element
    if (document.querySelector('.page-hero-slideshow')) {
        startSlideshow();
    }
};