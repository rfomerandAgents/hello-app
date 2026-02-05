# React/TypeScript Rotating Gallery Template

Production-ready React component with TypeScript for Next.js applications. Includes proper hooks, cleanup, and customization options.

## Complete Component Implementation

```tsx
'use client'

import { useState, useEffect, useRef } from 'react'

/**
 * Configuration for individual gallery images
 */
interface GalleryImage {
  src: string
  alt: string
}

/**
 * Props for the RotatingGallery component
 */
interface RotatingGalleryProps {
  /** Array of images to display in the gallery */
  images: GalleryImage[]
  /** Degrees to rotate per click (default: calculated from image count) */
  rotationSpeed?: number
  /** Enable automatic rotation (default: true) */
  autoRotate?: boolean
  /** Milliseconds between auto-rotations (default: 3000) */
  autoRotateInterval?: number
  /** Cylinder radius in pixels (default: 400) */
  cylinderRadius?: number
  /** CSS class for the wrapper element */
  className?: string
}

/**
 * RotatingGallery Component
 *
 * Creates a 3D rotating carousel using CSS transforms.
 * Images are arranged in a cylindrical formation and rotate on the Y-axis.
 *
 * @example
 * ```tsx
 * <RotatingGallery
 *   images={[
 *     { src: '/images/1.jpg', alt: 'Image 1' },
 *     { src: '/images/2.jpg', alt: 'Image 2' },
 *   ]}
 *   autoRotate={true}
 *   autoRotateInterval={3000}
 * />
 * ```
 */
export default function RotatingGallery({
  images,
  rotationSpeed,
  autoRotate = true,
  autoRotateInterval = 3000,
  cylinderRadius = 400,
  className = '',
}: RotatingGalleryProps) {
  // Calculate rotation angle based on image count
  const imageCount = images.length
  const defaultRotationSpeed = 360 / imageCount
  const rotationAngle = rotationSpeed || defaultRotationSpeed

  // State for current rotation angle
  const [currentRotation, setCurrentRotation] = useState(0)

  // State for auto-rotation control
  const [isAutoRotating, setIsAutoRotating] = useState(autoRotate)

  // Ref for storing timer to ensure proper cleanup
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  /**
   * Rotates the gallery to the next image
   */
  const rotateNext = () => {
    setCurrentRotation((prev) => prev - rotationAngle)
  }

  /**
   * Rotates the gallery to the previous image
   */
  const rotatePrev = () => {
    setCurrentRotation((prev) => prev + rotationAngle)
  }

  /**
   * Toggles auto-rotation on/off
   */
  const toggleAutoRotation = () => {
    setIsAutoRotating((prev) => !prev)
  }

  /**
   * Effect for handling auto-rotation
   */
  useEffect(() => {
    // Clear any existing timer
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }

    // Start new timer if auto-rotation is enabled
    if (isAutoRotating) {
      timerRef.current = setInterval(() => {
        rotateNext()
      }, autoRotateInterval)
    }

    // Cleanup function to clear timer on unmount or when dependencies change
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }
  }, [isAutoRotating, autoRotateInterval, rotationAngle])

  /**
   * Handler for manual navigation that resets the auto-rotation timer
   */
  const handleManualRotation = (direction: 'next' | 'prev') => {
    if (direction === 'next') {
      rotateNext()
    } else {
      rotatePrev()
    }

    // Reset auto-rotation timer if enabled
    if (isAutoRotating && timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = setInterval(() => {
        rotateNext()
      }, autoRotateInterval)
    }
  }

  /**
   * Keyboard navigation handler
   */
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft') {
        handleManualRotation('prev')
      } else if (e.key === 'ArrowRight') {
        handleManualRotation('next')
      } else if (e.key === ' ' || e.key === 'Enter') {
        e.preventDefault()
        toggleAutoRotation()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isAutoRotating])

  // Handle single image case
  if (images.length === 0) {
    return (
      <div className={`flex items-center justify-center h-96 ${className}`}>
        <p className="text-gray-500">No images to display</p>
      </div>
    )
  }

  if (images.length === 1) {
    return (
      <div className={`flex items-center justify-center h-96 ${className}`}>
        <img
          src={images[0].src}
          alt={images[0].alt}
          className="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
        />
      </div>
    )
  }

  return (
    <div className={`relative w-full ${className}`}>
      {/* 3D Gallery Container */}
      <div
        className="relative w-full flex justify-center items-center"
        style={{
          height: '500px',
          perspective: '1000px',
        }}
      >
        {/* Rotating wrapper */}
        <div
          className="relative w-full h-full transition-transform duration-1000 ease-in-out"
          style={{
            transformStyle: 'preserve-3d',
            transform: `rotateY(${currentRotation}deg)`,
          }}
        >
          {images.map((image, index) => (
            <div
              key={index}
              className="absolute top-1/2 left-1/2 rounded-xl overflow-hidden shadow-2xl"
              style={{
                width: '400px',
                height: '300px',
                transformStyle: 'preserve-3d',
                transform: `
                  translate(-50%, -50%)
                  rotateY(${index * rotationAngle}deg)
                  translateZ(${cylinderRadius}px)
                `,
              }}
            >
              <img
                src={image.src}
                alt={image.alt}
                className="w-full h-full object-cover"
              />
            </div>
          ))}
        </div>
      </div>

      {/* Navigation Controls */}
      <div className="flex justify-center items-center gap-5 mt-16">
        <button
          onClick={() => handleManualRotation('prev')}
          className="px-9 py-4 text-base font-semibold rounded-lg bg-white text-purple-600 shadow-lg hover:shadow-xl hover:-translate-y-0.5 active:translate-y-0 transition-all duration-300"
          aria-label="Previous image"
        >
          Previous
        </button>

        <button
          onClick={toggleAutoRotation}
          className="px-9 py-4 text-base font-semibold rounded-lg bg-purple-600 text-white shadow-lg hover:shadow-xl hover:bg-purple-700 hover:-translate-y-0.5 active:translate-y-0 transition-all duration-300"
          aria-label={isAutoRotating ? 'Pause auto-rotation' : 'Resume auto-rotation'}
        >
          {isAutoRotating ? 'Pause' : 'Play'}
        </button>

        <button
          onClick={() => handleManualRotation('next')}
          className="px-9 py-4 text-base font-semibold rounded-lg bg-white text-purple-600 shadow-lg hover:shadow-xl hover:-translate-y-0.5 active:translate-y-0 transition-all duration-300"
          aria-label="Next image"
        >
          Next
        </button>
      </div>

      {/* Mobile Responsive Styles */}
      <style jsx>{`
        @media (max-width: 768px) {
          .relative > div {
            height: 350px !important;
          }
        }

        /* Reduced motion support */
        @media (prefers-reduced-motion: reduce) {
          .transition-transform {
            transition: none !important;
          }
        }
      `}</style>
    </div>
  )
}
```

## Usage Examples

### Basic Usage

```tsx
import RotatingGallery from '@/components/RotatingGallery'

export default function Page() {
  const images = [
    { src: '/images/product-1.jpg', alt: 'Product view 1' },
    { src: '/images/product-2.jpg', alt: 'Product view 2' },
    { src: '/images/product-3.jpg', alt: 'Product view 3' },
    { src: '/images/product-4.jpg', alt: 'Product view 4' },
  ]

  return (
    <div className="container mx-auto py-12">
      <h1 className="text-4xl font-bold text-center mb-8">Product Gallery</h1>
      <RotatingGallery images={images} />
    </div>
  )
}
```

### With Custom Configuration

```tsx
<RotatingGallery
  images={galleryImages}
  rotationSpeed={60}           // 60 degrees per rotation (for 6 images)
  autoRotate={true}
  autoRotateInterval={4000}    // Rotate every 4 seconds
  cylinderRadius={500}         // Larger cylinder
  className="my-custom-class"
/>
```

### Disabled Auto-Rotation

```tsx
<RotatingGallery
  images={images}
  autoRotate={false}  // Manual control only
/>
```

### Integration with Data Fetching

```tsx
'use client'

import { useState, useEffect } from 'react'
import RotatingGallery from '@/components/RotatingGallery'

export default function ProductPage({ productId }: { productId: string }) {
  const [images, setImages] = useState<Array<{ src: string; alt: string }>>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Fetch product images
    fetch(`/api/products/${productId}/images`)
      .then(res => res.json())
      .then(data => {
        setImages(data.images)
        setLoading(false)
      })
  }, [productId])

  if (loading) {
    return <div className="text-center py-12">Loading gallery...</div>
  }

  return <RotatingGallery images={images} />
}
```

## Customization Guide

### Styling with Tailwind

The component uses Tailwind classes extensively. Customize by:

1. **Wrapper styling**: Pass custom classes via `className` prop
2. **Button styling**: Modify the button classes in the component
3. **Image container**: Adjust width/height in inline styles
4. **Colors**: Change `purple-600`, `white`, etc. to match your theme

### Adjusting for Different Image Counts

The component automatically calculates rotation angles. However, you may want to:

- **2 images**: Use 180° rotation (component handles this)
- **6 images**: 60° per image (automatic)
- **8 images**: 45° per image (default, automatic)
- **12 images**: 30° per image (automatic)

### Responsive Behavior

Mobile adjustments are included via styled-jsx. For more control:

```tsx
// Add custom breakpoint logic
const isMobile = useMediaQuery('(max-width: 768px)')
const radius = isMobile ? 280 : cylinderRadius
```

### Custom Animations

Replace the transition duration:

```tsx
<div
  className="relative w-full h-full ease-in-out"
  style={{
    transformStyle: 'preserve-3d',
    transform: `rotateY(${currentRotation}deg)`,
    transition: 'transform 0.8s cubic-bezier(0.4, 0, 0.2, 1)',
  }}
>
```

## TypeScript Integration

The component is fully typed. Extend interfaces as needed:

```tsx
interface ExtendedGalleryImage extends GalleryImage {
  title?: string
  description?: string
  metadata?: Record<string, any>
}

interface ExtendedGalleryProps extends Omit<RotatingGalleryProps, 'images'> {
  images: ExtendedGalleryImage[]
  onImageClick?: (image: ExtendedGalleryImage) => void
}
```

## Performance Tips

1. **Image Optimization**: Use Next.js Image component for automatic optimization
2. **Lazy Loading**: Only load visible images (requires custom implementation)
3. **Memoization**: Use `useMemo` for expensive calculations
4. **Reduce Image Count**: Limit to 8-10 images on mobile for smooth performance

## Accessibility Features

The component includes:
- ARIA labels on all interactive elements
- Keyboard navigation (arrow keys, space, enter)
- Reduced motion support via CSS media query
- Descriptive alt text (provided via props)
- Pause control for WCAG 2.2.2 compliance

## Testing

```tsx
import { render, screen, fireEvent } from '@testing-library/react'
import RotatingGallery from './RotatingGallery'

describe('RotatingGallery', () => {
  const mockImages = [
    { src: '/img1.jpg', alt: 'Image 1' },
    { src: '/img2.jpg', alt: 'Image 2' },
  ]

  it('renders all images', () => {
    render(<RotatingGallery images={mockImages} />)
    expect(screen.getByAltText('Image 1')).toBeInTheDocument()
    expect(screen.getByAltText('Image 2')).toBeInTheDocument()
  })

  it('rotates on button click', () => {
    render(<RotatingGallery images={mockImages} autoRotate={false} />)
    const nextButton = screen.getByLabelText('Next image')
    fireEvent.click(nextButton)
    // Add assertions for rotation state
  })
})
```

## Next.js Specific Considerations

- Use `'use client'` directive (already included)
- Consider using Next.js Image component for optimization
- Can be used in both pages and app directory
- Works with server components as a client island
