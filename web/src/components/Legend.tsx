import React from 'react'
import { useLayerStore } from '../store/layerStore'
import { kToC, kToF } from '../lib/time'

export default function Legend() {
  const { getVisibleLayers } = useLayerStore()
  const visibleLayers = getVisibleLayers()

  if (visibleLayers.length === 0) {
    return null
  }

  return (
    <div className="control-panel">
      <h3>Legend</h3>
      <div className="legend">
        {visibleLayers.map((layer) => (
          <LegendItem key={layer.id} layer={layer} />
        ))}
      </div>
    </div>
  )
}

interface LegendItemProps {
  layer: {
    id: string
    name: string
    metadata?: {
      units?: string
      legend?: string
      updateCadence?: string
      provenance?: string
      caveats?: string[]
    }
  }
}

function LegendItem({ layer }: LegendItemProps) {
  const renderLegendScale = () => {
    switch (layer.id) {
      case 'goes-c13':
        return <TemperatureLegend />
      case 'mrms-reflectivity':
        return <ReflectivityLegend />
      case 'alerts':
        return <AlertsLegend />
      default:
        return null
    }
  }

  return (
    <div className="legend-item">
      <div className="legend-title">{layer.name}</div>
      {renderLegendScale()}
      {layer.metadata && (
        <div style={{ fontSize: '11px', color: '#666', marginTop: '4px' }}>
          {layer.metadata.units && (
            <div>Units: {layer.metadata.units}</div>
          )}
          {layer.metadata.updateCadence && (
            <div>Updates: {layer.metadata.updateCadence}</div>
          )}
          {layer.metadata.provenance && (
            <div>Source: {layer.metadata.provenance}</div>
          )}
        </div>
      )}
    </div>
  )
}

function TemperatureLegend() {
  // GOES Band 13 temperature scale (180-330K typical range)
  const tempStops = [
    { temp: 180, color: '#800080' }, // Purple (very cold)
    { temp: 200, color: '#0000ff' }, // Blue (cold)
    { temp: 220, color: '#00ffff' }, // Cyan
    { temp: 240, color: '#00ff00' }, // Green
    { temp: 260, color: '#ffff00' }, // Yellow
    { temp: 280, color: '#ff8000' }, // Orange
    { temp: 300, color: '#ff0000' }, // Red
    { temp: 320, color: '#ffffff' }  // White (hot)
  ]

  return (
    <div>
      <div className="legend-scale" style={{ height: '15px' }}>
        {tempStops.map((stop, i) => (
          <div
            key={i}
            style={{
              flex: 1,
              backgroundColor: stop.color,
              height: '100%'
            }}
          />
        ))}
      </div>
      <div className="legend-labels">
        <span>{Math.round(kToC(180))}°C</span>
        <span>{Math.round(kToC(250))}°C</span>
        <span>{Math.round(kToC(320))}°C</span>
      </div>
    </div>
  )
}

function ReflectivityLegend() {
  // NEXRAD reflectivity scale
  const reflStops = [
    { dbz: -30, color: '#000000' }, // No return
    { dbz: -10, color: '#00ecec' }, // Light blue
    { dbz: 0,   color: '#01a0f6' }, // Blue
    { dbz: 10,  color: '#0000f6' }, // Dark blue
    { dbz: 20,  color: '#00ff00' }, // Green
    { dbz: 30,  color: '#00bb00' }, // Dark green
    { dbz: 40,  color: '#fff000' }, // Yellow
    { dbz: 50,  color: '#ff9000' }, // Orange
    { dbz: 60,  color: '#ff0000' }, // Red
    { dbz: 70,  color: '#d60000' }, // Dark red
    { dbz: 80,  color: '#c000ff' }  // Magenta
  ]

  return (
    <div>
      <div className="legend-scale" style={{ height: '15px' }}>
        {reflStops.map((stop, i) => (
          <div
            key={i}
            style={{
              flex: 1,
              backgroundColor: stop.color,
              height: '100%'
            }}
          />
        ))}
      </div>
      <div className="legend-labels">
        <span>-30 dBZ</span>
        <span>30 dBZ</span>
        <span>80 dBZ</span>
      </div>
    </div>
  )
}

function AlertsLegend() {
  const severityLevels = [
    { level: 'Minor', color: '#eab308', desc: 'Advisory' },
    { level: 'Moderate', color: '#ea580c', desc: 'Warning' },
    { level: 'Severe', color: '#dc2626', desc: 'Severe' },
    { level: 'Extreme', color: '#d946ef', desc: 'Extreme' }
  ]

  return (
    <div>
      {severityLevels.map((item) => (
        <div
          key={item.level}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            margin: '2px 0',
            fontSize: '11px'
          }}
        >
          <div
            style={{
              width: '12px',
              height: '12px',
              backgroundColor: item.color,
              borderRadius: '2px',
              border: '1px solid #ccc'
            }}
          />
          <span>{item.desc}</span>
        </div>
      ))}
    </div>
  )
}