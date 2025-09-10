import React, { useEffect, useState } from 'react'
import { useTimeStore } from '../store/timeStore'
import { useLayerStore } from '../store/layerStore'
import { formatDisplayTime } from '../lib/time'
import { api } from '../lib/api'

export default function TimeSlider() {
  const {
    currentTime,
    isPlaying,
    currentIndex,
    play,
    pause,
    step,
    jumpToLatest,
    setCurrentIndex,
    getReferenceTimeline,
    referenceLayer,
    setTimeline,
    isStale
  } = useTimeStore()

  const { layers } = useLayerStore()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const timeline = getReferenceTimeline()
  const referenceLayerConfig = layers[referenceLayer]
  const isStaleData = isStale()

  // Load timeline data for the reference layer
  useEffect(() => {
    if (!referenceLayerConfig?.hasTimeline) return

    const loadTimeline = async () => {
      setIsLoading(true)
      setError(null)

      try {
        let timelineData
        
        switch (referenceLayer) {
          case 'goes-c13':
            timelineData = await api.goesTimeline(13, 'CONUS', 12)
            break
          case 'mrms-reflectivity':
            timelineData = await api.mosaicTimeline('reflq', 12)
            break
          case 'alerts':
            const alertData = await api.alertsLatest()
            timelineData = {
              timestamps: alertData.history,
              latest: alertData.latest,
              cadenceMinutes: 5
            }
            break
          default:
            return
        }

        setTimeline(referenceLayer, {
          timestamps: timelineData.timestamps.sort(), // Ensure chronological order
          latest: timelineData.latest,
          cadenceMinutes: timelineData.cadence_minutes || 5
        })
      } catch (err) {
        console.error('Failed to load timeline:', err)
        setError(err instanceof Error ? err.message : 'Failed to load timeline')
      } finally {
        setIsLoading(false)
      }
    }

    loadTimeline()
  }, [referenceLayer, referenceLayerConfig, setTimeline])

  // Auto-refresh timeline data every 60 seconds
  useEffect(() => {
    if (!referenceLayerConfig?.hasTimeline) return

    const interval = setInterval(async () => {
      try {
        let timelineData
        
        switch (referenceLayer) {
          case 'goes-c13':
            timelineData = await api.goesTimeline(13, 'CONUS', 12)
            break
          case 'mrms-reflectivity':
            timelineData = await api.mosaicTimeline('reflq', 12)
            break
          case 'alerts':
            const alertData = await api.alertsLatest()
            timelineData = {
              timestamps: alertData.history,
              latest: alertData.latest,
              cadenceMinutes: 5
            }
            break
          default:
            return
        }

        setTimeline(referenceLayer, {
          timestamps: timelineData.timestamps.sort(),
          latest: timelineData.latest,
          cadenceMinutes: timelineData.cadence_minutes || 5
        })
      } catch (err) {
        console.error('Failed to refresh timeline:', err)
      }
    }, 60000) // Refresh every minute

    return () => clearInterval(interval)
  }, [referenceLayer, referenceLayerConfig, setTimeline])

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newIndex = parseInt(e.target.value)
    setCurrentIndex(newIndex)
  }

  const handlePlayPause = () => {
    if (isPlaying) {
      pause()
    } else {
      play()
    }
  }

  if (!referenceLayerConfig?.hasTimeline) {
    return (
      <div className="time-slider">
        <div style={{ textAlign: 'center', color: '#666', fontSize: '14px' }}>
          Select a temporal layer to enable time controls
        </div>
      </div>
    )
  }

  if (isLoading && timeline.length === 0) {
    return (
      <div className="time-slider">
        <div style={{ textAlign: 'center', color: '#666', fontSize: '14px' }}>
          Loading timeline data...
        </div>
      </div>
    )
  }

  if (error && timeline.length === 0) {
    return (
      <div className="time-slider">
        <div style={{ textAlign: 'center', color: '#dc2626', fontSize: '14px' }}>
          Error loading timeline: {error}
        </div>
      </div>
    )
  }

  return (
    <div className="time-slider">
      <div className="time-controls">
        <button
          className="play-button"
          onClick={handlePlayPause}
          disabled={timeline.length === 0 || isStaleData}
        >
          {isPlaying ? '⏸️ Pause' : '▶️ Play'}
        </button>
        
        <button
          onClick={() => step(-1)}
          disabled={currentIndex === 0 || isStaleData}
          style={{
            background: 'none',
            border: '1px solid #d1d5db',
            padding: '4px 8px',
            cursor: currentIndex === 0 || isStaleData ? 'not-allowed' : 'pointer',
            borderRadius: '3px'
          }}
        >
          ⏮️
        </button>
        
        <button
          onClick={() => step(1)}
          disabled={currentIndex >= timeline.length - 1 || isStaleData}
          style={{
            background: 'none',
            border: '1px solid #d1d5db',
            padding: '4px 8px',
            cursor: currentIndex >= timeline.length - 1 || isStaleData ? 'not-allowed' : 'pointer',
            borderRadius: '3px'
          }}
        >
          ⏭️
        </button>
        
        <button
          onClick={jumpToLatest}
          disabled={currentIndex >= timeline.length - 1 || isStaleData}
          style={{
            background: 'none',
            border: '1px solid #d1d5db',
            padding: '4px 8px',
            cursor: currentIndex >= timeline.length - 1 || isStaleData ? 'not-allowed' : 'pointer',
            borderRadius: '3px',
            fontSize: '12px'
          }}
        >
          Latest
        </button>

        <div className="time-info">
          {currentTime ? formatDisplayTime(currentTime) : 'No time selected'}
          {isStaleData && (
            <span className="stale-indicator">STALE</span>
          )}
        </div>
      </div>

      {timeline.length > 0 && (
        <input
          type="range"
          min={0}
          max={timeline.length - 1}
          value={currentIndex}
          onChange={handleSliderChange}
          className="time-range"
          disabled={isStaleData}
        />
      )}

      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: '11px',
        color: '#666',
        marginTop: '4px'
      }}>
        <span>
          {timeline.length > 0 ? formatDisplayTime(timeline[0]) : ''}
        </span>
        <span style={{ fontSize: '10px' }}>
          {timeline.length} frames • Reference: {referenceLayerConfig.name}
        </span>
        <span>
          {timeline.length > 0 ? formatDisplayTime(timeline[timeline.length - 1]) : ''}
        </span>
      </div>

      {/* Gap indicators */}
      {timeline.length > 1 && (
        <div style={{ position: 'relative', height: '4px', marginTop: '4px' }}>
          {timeline.map((_, index) => {
            if (index === 0) return null
            
            const prevTime = new Date(timeline[index - 1]).getTime()
            const currTime = new Date(timeline[index]).getTime()
            const expectedInterval = referenceLayerConfig.metadata?.updateCadence === '5 minutes' ? 5 * 60 * 1000 : 10 * 60 * 1000
            const actualInterval = currTime - prevTime
            const isGap = actualInterval > expectedInterval * 1.5
            
            if (!isGap) return null
            
            const position = (index / (timeline.length - 1)) * 100
            
            return (
              <div
                key={index}
                style={{
                  position: 'absolute',
                  left: `${position}%`,
                  top: 0,
                  width: '2px',
                  height: '4px',
                  backgroundColor: '#f59e0b',
                  transform: 'translateX(-50%)'
                }}
                title={`Data gap at ${formatDisplayTime(timeline[index])}`}
              />
            )
          })}
        </div>
      )}
    </div>
  )
}