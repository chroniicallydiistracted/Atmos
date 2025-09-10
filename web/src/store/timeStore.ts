import { create } from 'zustand'
import { findNearestTimestamp, isStale, FRAME_INTERVAL_MS } from '../lib/time'

interface TimelineData {
  timestamps: string[]
  latest: string
  cadenceMinutes: number
}

interface TimeState {
  // Current playback state
  currentTime: string | null
  isPlaying: boolean
  currentIndex: number
  
  // Reference layer (defines the timeline)
  referenceLayer: string
  
  // Timeline data for each layer
  timelines: Record<string, TimelineData>
  
  // Playback control
  play: () => void
  pause: () => void
  step: (direction: 1 | -1) => void
  jumpToLatest: () => void
  jumpToTime: (timestamp: string) => void
  setCurrentIndex: (index: number) => void
  
  // Timeline management
  setTimeline: (layerId: string, timeline: TimelineData) => void
  setReferenceLayer: (layerId: string) => void
  
  // Temporal joining
  getTimeForLayer: (layerId: string, targetTime?: string) => string | null
  
  // Status checks
  isStale: (layerId?: string) => boolean
  getReferenceTimeline: () => string[]
}

export const useTimeStore = create<TimeState>((set, get) => {
  let playbackInterval: NodeJS.Timeout | null = null
  
  const startPlayback = () => {
    if (playbackInterval) return
    
    playbackInterval = setInterval(() => {
      const { currentIndex, timelines, referenceLayer } = get()
      const timeline = timelines[referenceLayer]
      
      if (!timeline || currentIndex >= timeline.timestamps.length - 1) {
        // Reached end, stop playing
        set({ isPlaying: false })
        if (playbackInterval) {
          clearInterval(playbackInterval)
          playbackInterval = null
        }
        return
      }
      
      // Move to next frame
      const nextIndex = currentIndex + 1
      set({
        currentIndex: nextIndex,
        currentTime: timeline.timestamps[nextIndex]
      })
    }, FRAME_INTERVAL_MS)
  }
  
  const stopPlayback = () => {
    if (playbackInterval) {
      clearInterval(playbackInterval)
      playbackInterval = null
    }
  }

  return {
    currentTime: null,
    isPlaying: false,
    currentIndex: 0,
    referenceLayer: 'goes-c13', // Default to GOES as reference
    timelines: {},
    
    play: () => {
      const { timelines, referenceLayer, currentIndex } = get()
      const timeline = timelines[referenceLayer]
      
      if (!timeline || currentIndex >= timeline.timestamps.length - 1) {
        return // Can't play if no timeline or at end
      }
      
      set({ isPlaying: true })
      startPlayback()
    },
    
    pause: () => {
      set({ isPlaying: false })
      stopPlayback()
    },
    
    step: (direction: 1 | -1) => {
      const { currentIndex, timelines, referenceLayer, isPlaying } = get()
      const timeline = timelines[referenceLayer]
      
      if (!timeline) return
      
      // Pause if currently playing
      if (isPlaying) {
        set({ isPlaying: false })
        stopPlayback()
      }
      
      const newIndex = Math.max(0, Math.min(timeline.timestamps.length - 1, currentIndex + direction))
      
      set({
        currentIndex: newIndex,
        currentTime: timeline.timestamps[newIndex]
      })
    },
    
    jumpToLatest: () => {
      const { timelines, referenceLayer, isPlaying } = get()
      const timeline = timelines[referenceLayer]
      
      if (!timeline) return
      
      // Pause if playing
      if (isPlaying) {
        set({ isPlaying: false })
        stopPlayback()
      }
      
      const latestIndex = timeline.timestamps.length - 1
      set({
        currentIndex: latestIndex,
        currentTime: timeline.timestamps[latestIndex]
      })
    },
    
    jumpToTime: (timestamp: string) => {
      const { timelines, referenceLayer, isPlaying } = get()
      const timeline = timelines[referenceLayer]
      
      if (!timeline) return
      
      const index = timeline.timestamps.indexOf(timestamp)
      if (index === -1) return
      
      // Pause if playing
      if (isPlaying) {
        set({ isPlaying: false })
        stopPlayback()
      }
      
      set({
        currentIndex: index,
        currentTime: timestamp
      })
    },
    
    setCurrentIndex: (index: number) => {
      const { timelines, referenceLayer, isPlaying } = get()
      const timeline = timelines[referenceLayer]
      
      if (!timeline) return
      
      const clampedIndex = Math.max(0, Math.min(timeline.timestamps.length - 1, index))
      
      // Pause if playing
      if (isPlaying) {
        set({ isPlaying: false })
        stopPlayback()
      }
      
      set({
        currentIndex: clampedIndex,
        currentTime: timeline.timestamps[clampedIndex]
      })
    },
    
    setTimeline: (layerId: string, timeline: TimelineData) => {
      const { referenceLayer, currentIndex } = get()
      
      set((state) => ({
        timelines: {
          ...state.timelines,
          [layerId]: timeline
        }
      }))
      
      // If this is the reference layer and we don't have a current time, set it
      if (layerId === referenceLayer && !get().currentTime) {
        const index = Math.min(currentIndex, timeline.timestamps.length - 1)
        set({
          currentIndex: index,
          currentTime: timeline.timestamps[index]
        })
      }
    },
    
    setReferenceLayer: (layerId: string) => {
      const { timelines, isPlaying } = get()
      
      // Pause if playing
      if (isPlaying) {
        set({ isPlaying: false })
        stopPlayback()
      }
      
      set({ referenceLayer: layerId })
      
      // If the new reference layer has a timeline, jump to latest
      const timeline = timelines[layerId]
      if (timeline) {
        const latestIndex = timeline.timestamps.length - 1
        set({
          currentIndex: latestIndex,
          currentTime: timeline.timestamps[latestIndex]
        })
      }
    },
    
    getTimeForLayer: (layerId: string, targetTime?: string) => {
      const { timelines, currentTime } = get()
      const timeline = timelines[layerId]
      const target = targetTime || currentTime
      
      if (!timeline || !target) return null
      
      // Use as-of temporal join with 3-minute tolerance
      return findNearestTimestamp(target, timeline.timestamps, 3)
    },
    
    isStale: (layerId?: string) => {
      const { timelines, referenceLayer } = get()
      const targetLayer = layerId || referenceLayer
      const timeline = timelines[targetLayer]
      
      if (!timeline) return false
      
      // Check if the latest timestamp is stale (>10 minutes old)
      return isStale(timeline.latest, 10)
    },
    
    getReferenceTimeline: () => {
      const { timelines, referenceLayer } = get()
      return timelines[referenceLayer]?.timestamps || []
    }
  }
})