/**
 * NDVI Image Overlay Component
 * Displays NDVI visualization as Leaflet ImageOverlay
 * Uses native Leaflet API for better control and reliability
 */
import { useEffect, useRef } from 'react'
import { useMap } from 'react-leaflet'
import L from 'leaflet'
import { buildImageUrl } from '../utils/imageUrlHelper'

/**
 * NDVIOverlay Component
 * 
 * @param {Object} props
 * @param {string} props.url - Image URL from API response
 * @param {Array} props.bounds - Bounds array [[minLat, minLon], [maxLat, maxLon]]
 * @param {Function} props.onLoadStatusChange - Callback(status) where status is 'loading'|'loaded'|'error'
 */
function NDVIOverlay({ url, bounds, onLoadStatusChange }) {
  const map = useMap()
  const overlayRef = useRef(null)
  const imageRef = useRef(null)

  useEffect(() => {
    if (!url || !bounds || !map) {
      if (onLoadStatusChange) onLoadStatusChange(null)
      return
    }

    // Validate bounds format
    if (!Array.isArray(bounds) || bounds.length !== 2) {
      console.error('❌ Invalid bounds format:', bounds)
      if (onLoadStatusChange) onLoadStatusChange('error')
      return
    }

    const southWest = bounds[0]  // [minLat, minLon]
    const northEast = bounds[1]  // [maxLat, maxLon]
    
    if (!Array.isArray(southWest) || !Array.isArray(northEast) ||
        southWest.length !== 2 || northEast.length !== 2) {
      console.error('❌ Invalid bounds coordinates:', { southWest, northEast })
      if (onLoadStatusChange) onLoadStatusChange('error')
      return
    }

    // Create Leaflet bounds
    const leafletBounds = L.latLngBounds(
      [southWest[0], southWest[1]],  // [southLat, westLon]
      [northEast[0], northEast[1]]   // [northLat, eastLon]
    )
    
    if (!leafletBounds.isValid()) {
      console.error('❌ Invalid Leaflet bounds:', {
        southWest,
        northEast,
        calculated: leafletBounds.toBBoxString()
      })
      if (onLoadStatusChange) onLoadStatusChange('error')
      return
    }

    // Build correct image URL
    const imageUrl = buildImageUrl(url)
    if (!imageUrl) {
      console.error('❌ Failed to build image URL from:', url)
      if (onLoadStatusChange) onLoadStatusChange('error')
      return
    }

    console.log('🖼️ Loading NDVI image:', {
      originalUrl: url,
      finalUrl: imageUrl,
      bounds: {
        sw: leafletBounds.getSouthWest().toString(),
        ne: leafletBounds.getNorthEast().toString(),
        bbox: leafletBounds.toBBoxString()
      },
      mapCenter: map.getCenter().toString(),
      mapZoom: map.getZoom()
    })

    // Notify loading started
    if (onLoadStatusChange) onLoadStatusChange('loading')

    // Remove previous overlay if exists
    const removePreviousOverlay = () => {
      if (overlayRef.current) {
        try {
          map.removeLayer(overlayRef.current)
        } catch (err) {
          console.warn('Warning while removing previous overlay:', err)
        }
        overlayRef.current = null
      }
      if (imageRef.current) {
        imageRef.current.onload = null
        imageRef.current.onerror = null
        imageRef.current = null
      }
    }

    removePreviousOverlay()

    // Pre-load image to verify it's accessible
    const img = new Image()
    img.crossOrigin = 'anonymous'
    imageRef.current = img
    
    img.onload = () => {
      console.log('✅ Image loaded successfully:', {
        url: imageUrl,
        width: img.naturalWidth,
        height: img.naturalHeight,
        bounds: leafletBounds.toBBoxString()
      })
      
      try {
        // Create ImageOverlay with high z-index for visibility
        const overlay = L.imageOverlay(imageUrl, leafletBounds, {
          opacity: 1.0,  // Full opacity
          zIndex: 10000,  // Very high z-index to be above everything
          interactive: false,
          crossOrigin: 'anonymous',
          className: 'ndvi-overlay'
        })

        overlay.addTo(map)
        overlayRef.current = overlay
        
        // Force map to recalculate size and redraw
        map.invalidateSize()
        
        // Fit bounds to image if bounds are valid
        if (leafletBounds.isValid()) {
          map.fitBounds(leafletBounds, { 
            padding: [20, 20], 
            maxZoom: 18,
            duration: 0.5
          })
        }

        console.log('✅ ImageOverlay added to map successfully:', {
          visible: overlay.getBounds().toBBoxString(),
          opacity: overlay.options.opacity,
          zIndex: overlay.options.zIndex
        })

        if (onLoadStatusChange) onLoadStatusChange('loaded')
        
      } catch (overlayError) {
        console.error('❌ Failed to create ImageOverlay:', overlayError)
        if (onLoadStatusChange) onLoadStatusChange('error')
      }
    }
    
    img.onerror = (error) => {
      console.error('❌ Image failed to load:', {
        url: imageUrl,
        error: error,
        originalUrl: url
      })
      
      // Try to load anyway - sometimes CORS or other issues don't prevent display
      try {
        const overlay = L.imageOverlay(imageUrl, leafletBounds, {
          opacity: 1.0,
          zIndex: 10000,
          interactive: false,
          crossOrigin: 'anonymous',
          className: 'ndvi-overlay'
        })
        overlay.addTo(map)
        overlayRef.current = overlay
        map.invalidateSize()
        console.warn('⚠️ ImageOverlay added despite load error')
        if (onLoadStatusChange) onLoadStatusChange('loaded')
      } catch (fallbackError) {
        console.error('❌ Fallback also failed:', fallbackError)
        if (onLoadStatusChange) onLoadStatusChange('error')
      }
    }
    
    // Start loading
    img.src = imageUrl

    // Cleanup function
    return () => {
      removePreviousOverlay()
    }
  }, [url, bounds, map, onLoadStatusChange])

  // Component doesn't render anything
  return null
}

export default NDVIOverlay

