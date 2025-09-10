import { create } from 'zustand'

export interface LayerConfig {
  id: string
  name: string
  visible: boolean
  opacity: number
  type: 'raster' | 'vector'
  hasTimeline: boolean
  metadata?: {
    units?: string
    legend?: string
    updateCadence?: string
    provenance?: string
    caveats?: string[]
  }
}

interface LayerState {
  layers: Record<string, LayerConfig>
  activeLayers: string[]
  toggleLayer: (layerId: string) => void
  setLayerOpacity: (layerId: string, opacity: number) => void
  setLayerMetadata: (layerId: string, metadata: LayerConfig['metadata']) => void
  getVisibleLayers: () => LayerConfig[]
  isLayerVisible: (layerId: string) => boolean
}

const initialLayers: Record<string, LayerConfig> = {
  'alerts': {
    id: 'alerts',
    name: 'NWS Alerts',
    visible: false,
    opacity: 0.8,
    type: 'vector',
    hasTimeline: true,
    metadata: {
      units: 'Categorical',
      legend: 'Severity-based colors',
      updateCadence: '5 minutes',
      provenance: 'National Weather Service'
    }
  },
  'goes-c13': {
    id: 'goes-c13',
    name: 'GOES IR (Band 13)',
    visible: false,
    opacity: 0.8,
    type: 'raster',
    hasTimeline: true,
    metadata: {
      units: 'Kelvin',
      legend: 'Infrared temperature',
      updateCadence: '10 minutes',
      provenance: 'NOAA GOES-East'
    }
  },
  'mrms-reflectivity': {
    id: 'mrms-reflectivity',
    name: 'Radar Mosaic',
    visible: false,
    opacity: 0.8,
    type: 'raster',
    hasTimeline: true,
    metadata: {
      units: 'dBZ',
      legend: 'Reflectivity scale',
      updateCadence: '5 minutes',
      provenance: 'NOAA MRMS'
    }
  }
}

export const useLayerStore = create<LayerState>((set, get) => ({
  layers: initialLayers,
  activeLayers: [],
  
  toggleLayer: (layerId: string) => set((state) => {
    const layer = state.layers[layerId]
    if (!layer) return state

    const newLayers = {
      ...state.layers,
      [layerId]: {
        ...layer,
        visible: !layer.visible
      }
    }

    const newActiveLayers = layer.visible
      ? state.activeLayers.filter(id => id !== layerId)
      : [...state.activeLayers, layerId]

    return {
      layers: newLayers,
      activeLayers: newActiveLayers
    }
  }),
  
  setLayerOpacity: (layerId: string, opacity: number) => set((state) => ({
    layers: {
      ...state.layers,
      [layerId]: {
        ...state.layers[layerId],
        opacity: Math.max(0, Math.min(1, opacity))
      }
    }
  })),
  
  setLayerMetadata: (layerId: string, metadata: LayerConfig['metadata']) => set((state) => ({
    layers: {
      ...state.layers,
      [layerId]: {
        ...state.layers[layerId],
        metadata: { ...state.layers[layerId].metadata, ...metadata }
      }
    }
  })),
  
  getVisibleLayers: () => {
    const { layers } = get()
    return Object.values(layers).filter(layer => layer.visible)
  },
  
  isLayerVisible: (layerId: string) => {
    const { layers } = get()
    return layers[layerId]?.visible ?? false
  }
}))