import React from 'react'
import MapView from './components/MapView'
import LayerToggle from './components/LayerToggle'
import Legend from './components/Legend'
import TimeSlider from './components/TimeSlider'

export default function App() {
  return (
    <div style={{ height: '100vh', width: '100vw', position: 'relative' }}>
      <MapView />
      <div style={{ 
        position: 'absolute', 
        top: '20px', 
        left: '20px', 
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        gap: '10px'
      }}>
        <LayerToggle />
        <Legend />
      </div>
      <div style={{
        position: 'absolute',
        bottom: '20px',
        left: '20px',
        right: '20px',
        zIndex: 1000
      }}>
        <TimeSlider />
      </div>
      <div style={{
        position: 'absolute',
        bottom: '10px',
        right: '10px',
        fontSize: '12px',
        color: '#666',
        backgroundColor: 'rgba(255, 255, 255, 0.8)',
        padding: '5px 8px',
        borderRadius: '3px',
        zIndex: 1000
      }}>
        © OpenStreetMap contributors (ODbL) • Style © CyclOSM (CC-BY-SA 2.0) • Data: NOAA/NWS
      </div>
    </div>
  )
}