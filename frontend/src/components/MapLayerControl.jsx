import React, { useState } from 'react'
import { useMap } from 'react-leaflet'
import L from 'leaflet'
import './MapLayerControl.css'

function MapLayerControl() {
  const [isOpen, setIsOpen] = useState(false)
  const [selectedLayer, setSelectedLayer] = useState('osm')
  const map = useMap()

  const layers = [
    {
      id: 'osm',
      name: 'Обычная карта',
      icon: '🗺️',
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    },
    {
      id: 'satellite',
      name: 'Спутник',
      icon: '🛰️',
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      attribution: '&copy; <a href="https://www.esri.com/">Esri</a>'
    },
    {
      id: 'topo',
      name: 'Рельеф',
      icon: '⛰️',
      url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
      attribution: '&copy; <a href="https://opentopomap.org">OpenTopoMap</a>'
    },
    {
      id: 'hybrid',
      name: 'Гибрид',
      icon: '🌐',
      url: 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
      attribution: '&copy; Google'
    }
  ]

  const handleLayerChange = (layer) => {
    setSelectedLayer(layer.id)
    
    // Remove all existing tile layers
    map.eachLayer((mapLayer) => {
      if (mapLayer instanceof L.TileLayer) {
        map.removeLayer(mapLayer)
      }
    })

    // Add new tile layer
    L.tileLayer(layer.url, {
      attribution: layer.attribution,
      maxZoom: 19
    }).addTo(map)

    setIsOpen(false)
  }

  const currentLayer = layers.find(l => l.id === selectedLayer)

  return (
    <div className="map-layer-control">
      <button 
        className="layer-toggle-btn"
        onClick={() => setIsOpen(!isOpen)}
        title="Тип карты"
      >
        <span className="layer-icon">{currentLayer.icon}</span>
        <span className="layer-name">{currentLayer.name}</span>
        <span className="layer-arrow">{isOpen ? '▲' : '▼'}</span>
      </button>

      {isOpen && (
        <div className="layer-options">
          {layers.map((layer) => (
            <button
              key={layer.id}
              className={`layer-option ${selectedLayer === layer.id ? 'active' : ''}`}
              onClick={() => handleLayerChange(layer)}
            >
              <span className="option-icon">{layer.icon}</span>
              <span className="option-name">{layer.name}</span>
              {selectedLayer === layer.id && (
                <span className="option-check">✓</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default MapLayerControl

