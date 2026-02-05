# Vanilla JavaScript Rotating Gallery Template

Complete HTML/CSS/JavaScript implementation of a 3D rotating image gallery. Copy and customize this template for standalone pages or vanilla JavaScript projects.

## Complete Implementation

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Rotating Gallery</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            /* Center the gallery on the page */
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        }

        /* CUSTOMIZE: Container for the entire gallery */
        .gallery-wrapper {
            position: relative;
            width: 90%;
            max-width: 1200px;
            padding: 40px 20px;
        }

        /* CUSTOMIZE: Main 3D container with perspective */
        .image-container {
            position: relative;
            width: 100%;
            height: 500px;
            /* Perspective creates depth - higher values = less dramatic */
            transform-style: preserve-3d;
            perspective: 1000px;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        /* CUSTOMIZE: Inner rotating element */
        .image-container .rotation-wrapper {
            position: relative;
            width: 100%;
            height: 100%;
            transform-style: preserve-3d;
            /* Initial rotation - will be updated by JavaScript */
            transform: rotateY(0deg);
            /* Smooth transitions between rotations */
            transition: transform 1s ease-in-out;
        }

        /* CUSTOMIZE: Individual image positioning */
        .image-container .rotation-wrapper span {
            position: absolute;
            top: 50%;
            left: 50%;
            width: 400px;
            height: 300px;
            /* Transform origin at center for proper rotation */
            transform-origin: center;
            transform-style: preserve-3d;
            /*
                This is the key formula:
                - rotateY(calc(var(--i) * 45deg)) positions image around circle
                - translateZ(400px) pushes image outward to form cylinder
                - Higher translateZ = wider cylinder
            */
            transform:
                translate(-50%, -50%)
                rotateY(calc(var(--i) * 45deg))
                translateZ(400px);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
        }

        /* CUSTOMIZE: Image styling */
        .image-container .rotation-wrapper span img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 12px;
        }

        /* CUSTOMIZE: Navigation buttons container */
        .btn-container {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 20px;
            margin-top: 60px;
        }

        /* CUSTOMIZE: Button styling */
        .btn-container button {
            padding: 15px 35px;
            font-size: 16px;
            font-weight: 600;
            border: none;
            border-radius: 8px;
            background: white;
            color: #667eea;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }

        .btn-container button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
            background: #f8f9fa;
        }

        .btn-container button:active {
            transform: translateY(0);
        }

        /* CUSTOMIZE: Pause button styling */
        .btn-container button.pause-btn {
            background: #764ba2;
            color: white;
        }

        .btn-container button.pause-btn:hover {
            background: #5c3a7e;
        }

        /* CUSTOMIZE: Responsive adjustments */
        @media (max-width: 768px) {
            .image-container {
                height: 350px;
            }

            .image-container .rotation-wrapper span {
                width: 280px;
                height: 210px;
                /* Smaller cylinder for mobile */
                transform:
                    translate(-50%, -50%)
                    rotateY(calc(var(--i) * 45deg))
                    translateZ(280px);
            }

            .btn-container button {
                padding: 12px 24px;
                font-size: 14px;
            }
        }

        /* Accessibility: Reduced motion support */
        @media (prefers-reduced-motion: reduce) {
            .image-container .rotation-wrapper {
                transition: none;
            }
        }
    </style>
</head>
<body>
    <div class="gallery-wrapper">
        <!-- 3D Image Container -->
        <div class="image-container">
            <div class="rotation-wrapper" id="rotationWrapper">
                <!--
                    CUSTOMIZE: Add your images here
                    The --i CSS variable determines position (1, 2, 3, etc.)
                    For N images, rotation angle = 360 / N degrees
                    8 images = 45deg (as shown)
                    6 images = 60deg (change in CSS to calc(var(--i) * 60deg))
                    12 images = 30deg (change in CSS to calc(var(--i) * 30deg))
                -->
                <span style="--i: 1">
                    <img src="https://picsum.photos/400/300?random=1" alt="Gallery image 1">
                </span>
                <span style="--i: 2">
                    <img src="https://picsum.photos/400/300?random=2" alt="Gallery image 2">
                </span>
                <span style="--i: 3">
                    <img src="https://picsum.photos/400/300?random=3" alt="Gallery image 3">
                </span>
                <span style="--i: 4">
                    <img src="https://picsum.photos/400/300?random=4" alt="Gallery image 4">
                </span>
                <span style="--i: 5">
                    <img src="https://picsum.photos/400/300?random=5" alt="Gallery image 5">
                </span>
                <span style="--i: 6">
                    <img src="https://picsum.photos/400/300?random=6" alt="Gallery image 6">
                </span>
                <span style="--i: 7">
                    <img src="https://picsum.photos/400/300?random=7" alt="Gallery image 7">
                </span>
                <span style="--i: 8">
                    <img src="https://picsum.photos/400/300?random=8" alt="Gallery image 8">
                </span>
            </div>
        </div>

        <!-- Navigation Controls -->
        <div class="btn-container">
            <button id="prev" aria-label="Previous image">Previous</button>
            <button id="pause" class="pause-btn" aria-label="Pause auto-rotation">Pause</button>
            <button id="next" aria-label="Next image">Next</button>
        </div>
    </div>

    <script>
        // CUSTOMIZE: Gallery configuration
        const config = {
            imageCount: 8,              // Total number of images
            rotationAngle: 45,          // Degrees per image (360 / imageCount)
            autoRotateInterval: 3000,   // Milliseconds between auto-rotations
            transitionDuration: 1000    // Must match CSS transition duration
        };

        // State management
        let currentRotation = 0;
        let autoRotateTimer = null;
        let isAutoRotating = true;

        // Get DOM elements
        const rotationWrapper = document.getElementById('rotationWrapper');
        const prevBtn = document.getElementById('prev');
        const nextBtn = document.getElementById('next');
        const pauseBtn = document.getElementById('pause');

        /**
         * Updates the rotation of the gallery
         * @param {number} angle - Rotation angle in degrees
         */
        function updateRotation(angle) {
            currentRotation = angle;
            rotationWrapper.style.transform = `rotateY(${angle}deg)`;
        }

        /**
         * Rotates to the next image
         */
        function rotateNext() {
            currentRotation -= config.rotationAngle;
            updateRotation(currentRotation);
        }

        /**
         * Rotates to the previous image
         */
        function rotatePrev() {
            currentRotation += config.rotationAngle;
            updateRotation(currentRotation);
        }

        /**
         * Starts auto-rotation timer
         */
        function startAutoRotation() {
            if (!isAutoRotating) return;

            stopAutoRotation(); // Clear any existing timer
            autoRotateTimer = setInterval(() => {
                rotateNext();
            }, config.autoRotateInterval);
        }

        /**
         * Stops auto-rotation timer
         */
        function stopAutoRotation() {
            if (autoRotateTimer) {
                clearInterval(autoRotateTimer);
                autoRotateTimer = null;
            }
        }

        /**
         * Toggles auto-rotation on/off
         */
        function toggleAutoRotation() {
            isAutoRotating = !isAutoRotating;

            if (isAutoRotating) {
                pauseBtn.textContent = 'Pause';
                pauseBtn.setAttribute('aria-label', 'Pause auto-rotation');
                startAutoRotation();
            } else {
                pauseBtn.textContent = 'Play';
                pauseBtn.setAttribute('aria-label', 'Resume auto-rotation');
                stopAutoRotation();
            }
        }

        // Event Listeners
        prevBtn.addEventListener('click', () => {
            rotatePrev();
            // Reset auto-rotation timer on manual interaction
            if (isAutoRotating) {
                startAutoRotation();
            }
        });

        nextBtn.addEventListener('click', () => {
            rotateNext();
            // Reset auto-rotation timer on manual interaction
            if (isAutoRotating) {
                startAutoRotation();
            }
        });

        pauseBtn.addEventListener('click', toggleAutoRotation);

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') {
                rotatePrev();
                if (isAutoRotating) startAutoRotation();
            } else if (e.key === 'ArrowRight') {
                rotateNext();
                if (isAutoRotating) startAutoRotation();
            } else if (e.key === ' ' || e.key === 'Enter') {
                e.preventDefault();
                toggleAutoRotation();
            }
        });

        // Initialize auto-rotation
        startAutoRotation();

        // Cleanup on page unload
        window.addEventListener('beforeunload', stopAutoRotation);
    </script>
</body>
</html>
```

## Customization Quick Guide

### Change Number of Images

1. Update the `imageCount` in config (JavaScript)
2. Calculate new angle: `360 / imageCount`
3. Update `rotationAngle` in config
4. Update CSS: `calc(var(--i) * NEWdeg)`
5. Add/remove `<span>` elements with appropriate `--i` values

### Adjust Cylinder Size

Change `translateZ(400px)` in the CSS:
- Smaller value (200-350px): Tighter, more compact
- Larger value (450-600px): Wider, more spread out

### Modify Animation Speed

- CSS: Change `transition: transform 1s` to deparentAd duration
- JavaScript: Update `transitionDuration` to match
- Auto-rotate: Change `autoRotateInterval` (in milliseconds)

### Change Background/Styling

All visual styling is in the `<style>` section - customize colors, shadows, borders, etc.

## Tips

- Keep image dimensions consistent for best appearance
- Test on mobile devices and adjust `translateZ` in media query
- Add loading states if images are large
- Consider lazy loading for galleries with many images
- Use optimized image formats (WebP with fallbacks)
