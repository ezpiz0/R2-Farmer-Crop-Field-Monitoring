import React, { useEffect } from 'react';
import { GeoJSON, useMap } from 'react-leaflet';
import L from 'leaflet';

/**
 * ZoneMapLayer Component
 * Displays management zones on Leaflet map with color-coded styling
 */
function ZoneMapLayer({ zoneData, visible = true }) {
  const map = useMap();

  useEffect(() => {
    if (zoneData && zoneData.zone_geojson && visible) {
      // Fit map bounds to zones
      const geojsonLayer = L.geoJSON(zoneData.zone_geojson);
      const bounds = geojsonLayer.getBounds();
      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [50, 50] });
      }
    }
  }, [zoneData, visible, map]);

  if (!zoneData || !zoneData.zone_geojson || !visible) {
    return null;
  }

  /**
   * Style function for zone polygons
   * Colors zones based on zone_id using gradient from red (low NDVI) to green (high NDVI)
   */
  const styleZones = (feature) => {
    const zoneId = feature.properties.zone_id;
    const numZones = zoneData.num_zones;
    
    // Color palette: Red → Orange → Yellow → Light Green → Dark Green
    const colorPalettes = {
      3: [
        { fillColor: '#d32f2f', color: '#c62828' },  // Weak - Red
        { fillColor: '#fbc02d', color: '#f9a825' },  // Medium - Yellow
        { fillColor: '#388e3c', color: '#2e7d32' }   // Strong - Green
      ],
      4: [
        { fillColor: '#d32f2f', color: '#c62828' },  // Very Weak - Dark Red
        { fillColor: '#f57c00', color: '#ef6c00' },  // Weak - Orange
        { fillColor: '#fbc02d', color: '#f9a825' },  // Medium - Yellow
        { fillColor: '#7cb342', color: '#689f38' }   // Strong - Light Green
      ],
      5: [
        { fillColor: '#d32f2f', color: '#c62828' },  // Very Weak - Dark Red
        { fillColor: '#f57c00', color: '#ef6c00' },  // Weak - Orange
        { fillColor: '#fbc02d', color: '#f9a825' },  // Medium - Yellow
        { fillColor: '#7cb342', color: '#689f38' },  // Strong - Light Green
        { fillColor: '#388e3c', color: '#2e7d32' }   // Very Strong - Dark Green
      ]
    };

    const palette = colorPalettes[numZones] || colorPalettes[4];
    const colors = palette[zoneId - 1] || { fillColor: '#95a5a6', color: '#7f8c8d' };

    return {
      fillColor: colors.fillColor,
      weight: 2,
      opacity: 1,
      color: colors.color,
      fillOpacity: 0.6
    };
  };

  /**
   * Highlight zone on hover
   */
  const onEachFeature = (feature, layer) => {
    const zoneId = feature.properties.zone_id;
    const zonelabel = feature.properties.zone_label || `Зона ${zoneId}`;
    const meanNdvi = feature.properties.mean_ndvi?.toFixed(3) || 'N/A';
    const pixelCount = feature.properties.pixel_count?.toLocaleString() || 'N/A';

    // Create popup content
    const popupContent = `
      <div class="zone-popup">
        <h4 style="margin: 0 0 8px 0; color: #2c3e50;">
          <span style="color: ${styleZones(feature).fillColor};">●</span>
          Зона ${zoneId}
        </h4>
        <div style="color: #7f8c8d; margin-bottom: 8px; font-style: italic;">
          ${zonelabel}
        </div>
        <div style="display: grid; gap: 4px;">
          <div style="display: flex; justify-content: space-between;">
            <span style="color: #7f8c8d;">Средний NDVI:</span>
            <strong style="color: #27ae60;">${meanNdvi}</strong>
          </div>
          <div style="display: flex; justify-content: space-between;">
            <span style="color: #7f8c8d;">Пикселей:</span>
            <strong>${pixelCount}</strong>
          </div>
        </div>
      </div>
    `;

    layer.bindPopup(popupContent);

    // Tooltip on hover
    layer.bindTooltip(
      `<strong>Зона ${zoneId}:</strong> ${zonelabel}<br/>NDVI: ${meanNdvi}`,
      {
        sticky: true,
        className: 'zone-tooltip'
      }
    );

    // Highlight on mouse events
    layer.on({
      mouseover: function (e) {
        const layer = e.target;
        layer.setStyle({
          weight: 4,
          fillOpacity: 0.8
        });
        layer.bringToFront();
      },
      mouseout: function (e) {
        const layer = e.target;
        layer.setStyle({
          weight: 2,
          fillOpacity: 0.6
        });
      },
      click: function (e) {
        map.fitBounds(e.target.getBounds(), { padding: [20, 20] });
      }
    });
  };

  return (
    <GeoJSON
      data={zoneData.zone_geojson}
      style={styleZones}
      onEachFeature={onEachFeature}
    />
  );
}

export default ZoneMapLayer;

