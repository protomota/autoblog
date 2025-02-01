console.log('Gallery.js: Image gallery script loaded');

document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.gallery-container');
    const images = document.querySelectorAll('.gallery-image');
    const dots = document.querySelectorAll('.dot');
    const prevButton = document.querySelector('.prev-button');
    const nextButton = document.querySelector('.next-button');
    let currentIndex = 0;
    
    // Function to update container height based on current image
    function updateContainerHeight(image) {
        console.log('Updating container height for image:', image.src);
        console.log('Natural dimensions:', image.naturalWidth, 'x', image.naturalHeight);
        
        if (image.complete) {
            const containerWidth = container.offsetWidth;
            const aspectRatio = image.naturalHeight / image.naturalWidth;
            container.style.height = `${containerWidth * aspectRatio}px`;
        } else {
            image.onload = function() {
                const containerWidth = container.offsetWidth;
                const aspectRatio = image.naturalHeight / image.naturalWidth;
                container.style.height = `${containerWidth * aspectRatio}px`;
            }
        }
    }
    
    // Initialize with first image
    if (images.length > 0) {
        showImage(0);
    }
    
    function showImage(index) {
        images.forEach(img => img.classList.remove('active'));
        dots.forEach(dot => dot.classList.remove('active'));
        
        images[index].classList.add('active');
        dots[index].classList.add('active');
        currentIndex = index;
        
        updateContainerHeight(images[index]);
    }
    
    function nextImage() {
        const nextIndex = (currentIndex + 1) % images.length;
        showImage(nextIndex);
    }
    
    function prevImage() {
        const prevIndex = (currentIndex - 1 + images.length) % images.length;
        showImage(prevIndex);
    }
    
    // Set up click handlers
    nextButton.addEventListener('click', nextImage);
    prevButton.addEventListener('click', prevImage);
    
    dots.forEach((dot, index) => {
        dot.addEventListener('click', () => showImage(index));
    });
    
    // Auto advance every 3 seconds
    setInterval(nextImage, 3000);
});