---
name: rotating-gallery
description: Create 3D rotating image galleries with CSS transforms and smooth animations. Use when building carousels, image showcases, or product displays with immersive 3D rotation effects.
---

# Rotating Gallery Skill

Expert guidance for creating 3D rotating image galleries using CSS transforms, perspective, and smooth animations. This skill provides complete templates for both vanilla JavaScript and React implementations.

## Overview

The rotating gallery creates an immersive 3D carousel effect where images are positioned on a cylindrical surface that rotates on the Y-axis. Users can manually navigate or watch auto-rotation.

### Core Concepts

**3D Transform Principles:**
- **Perspective**: Creates depth perception by setting viewing distance (typically 1000px)
- **transform-style: preserve-3d**: Maintains 3D space for child elements
- **rotateY()**: Rotates container on vertical axis for carousel effect
- **translateZ()**: Pushes images outward to form cylinder (radius typically 400px)
- **CSS Variables**: `--i` calculates individual image rotation: `calc(var(--i) * rotationAngle)`

**Animation System:**
- CSS transitions handle smooth rotation between states
- JavaScript manages rotation angle state and auto-advance timing
- Manual controls override auto-rotation for user control

## Key Features

- **3D Cylindrical Layout**: Images arranged in circular 3D space
- **Smooth Rotation**: CSS transitions with customizable easing
- **Auto-rotation**: Optional timer-based advancement
- **Manual Controls**: Previous/Next buttons for user control
- **Flexible Image Count**: Automatically calculates angles for any number of images
- **Responsive Design**: Scales appropriately for different viewport sizes

## When to Use

Use this skill when building:
- Product showcases with 360-degree rotation
- Photo galleries requiring immersive presentation
- Portfolio displays with premium aesthetic
- Image carousels that stand out from standard sliders
- Any interface where depth and dimension enhance the experience

## Templates

### Vanilla JavaScript
See `assets/vanilla-template.md` for complete HTML/CSS/JS implementation.

**Key customization points:**
- Number of images (automatically calculates rotation angle)
- Cylinder radius (translateZ value)
- Auto-rotation interval
- Animation duration and easing

### React/TypeScript
See `assets/react-template.md` for Next.js compatible component.

**Props interface:**
```typescript
interface RotatingGalleryProps {
  images: { src: string; alt: string }[];
  rotationSpeed?: number;        // degrees per click (default: 45)
  autoRotate?: boolean;          // enable auto-rotation (default: true)
  autoRotateInterval?: number;   // ms between rotations (default: 3000)
  cylinderRadius?: number;       // translateZ distance (default: 400)
}
```

## Customization Parameters

### Rotation Angle Calculation
For N images: `angle = 360 / N` degrees

Examples:
- 8 images = 45° per image
- 6 images = 60° per image
- 12 images = 30° per image

### Cylinder Radius
Controls how "spread out" images appear:
- Smaller radius (250-350px): Tighter, more compact
- Default radius (400px): Balanced, natural spacing
- Larger radius (450-600px): Wider, more dramatic

### Animation Timing
- **Transition duration**: 0.5-1.5s (CSS `transition` property)
- **Auto-rotate interval**: 2000-5000ms (JavaScript timer)
- **Easing function**: `ease-in-out` (smooth), `cubic-bezier()` (custom)

## Implementation Guide

1. **Choose your template** - Vanilla for standalone pages, React for component integration
2. **Customize parameters** - Adjust rotation angles, radius, timing to match design
3. **Prepare images** - Optimize sizes (recommend 800x600 or similar aspect ratio)
4. **Test responsiveness** - Verify appearance on mobile, tablet, desktop
5. **Add accessibility** - Include pause button, keyboard navigation if needed

## Advanced Patterns

See `references/customization.md` for:
- Vertical rotation (rotateX instead of rotateY)
- Responsive sizing strategies
- Touch gesture support for mobile
- Accessibility enhancements
- Performance optimization for large image sets
- Nested galleries and multi-axis rotation

## Browser Compatibility

- Modern browsers (Chrome, Firefox, Safari, Edge) fully support CSS 3D transforms
- Mobile browsers support touch interaction with appropriate event handlers
- Graceful degradation: provide fallback for browsers without 3D transform support

## Performance Considerations

- **GPU Acceleration**: `transform` and `opacity` are GPU-accelerated for smooth animations
- **Image Optimization**: Use appropriately sized images (avoid 4K images in web galleries)
- **Lazy Loading**: Consider loading images "behind" the visible face on demand
- **Mobile Performance**: Limit to 8-10 images on mobile devices for optimal performance

## Accessibility

- Provide pause/play controls for auto-rotation (WCAG 2.2.2)
- Ensure keyboard navigation works (arrow keys or tab + enter)
- Add proper alt text to all images
- Consider reduced motion preferences with `prefers-reduced-motion` media query

## License

This skill provides implementation guidance. The rotating gallery pattern is a common web technique. Ensure any images used respect copyright and licensing requirements.
