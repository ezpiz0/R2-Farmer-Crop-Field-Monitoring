import React, { useState, useEffect, useRef } from 'react'
import './MapSearch.css'

function MapSearch({ onLocationSelect }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  const [showResults, setShowResults] = useState(false)
  const searchRef = useRef(null)

  // Закрытие результатов при клике вне компонента
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setShowResults(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  // Debounced поиск
  useEffect(() => {
    if (query.length < 3) {
      setResults([])
      setShowResults(false)
      return
    }

    const timeoutId = setTimeout(() => {
      performSearch(query)
    }, 500)

    return () => clearTimeout(timeoutId)
  }, [query])

  const performSearch = async (searchQuery) => {
    setIsSearching(true)
    
    try {
      // Используем Nominatim API от OpenStreetMap
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?` +
        `format=json&q=${encodeURIComponent(searchQuery)}&` +
        `limit=5&addressdetails=1&accept-language=ru`,
        {
          headers: {
            'User-Agent': 'AgroSky-Insight-App' // Nominatim требует User-Agent
          }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setResults(data)
        setShowResults(data.length > 0)
      } else {
        console.error('Search error:', response.statusText)
        setResults([])
        setShowResults(false)
      }
    } catch (error) {
      console.error('Search error:', error)
      setResults([])
      setShowResults(false)
    } finally {
      setIsSearching(false)
    }
  }

  const handleSelectLocation = (result) => {
    const lat = parseFloat(result.lat)
    const lon = parseFloat(result.lon)
    
    // Передаем координаты и zoom level родительскому компоненту
    onLocationSelect({
      lat,
      lon,
      zoom: 13,
      name: result.display_name
    })

    setQuery(result.display_name)
    setShowResults(false)
    setResults([])
  }

  const handleClear = () => {
    setQuery('')
    setResults([])
    setShowResults(false)
  }

  return (
    <div className="map-search" ref={searchRef}>
      <div className="search-input-wrapper">
        <span className="search-icon">🔍</span>
        <input
          type="text"
          className="search-input"
          placeholder="Поиск города, адреса или объекта..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setShowResults(true)}
        />
        {query && (
          <button className="search-clear" onClick={handleClear} title="Очистить">
            ✕
          </button>
        )}
        {isSearching && (
          <div className="search-spinner">
            <div className="spinner-small"></div>
          </div>
        )}
      </div>

      {showResults && results.length > 0 && (
        <div className="search-results">
          {results.map((result) => (
            <div
              key={result.place_id}
              className="search-result-item"
              onClick={() => handleSelectLocation(result)}
            >
              <div className="result-icon">📍</div>
              <div className="result-info">
                <div className="result-name">
                  {result.name || result.display_name.split(',')[0]}
                </div>
                <div className="result-address">
                  {result.display_name}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {showResults && results.length === 0 && query.length >= 3 && !isSearching && (
        <div className="search-results">
          <div className="search-no-results">
            <div className="no-results-icon">🔍</div>
            <div className="no-results-text">Ничего не найдено</div>
          </div>
        </div>
      )}
    </div>
  )
}

export default MapSearch

