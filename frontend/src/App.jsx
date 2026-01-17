import { useState, useEffect } from 'react'

import Topbar from './components/layout/Topbar'

import ThreatMapPanel from './components/panels/ThreatMapPanel'
import TimelinePanel from './components/panels/TimelinePanel'
import AlertsPanel from './components/panels/AlertsPanel'
import TelemetryTerminal from './components/panels/TelemetryTerminal'
import DemoControlPanel from './components/panels/DemoControlPanel'

import TelemetryChart from './components/charts/TelemetryChart'

import useTelemetry from './hooks/useTelemetry'

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

  useEffect(() => {
    setConnectionStatus(isConnected ? 'connected' : 'disconnected')
  }, [isConnected])

  return (
    <div className="min-h-screen bg-background-primary flex flex-col">
      <Topbar connectionStatus={connectionStatus} />

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
                  📊 Telemetry
                </button>
                <button
                  onClick={() => setActiveView('timeline')}
                  className={`px-3 py-1.5 rounded-glass text-caption font-medium transition-all ${
                    activeView === 'timeline'
                      ? 'bg-accent-cyan/20 text-accent-cyan'
                      : 'text-text-muted hover:text-text-secondary'
                  }`}
                >
                  ⚡ Timeline
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
                ) : (
                  <TimelinePanel />
                )}
              </div>
            </div>
          </section>

          <aside className="w-80 xl:w-96 border-l border-white/5 p-4 overflow-hidden flex-shrink-0 hidden md:block">
            <AlertsPanel />
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
          <MobileNavItem icon="◎" label="Map" active />
          <MobileNavItem icon="📊" label="Telemetry" />
          <MobileNavItem icon="⚠" label="Alerts" badge={3} />
          <MobileNavItem icon="◈" label="Log" />
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
