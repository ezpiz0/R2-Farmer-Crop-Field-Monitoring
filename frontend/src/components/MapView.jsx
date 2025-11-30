import React, { useEffect, useRef, useState } from 'react'
import { MapContainer, TileLayer, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet-draw/dist/leaflet.draw.css'
import 'leaflet-draw'
import MapSearch from './MapSearch'
import MapLayerControl from './MapLayerControl'
import NDVIOverlay from './NDVIOverlay'
import { buildImageUrl } from '../utils/imageUrlHelper'
import './MapView.css'

// Fix for default markers
import icon from 'leaflet/dist/images/marker-icon.png'
import iconShadow from 'leaflet/dist/images/marker-shadow.png'

let DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41]
})

L.Marker.prototype.options.icon = DefaultIcon

// Component to handle drawing controls
function DrawControl({ onGeometrySelected, onClearSelection, hideAfterAnalysis = false, analysisResult = null }) {
  const map = useMap()
  const drawnItemsRef = useRef(new L.FeatureGroup())
  
  // Hide or reduce opacity of drawn geometry when analysis is complete
  useEffect(() => {
    if (analysisResult && drawnItemsRef.current) {
      drawnItemsRef.current.eachLayer((layer) => {
        if (layer.setStyle) {
          layer.setStyle({
            fillColor: '#3388ff',
            fillOpacity: 0.05,  // Almost invisible after analysis
            color: '#3388ff',
            weight: 1,
            opacity: 0.2
          })
        }
      })
    }
  }, [analysisResult])

  useEffect(() => {
    const drawnItems = drawnItemsRef.current
    map.addLayer(drawnItems)

    // Add draw control
    const drawControl = new L.Control.Draw({
      position: 'topright',
      draw: {
        rectangle: true,
        polygon: true,
        circle: false,
        circlemarker: false,
        marker: false,
        polyline: false,
      },
      edit: {
        featureGroup: drawnItems,
        edit: false,
        remove: true,
      }
    })
    map.addControl(drawControl)

    // Handle draw created event
    map.on(L.Draw.Event.CREATED, (e) => {
      const layer = e.layer
      
      // Clear previous drawings
      drawnItems.clearLayers()
      
      // Style the layer with reduced opacity so NDVI image is visible
      if (layer.setStyle) {
        layer.setStyle({
          fillColor: '#3388ff',
          fillOpacity: 0.1,  // Very transparent
          color: '#3388ff',
          weight: 2,
          opacity: 0.3
        })
      }
      
      // Add new layer
      drawnItems.addLayer(layer)
      
      // Get GeoJSON
      const geoJSON = layer.toGeoJSON()
      
      // Pass geometry to parent
      onGeometrySelected(geoJSON.geometry)
    })

    // Handle delete event
    map.on(L.Draw.Event.DELETED, () => {
      onClearSelection()
    })

    return () => {
      map.removeControl(drawControl)
      map.removeLayer(drawnItems)
      map.off(L.Draw.Event.CREATED)
      map.off(L.Draw.Event.DELETED)
    }
  }, [map, onGeometrySelected, onClearSelection])

  return null
}

// Component to handle map view updates
function MapController({ bounds, flyToLocation }) {
  const map = useMap()
  
  useEffect(() => {
    if (bounds && bounds.length === 2) {
      map.fitBounds(bounds, { padding: [50, 50] })
    }
  }, [bounds, map])
  
  useEffect(() => {
    if (flyToLocation) {
      map.flyTo([flyToLocation.lat, flyToLocation.lon], flyToLocation.zoom, {
        duration: 1.5
      })
    }
  }, [flyToLocation, map])
  
  return null
}

// NDVIOverlay component moved to separate file: ./NDVIOverlay.jsx

// NDVI Legend component
function NDVILegend() {
  const legendItems = [
    { color: '#8B4513', label: '< 0.2 - Почва, вода' },
    { color: '#FFD700', label: '0.2-0.4 - Низкая вегетация' },
    { color: '#ADFF2F', label: '0.4-0.6 - Средняя вегетация' },
    { color: '#228B22', label: '> 0.6 - Здоровая вегетация' },
  ]
  
  return (
    <div className="legend">
      <h3>NDVI Индекс</h3>
      {legendItems.map((item, index) => (
        <div key={index} className="legend-item">
          <div className="legend-color" style={{ background: item.color }}></div>
          <span className="legend-label">{item.label}</span>
        </div>
      ))}
    </div>
  )
}

function MapView({ onGeometrySelected, analysisResult, onClearSelection }) {
  const [showLegend, setShowLegend] = useState(false)
  const [flyToLocation, setFlyToLocation] = useState(null)
  const [imageUrl, setImageUrl] = useState(null)
  const [imageLoadStatus, setImageLoadStatus] = useState(null) // 'loading', 'loaded', 'error'

  useEffect(() => {
    if (analysisResult?.image_url) {
      setShowLegend(true)
      
      // Build correct image URL using helper function
      // This handles both dev (vite proxy) and production (nginx proxy) environments
      const builtUrl = buildImageUrl(analysisResult.image_url)
      
      if (builtUrl) {
        console.log('🖼️ Setting NDVI image URL:', {
          original: analysisResult.image_url,
          built: builtUrl,
          bounds: analysisResult.bounds
        })
        setImageUrl(builtUrl)
        setImageLoadStatus('loading')
      } else {
        console.error('❌ Failed to build image URL from:', analysisResult.image_url)
        setImageLoadStatus('error')
      }
    } else {
      setShowLegend(false)
      setImageUrl(null)
      setImageLoadStatus(null)
    }
  }, [analysisResult])

  const handleLocationSelect = (location) => {
    setFlyToLocation(location)
    // Reset after animation to allow re-selecting same location
    setTimeout(() => setFlyToLocation(null), 2000)
  }

  // Convert bounds format if needed
  // Backend returns: [[minLat, minLon], [maxLat, maxLon]]
  // Leaflet expects: [[southLat, westLon], [northLat, eastLon]] which is the same
  const leafletBounds = analysisResult?.bounds ? analysisResult.bounds : null

  return (
    <div style={{ height: '100%', width: '100%', position: 'relative' }}>
      <MapContainer
        center={[55.7558, 37.6173]}
        zoom={10}
        style={{ height: '100%', width: '100%' }}
        zoomControl={true}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        
        <DrawControl 
          onGeometrySelected={onGeometrySelected}
          onClearSelection={onClearSelection}
          hideAfterAnalysis={!!analysisResult}
          analysisResult={analysisResult}
        />

        {/* Display NDVI result as image overlay - using custom component */}
        {imageUrl && leafletBounds && (
          <NDVIOverlay
            url={imageUrl}
            bounds={leafletBounds}
            onLoadStatusChange={setImageLoadStatus}
          />
        )}
        
        {/* Map controller for bounds and location */}
        <MapController 
          bounds={analysisResult?.bounds} 
          flyToLocation={flyToLocation}
        />
        
        {/* Layer control */}
        <MapLayerControl />
      </MapContainer>
      
      {/* Search component */}
      <MapSearch onLocationSelect={handleLocationSelect} />
      
      {/* Show legend when NDVI result is displayed */}
      {showLegend && <NDVILegend />}
      
      {/* Debug info - показывать только при проблемах */}
      {imageLoadStatus === 'error' && (
        <div style={{
          position: 'absolute',
          top: '10px',
          right: '10px',
          background: 'rgba(255, 0, 0, 0.8)',
          color: 'white',
          padding: '10px',
          borderRadius: '5px',
          zIndex: 9999,
          fontSize: '12px'
        }}>
          ⚠️ Ошибка загрузки изображения NDVI
        </div>
      )}
    </div>
  )
}

export default MapView
