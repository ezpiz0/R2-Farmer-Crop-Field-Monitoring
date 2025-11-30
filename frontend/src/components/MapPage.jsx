import React, { useState } from 'react'
import Header from './Header'
import MapView from './MapView'
import Sidebar from './Sidebar'
import TimeSeriesModal from './TimeSeriesModal'
import AIAgronomistPanel from './AIAgronomistPanel'
import aiService from '../utils/aiService'
import './MapPage.css'

function MapPage() {
  const [selectedGeometry, setSelectedGeometry] = useState(null)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [showTimeSeriesModal, setShowTimeSeriesModal] = useState(false)
  const [showAIPanel, setShowAIPanel] = useState(false)
  const [sidebarWidth, setSidebarWidth] = useState(400) // Ширина боковой панели
  const [isResizing, setIsResizing] = useState(false)

  const handleGeometrySelected = (geometry) => {
    setSelectedGeometry(geometry)
    setAnalysisResult(null)
  }

  const handleClearSelection = () => {
    setSelectedGeometry(null)
    setAnalysisResult(null)
  }

  const handleAnalysisStart = () => {
    setIsAnalyzing(true)
  }

  const handleAnalysisComplete = (result) => {
    setAnalysisResult(result)
    setIsAnalyzing(false)
  }

  const handleAnalysisError = () => {
    setIsAnalyzing(false)
  }

  const handleOpenTimeSeries = () => {
    setShowTimeSeriesModal(true)
  }

  const handleCloseTimeSeries = () => {
    setShowTimeSeriesModal(false)
  }

  const handleOpenAIPanel = () => {
    setShowAIPanel(true)
  }

  const handleCloseAIPanel = () => {
    setShowAIPanel(false)
  }

  // Обработчики изменения размера панели
  const handleMouseDown = (e) => {
    setIsResizing(true)
    e.preventDefault()
  }

  const handleMouseMove = (e) => {
    if (!isResizing) return
    
    // Используем requestAnimationFrame для более плавного обновления
    requestAnimationFrame(() => {
      const newWidth = e.clientX
      // Ограничиваем ширину панели от 300px до 600px
      if (newWidth >= 300 && newWidth <= 600) {
        setSidebarWidth(newWidth)
      }
    })
  }

  const handleMouseUp = () => {
    setIsResizing(false)
  }

  // Добавляем обработчики событий мыши
  React.useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = 'ew-resize'
      document.body.style.userSelect = 'none'
    } else {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = 'default'
      document.body.style.userSelect = 'auto'
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = 'default'
      document.body.style.userSelect = 'auto'
    }
  }, [isResizing])

  return (
    <div className="map-page-wrapper">
      <Header />
      <div className={`map-page ${isResizing ? 'resizing' : ''}`}>
        <div className="sidebar-container" style={{ width: `${sidebarWidth}px` }}>
          <Sidebar 
            selectedGeometry={selectedGeometry}
            onAnalysisStart={handleAnalysisStart}
            onAnalysisComplete={handleAnalysisComplete}
            onAnalysisError={handleAnalysisError}
            onClearSelection={handleClearSelection}
            onOpenTimeSeries={handleOpenTimeSeries}
            onOpenAIPanel={handleOpenAIPanel}
            analysisResult={analysisResult}
            isAnalyzing={isAnalyzing}
          />
          <div 
            className={`sidebar-resizer ${isResizing ? 'resizing' : ''}`}
            onMouseDown={handleMouseDown}
            title="Перетащите для изменения ширины панели"
          />
        </div>
        
        <MapView 
          onGeometrySelected={handleGeometrySelected}
          onClearSelection={handleClearSelection}
          analysisResult={analysisResult}
          isAnalyzing={isAnalyzing}
          sidebarWidth={sidebarWidth}
        />
      </div>

      {/* Time Series Modal */}
      {showTimeSeriesModal && (
        <TimeSeriesModal 
          selectedGeometry={selectedGeometry}
          onClose={handleCloseTimeSeries}
        />
      )}

      {/* AI Agronomist Panel */}
      {showAIPanel && analysisResult && (() => {
        // Build AI analysis context from analysisResult
        const analysisContext = aiService.buildAnalysisContext({
          fieldName: 'Выбранное поле',
          fieldLocation: selectedGeometry ? {
            region: 'Обнинск, Калужская область',
            lat: selectedGeometry.coordinates?.[0]?.[0]?.[1] || 0,
            lon: selectedGeometry.coordinates?.[0]?.[0]?.[0] || 0
          } : null,
          fieldAreaHa: analysisResult.stats.area_ha,
          cropType: null,
          sowingDate: null,
          dateOfScan: analysisResult.stats.capture_date,
          satellite: 'Sentinel-2',
          weatherContext: null,
          ndviStats: {
            mean: analysisResult.stats.mean_ndvi,
            std_dev: analysisResult.stats.std_ndvi || 0,
            min: analysisResult.stats.min_ndvi || 0,
            max: analysisResult.stats.max_ndvi || 1
          },
          additionalIndicesStats: analysisResult.stats.indices_stats || null,
          zones: analysisResult.stats.zones_percent ? Object.entries(analysisResult.stats.zones_percent)
            .filter(([zone, percent]) => percent > 0) // Фильтруем зоны с нулевой площадью
            .map(([zone, percent], idx) => ({
              id: idx + 1,
              label: zone,
              area_ha: Math.max(0.01, (analysisResult.stats.area_ha * percent) / 100), // Минимум 0.01 га
              percentage: percent,
              mean_NDVI: zone.includes('low') ? 0.2 : zone.includes('medium') ? 0.45 : 0.75
            })) : null,
          temporalAnalysis: null
        });

        return (
          <AIAgronomistPanel 
            analysisContext={analysisContext}
            onClose={handleCloseAIPanel}
          />
        );
      })()}
    </div>
  )
}

export default MapPage

