import React from 'react'
import { useLayerStore } from '../store/layerStore'
import { useTimeStore } from '../store/timeStore'
import clsx from 'clsx'

export default function LayerToggle() {
  const { layers, toggleLayer, setLayerOpacity } = useLayerStore()
  const { setReferenceLayer, referenceLayer, isStale } = useTimeStore()

  const layerList = Object.values(layers)

  return (
    <div className="control-panel">
      <h3>Data Layers</h3>
      <div className="layer-toggle">
        {layerList.map((layer) => {
          const isReference = layer.id === referenceLayer
          const layerIsStale = isStale(layer.id)
          
          return (
            <div key={layer.id} className={clsx('layer-item', { disabled: layerIsStale })}>
              <input
                type="checkbox"
                id={layer.id}
                checked={layer.visible}
                onChange={() => toggleLayer(layer.id)}
                disabled={layerIsStale}
              />
              <label htmlFor={layer.id}>
                {layer.name}
                {isReference && <span style={{ color: '#2563eb', fontSize: '11px' }}> (time ref)</span>}
                {layerIsStale && <span style={{ color: '#dc2626', fontSize: '11px' }}> (stale)</span>}
              </label>
              
              {layer.visible && (
                <div style={{ marginTop: '4px', width: '100%' }}>
                  {/* Opacity slider */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px' }}>
                    <span>Opacity:</span>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={layer.opacity * 100}
                      onChange={(e) => setLayerOpacity(layer.id, parseInt(e.target.value) / 100)}
                      style={{ flex: 1 }}
                    />
                    <span>{Math.round(layer.opacity * 100)}%</span>
                  </div>
                  
                  {/* Time reference selector for temporal layers */}
                  {layer.hasTimeline && (
                    <button
                      onClick={() => setReferenceLayer(layer.id)}
                      disabled={isReference}
                      style={{
                        marginTop: '4px',
                        padding: '2px 6px',
                        fontSize: '11px',
                        border: '1px solid #d1d5db',
                        borderRadius: '3px',
                        background: isReference ? '#2563eb' : 'white',
                        color: isReference ? 'white' : '#374151',
                        cursor: isReference ? 'default' : 'pointer',
                        width: '100%'
                      }}
                    >
                      {isReference ? 'Time Reference' : 'Use for Time'}
                    </button>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
      
      {layerList.some(layer => isStale(layer.id)) && (
        <div style={{
          marginTop: '12px',
          padding: '8px',
          backgroundColor: '#fef3c7',
          border: '1px solid #f59e0b',
          borderRadius: '4px',
          fontSize: '12px',
          color: '#92400e'
        }}>
          ⚠️ Some data layers have stale data (&gt;10 min old)
        </div>
      )}
    </div>
  )
}