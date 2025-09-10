import React, { useEffect, useRef } from 'react'
import maplibregl, { Map, NavigationControl } from 'maplibre-gl'
import { Protocol } from 'pmtiles'
import { useLayerStore } from '../store/layerStore'
import { useTimeStore } from '../store/timeStore'

const styleUrl = import.meta.env.VITE_STYLE_URL || '/styles/cyclosm.json'

export default function MapView() {
  const mapRef = useRef<Map | null>(null)
  const containerRef = useRef<HTMLDivElement | null>(null)
  const { layers, toggleLayer } = useLayerStore()
  const { currentTime, isPlaying } = useTimeStore()

  useEffect(() => {
    if (!containerRef.current) return

    // Set up PMTiles protocol for CyclOSM basemap
    const protocol = new Protocol()
    maplibregl.addProtocol('pmtiles', protocol.tile)

    // Initialize the map
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: styleUrl,
      center: [-98.5, 39.5], // Center on CONUS
      zoom: 4,
      hash: true,
      attributionControl: true,
      maxZoom: 15,
      minZoom: 3
    })

    // Add navigation control
    map.addControl(new NavigationControl({ visualizePitch: true }), 'top-right')

    // Store map reference
    mapRef.current = map

    // Handle map load
    map.on('load', () => {
      console.log('Map loaded successfully')
      
      // Add weather data sources and layers
      addWeatherLayers(map)
    })

    // Handle map errors
    map.on('error', (e) => {
      console.error('Map error:', e.error)
    })

    // Cleanup function
    return () => {
      if (mapRef.current) {
        mapRef.current.remove()
        mapRef.current = null
      }
      maplibregl.removeProtocol('pmtiles')
    }
  }, [])

  // Update layers when layer state changes
  useEffect(() => {
    if (!mapRef.current) return

    const map = mapRef.current
    
    // Update layer visibility
    Object.entries(layers).forEach(([layerId, layer]) => {
      if (map.getLayer(layerId)) {
        map.setLayoutProperty(layerId, 'visibility', layer.visible ? 'visible' : 'none')
      }
    })
  }, [layers])

  // Update layers when time changes
  useEffect(() => {
    if (!mapRef.current || !currentTime) return
    
    updateTemporalLayers(mapRef.current, currentTime)
  }, [currentTime])

  return <div ref={containerRef} style={{ height: '100%', width: '100%' }} />
}

function addWeatherLayers(map: Map) {
  const TILE_BASE = import.meta.env.VITE_TILE_BASE || 'https://weather.westfam.media'
  
  // NWS Alerts (Vector Tiles)
  map.addSource('alerts', {
    type: 'vector',
    tiles: [`${TILE_BASE}/tiles/alerts/{timestampPlaceholder}/{z}/{x}/{y}.pbf`],
    maxzoom: 12,
    attribution: 'National Weather Service'
  })

  // Alert styling by severity
  map.addLayer({
    id: 'alerts',
    type: 'fill',
    source: 'alerts',
    'source-layer': 'alerts',
    layout: {
      visibility: 'none'
    },
    paint: {
      'fill-color': [
        'case',
        ['==', ['get', 'severity'], 'Extreme'], '#d946ef', // Purple
        ['==', ['get', 'severity'], 'Severe'], '#dc2626',  // Red
        ['==', ['get', 'severity'], 'Moderate'], '#ea580c', // Orange
        ['==', ['get', 'severity'], 'Minor'], '#eab308',   // Yellow
        '#6b7280' // Gray for Unknown
      ],
      'fill-opacity': [
        'case',
        ['==', ['get', 'urgency'], 'Immediate'], 0.7,
        ['==', ['get', 'urgency'], 'Expected'], 0.5,
        0.3
      ],
      'fill-outline-color': [
        'case',
        ['in', 'Warning', ['get', 'event']], '#000000',  // Solid black for warnings
        ['in', 'Watch', ['get', 'event']], '#666666',    // Dashed for watches
        '#999999' // Dotted for advisories
      ]
    }
  })

  // GOES Satellite (Raster Tiles)
  map.addSource('goes-c13', {
    type: 'raster',
    tiles: [`${TILE_BASE}/tiles/goes/abi/c13/conus/{timestampPlaceholder}/kelvin/{z}/{x}/{y}.png`],
    tileSize: 256,
    maxzoom: 12,
    attribution: 'NOAA GOES'
  })

  map.addLayer({
    id: 'goes-c13',
    type: 'raster',
    source: 'goes-c13',
    layout: {
      visibility: 'none'
    },
    paint: {
      'raster-opacity': 0.8
    }
  })

  // MRMS Radar Mosaic (Raster Tiles)
  map.addSource('mrms-reflectivity', {
    type: 'raster',
    tiles: [`${TILE_BASE}/tiles/mosaic/reflq/{timestampPlaceholder}/{z}/{x}/{y}.png`],
    tileSize: 256,
    maxzoom: 10,
    attribution: 'NOAA MRMS'
  })

  map.addLayer({
    id: 'mrms-reflectivity',
    type: 'raster',
    source: 'mrms-reflectivity',
    layout: {
      visibility: 'none'
    },
    paint: {
      'raster-opacity': 0.8
    }
  })

  // Single-site NEXRAD radar (placeholder - will be added dynamically)
  // This will be handled by the site selector component
}

function updateTemporalLayers(map: Map, currentTime: string) {
  const TILE_BASE = import.meta.env.VITE_TILE_BASE || 'https://weather.westfam.media'
  
  // Update GOES tiles
  const goesSource = map.getSource('goes-c13') as maplibregl.RasterSource
  if (goesSource && goesSource.tiles) {
    const newGoesTiles = goesSource.tiles.map(tile => 
      tile.replace('{timestampPlaceholder}', currentTime)
    )
    goesSource.setTiles(newGoesTiles)
  }

  // Update MRMS tiles
  const mrmsSource = map.getSource('mrms-reflectivity') as maplibregl.RasterSource
  if (mrmsSource && mrmsSource.tiles) {
    const newMrmsTiles = mrmsSource.tiles.map(tile => 
      tile.replace('{timestampPlaceholder}', currentTime)
    )
    mrmsSource.setTiles(newMrmsTiles)
  }

  // Update alerts tiles
  const alertsSource = map.getSource('alerts') as maplibregl.VectorSource
  if (alertsSource && alertsSource.tiles) {
    const newAlertsTiles = alertsSource.tiles.map(tile => 
      tile.replace('{timestampPlaceholder}', currentTime)
    )
    alertsSource.setTiles(newAlertsTiles)
  }
}