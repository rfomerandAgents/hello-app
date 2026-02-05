# Rotating Gallery Customization Reference

Advanced patterns, customization options, and implementation details for the rotating gallery skill.

## Table of Contents

1. [Rotation Angle Calculation](#rotation-angle-calculation)
2. [Cylinder Radius Adjustment](#cylinder-radius-adjustment)
3. [Animation Timing](#animation-timing)
4. [Responsive Design Strategies](#responsive-design-strategies)
5. [Touch Gesture Support](#touch-gesture-support)
6. [Accessibility Enhancements](#accessibility-enhancements)
7. [Performance Optimization](#performance-optimization)
8. [Advanced Patterns](#advanced-patterns)

---

## Rotation Angle Calculation

### Basic Formula

For N images uniformly distributed around a circle:

```
rotationAngle = 360 / N degrees
```

### Common Configurations

| Image Count | Angle per Image | Visual Result |
|-------------|-----------------|---------------|
| 3 images    | 120°            | Triangle formation |
| 4 images    | 90°             | Square formation |
| 6 images    | 60°             | Hexagon formation |
| 8 images    | 45°             | Octagon (default) |
| 10 images   | 36°             | Decagon |
| 12 images   | 30°             | Dodecagon |

### Implementation

**CSS (Vanilla):**
```css
/* For 8 images */
.image-container .rotation-wrapper span {
    transform:
        translate(-50%, -50%)
        rotateY(calc(var(--i) * 45deg))
        translateZ(400px);
}
```

**JavaScript (Vanilla):**
```javascript
const imageCount = 8
const rotationAngle = 360 / imageCount  // 45 degrees
```

**React/TypeScript:**
```tsx
const imageCount = images.length
const rotationAngle = 360 / imageCount

// Applied in render:
style={{
  transform: `
    translate(-50%, -50%)
    rotateY(${index * rotationAngle}deg)
    translateZ(${cylinderRadius}px)
  `
}}
```

### Odd Number Considerations

Odd numbers of images (3, 5, 7, 9, etc.) create asymmetrical visual balance:

- **3 images**: Works well, creates triangular composition
- **5 images**: Can feel unbalanced; consider adding visual weight to bottom
- **7 images**: Similar to 5; may want to adjust camera angle
- **9+ odd images**: Less noticeable imbalance with higher counts

**Solution**: Add a subtle background or adjust the perspective origin to create visual stability.

---

## Cylinder Radius Adjustment

The `translateZ` value determines the radius of the cylinder, affecting spacing and depth.

### Radius Guidelines

| Radius (px) | Best For | Visual Effect |
|-------------|----------|---------------|
| 200-300     | 4-6 images, mobile devices | Compact, images appear closer |
| 350-400     | 6-8 images, standard desktop | Balanced, natural spacing |
| 450-550     | 8-12 images, large screens | Dramatic, wide spacing |
| 600+        | 12+ images, immersive displays | Very wide, immersive |

### Calculating Optimal Radius

For images of width W, optimal radius prevents overlap:

```
radius = (W / 2) / tan(rotationAngle / 2)
```

Example for 400px wide images with 8 images (45° rotation):
```
radius = (400 / 2) / tan(45° / 2)
radius = 200 / tan(22.5°)
radius ≈ 200 / 0.414
radius ≈ 483px
```

### Implementation

**CSS:**
```css
/* Adjust translateZ value */
transform:
    translate(-50%, -50%)
    rotateY(calc(var(--i) * 45deg))
    translateZ(500px);  /* Increased from 400px */
```

**React:**
```tsx
<RotatingGallery
  images={images}
  cylinderRadius={500}  // Wider cylinder
/>
```

### Responsive Radius

Scale radius based on viewport:

```css
@media (max-width: 768px) {
    transform:
        translate(-50%, -50())
        rotateY(calc(var(--i) * 45deg))
        translateZ(280px);  /* Smaller for mobile */
}
```

```tsx
// React with custom hook
const useResponsiveRadius = () => {
  const [radius, setRadius] = useState(400)

  useEffect(() => {
    const updateRadius = () => {
      if (window.innerWidth < 768) {
        setRadius(280)
      } else if (window.innerWidth < 1024) {
        setRadius(350)
      } else {
        setRadius(400)
      }
    }

    updateRadius()
    window.addEventListener('resize', updateRadius)
    return () => window.removeEventListener('resize', updateRadius)
  }, [])

  return radius
}
```

---

## Animation Timing

### CSS Transition Properties

**Duration**: How long the rotation takes
```css
transition: transform 1s ease-in-out;
```

**Timing Functions**:
- `linear`: Constant speed (mechanical feel)
- `ease`: Slow start, fast middle, slow end (default)
- `ease-in-out`: Smooth acceleration and deceleration (recommended)
- `cubic-bezier(0.4, 0, 0.2, 1)`: Custom easing (Material Design)

### Advanced Timing Examples

**Bouncy rotation:**
```css
transition: transform 0.8s cubic-bezier(0.68, -0.55, 0.265, 1.55);
```

**Sharp, snappy:**
```css
transition: transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
```

**Smooth and elastic:**
```css
transition: transform 1.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
```

### Auto-Rotation Timing

Balance between viewing time and engagement:

| Interval (ms) | Use Case |
|---------------|----------|
| 1500-2000     | Quick showcase, many images |
| 2500-3000     | Standard gallery (recommended) |
| 4000-5000     | Detailed images, fewer items |
| 6000+         | Slow, contemplative viewing |

### Synchronized Animations

Coordinate rotation with other animations:

```tsx
const [currentRotation, setCurrentRotation] = useState(0)
const [fadeOpacity, setFadeOpacity] = useState(1)

const rotateNext = () => {
  // Fade out
  setFadeOpacity(0)

  // Rotate after brief delay
  setTimeout(() => {
    setCurrentRotation(prev => prev - rotationAngle)
  }, 200)

  // Fade in
  setTimeout(() => {
    setFadeOpacity(1)
  }, 300)
}
```

---

## Responsive Design Strategies

### Breakpoint-Based Scaling

```css
/* Mobile: Smaller, tighter */
@media (max-width: 640px) {
    .image-container {
        height: 250px;
    }
    .image-container span {
        width: 200px;
        height: 150px;
        transform:
            translate(-50%, -50%)
            rotateY(calc(var(--i) * 45deg))
            translateZ(200px);
    }
}

/* Tablet: Medium size */
@media (min-width: 641px) and (max-width: 1024px) {
    .image-container {
        height: 400px;
    }
    .image-container span {
        width: 320px;
        height: 240px;
        transform:
            translate(-50%, -50%)
            rotateY(calc(var(--i) * 45deg))
            translateZ(320px);
    }
}

/* Desktop: Full size */
@media (min-width: 1025px) {
    .image-container {
        height: 500px;
    }
    .image-container span {
        width: 400px;
        height: 300px;
        transform:
            translate(-50%, -50%)
            rotateY(calc(var(--i) * 45deg))
            translateZ(400px);
    }
}
```

### Container-Based Sizing

Use CSS container queries (modern browsers):

```css
@container (max-width: 600px) {
    .image-container span {
        width: 250px;
        height: 187px;
        transform:
            translate(-50%, -50%)
            rotateY(calc(var(--i) * 45deg))
            translateZ(250px);
    }
}
```

### Viewport-Relative Units

Scale with viewport width:

```css
.image-container span {
    width: clamp(250px, 30vw, 400px);
    height: clamp(187px, 22.5vw, 300px);
    transform:
        translate(-50%, -50%)
        rotateY(calc(var(--i) * 45deg))
        translateZ(clamp(250px, 30vw, 400px));
}
```

---

## Touch Gesture Support

Add swipe gestures for mobile devices.

### Vanilla JavaScript Implementation

```javascript
let touchStartX = 0
let touchEndX = 0
let touchStartY = 0

const rotationWrapper = document.getElementById('rotationWrapper')

rotationWrapper.addEventListener('touchstart', (e) => {
    touchStartX = e.changedTouches[0].screenX
    touchStartY = e.changedTouches[0].screenY
}, { passive: true })

rotationWrapper.addEventListener('touchend', (e) => {
    touchEndX = e.changedTouches[0].screenX
    const touchEndY = e.changedTouches[0].screenY

    const deltaX = touchEndX - touchStartX
    const deltaY = Math.abs(touchEndY - touchStartY)

    // Only handle horizontal swipes (not vertical scrolling)
    if (Math.abs(deltaX) > 50 && deltaY < 50) {
        if (deltaX > 0) {
            rotatePrev()  // Swipe right
        } else {
            rotateNext()  // Swipe left
        }

        // Reset auto-rotation timer
        if (isAutoRotating) {
            startAutoRotation()
        }
    }
}, { passive: true })
```

### React Implementation

```tsx
import { useRef, useState } from 'react'

export default function RotatingGallery({ images, ...props }: RotatingGalleryProps) {
  const touchStartX = useRef(0)
  const touchStartY = useRef(0)

  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.changedTouches[0].screenX
    touchStartY.current = e.changedTouches[0].screenY
  }

  const handleTouchEnd = (e: React.TouchEvent) => {
    const touchEndX = e.changedTouches[0].screenX
    const touchEndY = e.changedTouches[0].screenY

    const deltaX = touchEndX - touchStartX.current
    const deltaY = Math.abs(touchEndY - touchStartY.current)

    // Horizontal swipe with minimal vertical movement
    if (Math.abs(deltaX) > 50 && deltaY < 50) {
      if (deltaX > 0) {
        handleManualRotation('prev')
      } else {
        handleManualRotation('next')
      }
    }
  }

  return (
    <div
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      {/* Gallery content */}
    </div>
  )
}
```

### Advanced Touch: Drag to Rotate

Allow continuous rotation by dragging:

```tsx
const handleTouchMove = (e: React.TouchEvent) => {
  if (!isDragging) return

  const currentX = e.changedTouches[0].screenX
  const deltaX = currentX - lastTouchX.current

  // Rotate proportional to drag distance
  const rotationDelta = deltaX * 0.5  // Adjust sensitivity
  setCurrentRotation(prev => prev + rotationDelta)

  lastTouchX.current = currentX
}
```

---

## Accessibility Enhancements

### Keyboard Navigation

Full keyboard support implementation:

```javascript
document.addEventListener('keydown', (e) => {
    switch(e.key) {
        case 'ArrowLeft':
            e.preventDefault()
            rotatePrev()
            break
        case 'ArrowRight':
            e.preventDefault()
            rotateNext()
            break
        case ' ':  // Spacebar
        case 'Enter':
            e.preventDefault()
            toggleAutoRotation()
            break
        case 'Home':
            e.preventDefault()
            resetToFirst()
            break
        case 'End':
            e.preventDefault()
            rotateToLast()
            break
    }
})
```

### ARIA Attributes

```html
<div
    class="image-container"
    role="region"
    aria-label="3D rotating image gallery"
    aria-live="polite"
>
    <div class="rotation-wrapper">
        <span
            role="img"
            aria-label="Gallery image 1 of 8"
            tabindex="0"
        >
            <img src="..." alt="Descriptive alt text">
        </span>
    </div>
</div>

<div class="btn-container" role="group" aria-label="Gallery controls">
    <button aria-label="View previous image">Previous</button>
    <button aria-label="Pause automatic rotation">Pause</button>
    <button aria-label="View next image">Next</button>
</div>
```

### Screen Reader Support

Announce current image:

```javascript
const announceCurrentImage = (imageIndex) => {
    const announcement = document.createElement('div')
    announcement.setAttribute('role', 'status')
    announcement.setAttribute('aria-live', 'polite')
    announcement.textContent = `Now showing image ${imageIndex + 1} of ${imageCount}`
    announcement.style.position = 'absolute'
    announcement.style.left = '-10000px'

    document.body.appendChild(announcement)

    setTimeout(() => {
        document.body.removeChild(announcement)
    }, 1000)
}
```

### Reduced Motion

Respect user preferences:

```css
@media (prefers-reduced-motion: reduce) {
    .rotation-wrapper {
        transition: none !important;
    }

    /* Show all images in a grid instead */
    .image-container.reduced-motion .rotation-wrapper span {
        position: static;
        transform: none;
        display: inline-block;
        margin: 10px;
    }
}
```

---

## Performance Optimization

### Lazy Loading Images

Only load images when needed:

```javascript
const observerOptions = {
    root: null,
    threshold: 0.1
}

const imageObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const img = entry.target
            img.src = img.dataset.src
            img.removeAttribute('data-src')
            imageObserver.unobserve(img)
        }
    })
}, observerOptions)

// Apply to images
document.querySelectorAll('img[data-src]').forEach(img => {
    imageObserver.observe(img)
})
```

### GPU Acceleration

Force GPU acceleration for smoother animations:

```css
.rotation-wrapper {
    transform: translateZ(0);  /* Force GPU layer */
    will-change: transform;     /* Hint to browser */
    backface-visibility: hidden;  /* Prevent flicker */
}

/* Remove will-change after animation completes */
.rotation-wrapper.animating {
    will-change: transform;
}

.rotation-wrapper.static {
    will-change: auto;
}
```

### Reduce Repaints

Minimize layout thrashing:

```javascript
// Bad: Forces multiple reflows
images.forEach(img => {
    img.style.transform = getComputedTransform(img)
})

// Good: Batch read, then batch write
const transforms = images.map(img => getComputedTransform(img))
images.forEach((img, i) => {
    img.style.transform = transforms[i]
})
```

### Debounce Resize Events

```javascript
let resizeTimer
window.addEventListener('resize', () => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => {
        updateGalleryDimensions()
    }, 250)
})
```

---

## Advanced Patterns

### Vertical Rotation

Rotate on X-axis instead of Y-axis:

```css
/* Change rotateY to rotateX */
.rotation-wrapper {
    transform: rotateX(0deg);  /* Instead of rotateY */
}

.rotation-wrapper span {
    transform:
        translate(-50%, -50%)
        rotateX(calc(var(--i) * 45deg))  /* Instead of rotateY */
        translateZ(400px);
}
```

### Nested Galleries

Gallery within a gallery:

```html
<div class="outer-gallery">
    <div class="rotation-wrapper" id="outerRotation">
        <div class="gallery-face" style="--i: 1">
            <div class="inner-gallery">
                <!-- Nested rotating gallery -->
            </div>
        </div>
    </div>
</div>
```

### Multi-Axis Rotation

Combine X and Y rotation:

```javascript
let rotationX = 0
let rotationY = 0

function updateRotation() {
    rotationWrapper.style.transform = `
        rotateX(${rotationX}deg)
        rotateY(${rotationY}deg)
    `
}

// Allow tilting with arrow keys
document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowUp') rotationX += 10
    if (e.key === 'ArrowDown') rotationX -= 10
    if (e.key === 'ArrowLeft') rotationY += 45
    if (e.key === 'ArrowRight') rotationY -= 45
    updateRotation()
})
```

### Image Preview Modal

Click to expand:

```tsx
const [selectedImage, setSelectedImage] = useState<number | null>(null)

return (
  <>
    <div onClick={() => setSelectedImage(currentImageIndex)}>
      {/* Gallery */}
    </div>

    {selectedImage !== null && (
      <Modal onClose={() => setSelectedImage(null)}>
        <img src={images[selectedImage].src} alt={images[selectedImage].alt} />
      </Modal>
    )}
  </>
)
```

### Progress Indicator

Show current position:

```tsx
<div className="progress-dots">
  {images.map((_, index) => (
    <button
      key={index}
      className={index === currentIndex ? 'active' : ''}
      onClick={() => rotateToIndex(index)}
      aria-label={`Go to image ${index + 1}`}
    />
  ))}
</div>
```

### Automatic Rotation Speed Adjustment

Slower for more images:

```javascript
const calculateInterval = (imageCount) => {
    // More images = longer interval to give viewing time
    const baseInterval = 2000
    const additionalTime = (imageCount - 4) * 200
    return Math.max(baseInterval, baseInterval + additionalTime)
}

const autoRotateInterval = calculateInterval(images.length)
```

---

## Edge Case Handling

### Single Image

```tsx
if (images.length === 1) {
    return <img src={images[0].src} alt={images[0].alt} />
}
```

### Two Images

```javascript
// Use 180° rotation for 2 images
const rotationAngle = images.length === 2 ? 180 : 360 / images.length
```

### Empty Gallery

```tsx
if (images.length === 0) {
    return <div>No images to display</div>
}
```

### Image Load Errors

```tsx
<img
    src={image.src}
    alt={image.alt}
    onError={(e) => {
        e.currentTarget.src = '/placeholder-image.jpg'
    }}
/>
```

### Browser Compatibility Fallback

```javascript
// Check for 3D transform support
const supports3D = () => {
    const el = document.createElement('div')
    return 'perspective' in el.style ||
           'WebkitPerspective' in el.style
}

if (!supports3D()) {
    // Fall back to 2D slider
    renderFallbackSlider()
}
```

---

## Testing Checklist

- [ ] Works with different image counts (3, 4, 6, 8, 12)
- [ ] Smooth animation on all devices
- [ ] Auto-rotation starts and stops correctly
- [ ] Manual controls override auto-rotation appropriately
- [ ] Keyboard navigation works (arrows, space, enter)
- [ ] Touch gestures work on mobile (swipe left/right)
- [ ] Reduced motion preference respected
- [ ] ARIA labels present and correct
- [ ] Images load correctly, handle errors gracefully
- [ ] No layout shift or content jump
- [ ] Performs well on low-end devices
- [ ] Accessible to screen readers
- [ ] Responsive at all breakpoints

---

## Troubleshooting

### Images appear flat (no 3D effect)

**Cause**: Missing `perspective` or `transform-style: preserve-3d`

**Solution**:
```css
.image-container {
    perspective: 1000px;
}

.rotation-wrapper {
    transform-style: preserve-3d;
}
```

### Images overlap

**Cause**: `translateZ` value too small for image width and count

**Solution**: Increase `translateZ` value or reduce image width

### Choppy animation

**Cause**: Too many images or images too large

**Solution**:
- Optimize image sizes
- Use GPU acceleration
- Reduce image count on mobile
- Use `will-change: transform`

### Auto-rotation doesn't stop

**Cause**: Timer not cleared properly

**Solution**: Always clear timer in cleanup:
```javascript
useEffect(() => {
    // ... timer setup
    return () => {
        if (timerRef.current) {
            clearInterval(timerRef.current)
        }
    }
}, [dependencies])
```
