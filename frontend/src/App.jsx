import { useState, useEffect } from 'react'

import Topbar from './components/layout/Topbar'

import ThreatMapPanel from './components/panels/ThreatMapPanel'
import TimelinePanel from './components/panels/TimelinePanel'
import AlertsPanel from './components/panels/AlertsPanel'
import TelemetryTerminal from './components/panels/TelemetryTerminal'
import DemoControlPanel from './components/panels/DemoControlPanel'
import IoTMapPanel from './components/panels/IoTMapPanel'
import ResponseStatusPanel from './components/panels/ResponseStatusPanel'
import DroppedPacketsPanel from './components/panels/DroppedPacketsPanel'

import TelemetryChart from './components/charts/TelemetryChart'

import useTelemetry from './hooks/useTelemetry'
import useAlerts from './hooks/useAlerts'
import useDroppedPackets from './hooks/useDroppedPackets'

function App() {
  const [connectionStatus, setConnectionStatus] = useState('connected')
  const [activeView, setActiveView] = useState('telemetry')

  const {
    isConnected,
    isPaused,
    telemetryData,
    latestPoint,
    rawEvents,
    toggle,
    clearData,
    devices,
    activeDeviceId,
    setActiveDeviceId
  } = useTelemetry()

  const alertsData = useAlerts()
  const { stats: alertStats } = alertsData

  // Use dropped packets hook
  const { droppedPackets, droppedStats } = useDroppedPackets()

  // Calculate blocked count from dropped packets stats
  const blockedCount = droppedStats.total_dropped || 0

  // Calculate total events per minute from all active devices
  const totalEventsRate = devices.reduce((acc, device) => {
    // We don't have direct access to all device metrics here, only activeDeviceData.
    // However, we can approximate or if useTelemetry exposed it.
    // Let's use a simpler heuristic for now: active device * devices count (if mostly uniform)
    // OR better: useTelemetry should probably return a map of latest metrics.
    // For now, let's use the active device's request rate * number of devices as a rough dynamic proxy
    // or just the active one if that's what we see.
    // Wait, useTelemetry has latestPoint for active device.
    if (latestPoint) return latestPoint.requests
    return 0
  }, 0)

  // Better estimation if we want "Global" events:
  // Since we don't have all data, let's just use the active device's rate for the demo
  // or randomize it slightly to look alive if 0.
  const eventsRate = latestPoint ? latestPoint.requests : 0

  const topbarStats = {
    eventsRate: eventsRate,
    activeAlerts: alertStats.active,
    blockedCount: blockedCount
  }

  useEffect(() => {
    setConnectionStatus(isConnected ? 'connected' : 'disconnected')
  }, [isConnected])

  return (
    <div className="h-screen bg-background-primary flex flex-col overflow-hidden">
      <Topbar connectionStatus={connectionStatus} stats={topbarStats} />

      <main className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 flex overflow-hidden">
          <aside className="w-72 xl:w-80 border-r border-white/5 p-4 overflow-hidden flex-shrink-0 hidden lg:block">
            <ThreatMapPanel
              devices={devices}
              activeDeviceId={activeDeviceId}
              onSelectDevice={setActiveDeviceId}
            />
          </aside>

          <section className="flex-1 p-4 overflow-hidden min-w-0">
            <div className="h-full glass-panel p-4 flex flex-col">
              <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/5">
                <button
                  onClick={() => setActiveView('telemetry')}
                  className={`px-3 py-1.5 rounded-glass text-caption font-medium transition-all ${
                    activeView === 'telemetry'
                      ? 'bg-accent-cyan/20 text-accent-cyan'
                      : 'text-text-muted hover:text-text-secondary'
                  }`}
                >
                  <svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
                  Telemetry
                </button>
                <button
                  onClick={() => setActiveView('timeline')}
                  className={`px-3 py-1.5 rounded-glass text-caption font-medium transition-all ${
                    activeView === 'timeline'
                      ? 'bg-accent-cyan/20 text-accent-cyan'
                      : 'text-text-muted hover:text-text-secondary'
                  }`}
                >
                  <svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                  Timeline
                </button>
                <button
                  onClick={() => setActiveView('iot-fleet')}
                  className={`px-3 py-1.5 rounded-glass text-caption font-medium transition-all ${
                    activeView === 'iot-fleet'
                      ? 'bg-accent-cyan/20 text-accent-cyan'
                      : 'text-text-muted hover:text-text-secondary'
                  }`}
                >
                  <svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" /></svg>
                  IoT Fleet
                </button>
                <button
                  onClick={() => setActiveView('response')}
                  className={`px-3 py-1.5 rounded-glass text-caption font-medium transition-all ${
                    activeView === 'response'
                      ? 'bg-accent-green/20 text-accent-green'
                      : 'text-text-muted hover:text-text-secondary'
                  }`}
                >
                  <svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
                  Response
                </button>
                <button
                  onClick={() => setActiveView('dropped')}
                  className={`px-3 py-1.5 rounded-glass text-caption font-medium transition-all ${
                    activeView === 'dropped'
                      ? 'bg-status-critical/20 text-status-critical'
                      : 'text-text-muted hover:text-text-secondary'
                  }`}
                >
                  <svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" /></svg>
                  Dropped {blockedCount > 0 && <span className="ml-1 px-1.5 py-0.5 rounded-full bg-status-critical/30 text-xs">{blockedCount}</span>}
                </button>
              </div>

              <div className="flex-1 min-h-0">
                {activeView === 'telemetry' ? (
                  <TelemetryChart
                    data={telemetryData}
                    latestPoint={latestPoint}
                    isPaused={isPaused}
                    onTogglePause={toggle}
                    devices={devices}
                    activeDeviceId={activeDeviceId}
                    onSelectDevice={setActiveDeviceId}
                  />
                ) : activeView === 'iot-fleet' ? (
                  <IoTMapPanel latestPoint={latestPoint} />
                ) : activeView === 'response' ? (
                  <ResponseStatusPanel />
                ) : activeView === 'dropped' ? (
                  <DroppedPacketsPanel
                    droppedPackets={droppedPackets}
                    stats={droppedStats}
                  />
                ) : (
                  <TimelinePanel />
                )}
              </div>
            </div>
          </section>

          <aside className="w-96 xl:w-[450px] border-l border-white/5 p-4 overflow-hidden flex-shrink-0 hidden md:block">
            <AlertsPanel alertsData={alertsData} />
          </aside>
        </div>

        <div className="border-t border-white/5 flex-shrink-0">
          <TelemetryTerminal
            events={rawEvents}
            isPaused={isPaused}
            onTogglePause={toggle}
            onClear={clearData}
          />
        </div>
      </main>

      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-background-secondary border-t border-white/5 px-4 py-2">
        <div className="flex justify-around">
          <MobileNavItem icon="map" label="Map" active />
          <MobileNavItem icon="chart" label="Telemetry" />
          <MobileNavItem icon="alert" label="Alerts" badge={3} />
          <MobileNavItem icon="log" label="Log" />
        </div>
      </nav>

      <DemoControlPanel />
    </div>
  )
}

function MobileNavItem({ icon, label, active = false, badge = null }) {
  return (
    <button className={`flex flex-col items-center gap-1 px-4 py-1 relative ${
      active ? 'text-accent-cyan' : 'text-text-muted'
    }`}>
      <span className="text-lg">{icon}</span>
      <span className="text-caption">{label}</span>
      {badge && (
        <span className="absolute -top-1 right-1 w-4 h-4 rounded-full bg-status-warning text-xs flex items-center justify-center">
          {badge}
        </span>
      )}
    </button>
  )
}

export default App
