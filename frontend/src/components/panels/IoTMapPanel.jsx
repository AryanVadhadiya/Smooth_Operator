import React, { useState, useEffect } from 'react'

const API_GATEWAY_URL = 'http://localhost:3001'

const IoTMapPanel = ({ latestPoint }) => {
  const [fleetNodes, setFleetNodes] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [sectorCounts, setSectorCounts] = useState({})

  // Fetch fleet nodes from API Gateway
  useEffect(() => {
    const fetchNodes = async () => {
      try {
        const res = await fetch(`${API_GATEWAY_URL}/nodes`)
        if (!res.ok) throw new Error('Failed to fetch nodes')
        const data = await res.json()
        setFleetNodes(data.nodes || [])
        setSectorCounts(data.sectors || {})
        setError(null)
      } catch (err) {
        setError(err.message)
      } finally {
        setIsLoading(false)
      }
    }

    fetchNodes()
    const interval = setInterval(fetchNodes, 5000) // Refresh every 5s
    return () => clearInterval(interval)
  }, [])

  // Also show virtual devices from telemetry
  const telemetryDevices = latestPoint?.devices || {}
  const telemetrySector = latestPoint?.sector || 'Unknown'

  const getSectorIcon = (sector) => {
    if (sector === 'healthcare') return <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" /></svg>
    if (sector === 'agriculture') return <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
    if (sector === 'urban') return <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
    return <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" /></svg>
  }

  const getStatusColor = (status) => {
    if (status === 'online') return { text: 'text-accent-green', bg: 'bg-accent-green' }
    return { text: 'text-status-critical', bg: 'bg-status-critical' }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
            <svg className="w-6 h-6 text-accent-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" /></svg>
            FLEET NETWORK
          </h2>
          <p className="text-caption text-text-muted mt-1">
            <span className="text-accent-cyan font-bold">{fleetNodes.length}</span> registered nodes across network
          </p>
        </div>
        <div className="flex gap-2">
          {Object.entries(sectorCounts).map(([sector, count]) => (
            <div key={sector} className="px-2 py-1 rounded-full bg-white/5 border border-white/10 text-xs">
              {getSectorIcon(sector)} {count}
            </div>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="flex-1 flex items-center justify-center text-text-muted flex-col gap-2">
          <svg className="w-10 h-10 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
          <p>Connecting to API Gateway...</p>
        </div>
      ) : error ? (
        <div className="flex-1 flex items-center justify-center text-status-critical flex-col gap-2">
          <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          <p>{error}</p>
          <p className="text-xs text-text-muted">Is the backend running?</p>
        </div>
      ) : fleetNodes.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-text-muted flex-col gap-2">
          <svg className="w-10 h-10 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" /></svg>
          <p>No nodes registered yet</p>
          <p className="text-xs">Start monitor_server.py on laptops</p>
        </div>
      ) : (
        <div className="space-y-6 overflow-y-auto pr-2">
          {/* Fleet Nodes (Physical Laptops) */}
          <div>
            <h3 className="text-xs uppercase text-text-muted tracking-widest mb-3 border-b border-white/5 pb-2 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
              Physical Nodes
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {fleetNodes.map((node) => {
                const { text: statusColor, bg: statusBg } = getStatusColor(node.status)
                return (
                  <div key={node.node_id} className="glass-panel p-3 border border-white/5 hover:border-white/20 transition-all">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${statusBg} animate-pulse`}></div>
                        <span className="font-mono text-sm text-text-secondary">{node.node_id}</span>
                      </div>
                      <span className="text-xl">{getSectorIcon(node.sector)}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-text-muted">IP:</span>
                        <span className="ml-1 font-mono text-accent-cyan">{node.ip}</span>
                      </div>
                      <div>
                        <span className="text-text-muted">Port:</span>
                        <span className="ml-1 font-mono">{node.port}</span>
                      </div>
                      <div>
                        <span className="text-text-muted">Sector:</span>
                        <span className="ml-1 font-bold uppercase">{node.sector}</span>
                      </div>
                      <div>
                        <span className={`font-bold ${statusColor}`}>{node.status.toUpperCase()}</span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Virtual Devices from Telemetry */}
          {Object.keys(telemetryDevices).length > 0 && (
            <div>
              <h3 className="text-xs uppercase text-text-muted tracking-widest mb-3 border-b border-white/5 pb-2 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
              Virtual IoT Devices ({telemetrySector.toUpperCase()})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {Object.entries(telemetryDevices).map(([id, info]) => {
                  const health = info.health
                  let statusColor = 'text-accent-green'
                  let barColor = 'bg-accent-green'
                  let statusText = 'SECURE'

                  if (health < 70) {
                    statusColor = 'text-status-warning'
                    barColor = 'bg-status-warning'
                    statusText = 'WARNING'
                  }
                  if (health < 30) {
                    statusColor = 'text-status-critical'
                    barColor = 'bg-status-critical'
                    statusText = 'COMPROMISED'
                  }

                  return (
                    <div key={id} className="glass-panel p-3 border border-white/5">
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex items-center gap-2">
                          <div className={`w-2 h-2 rounded-full ${barColor} animate-pulse`}></div>
                          <span className="font-mono text-xs text-text-secondary">{id}</span>
                        </div>
                        <span className={`text-[10px] font-bold border px-1 py-0.5 rounded ${statusColor} border-current`}>
                          {info.type?.toUpperCase()}
                        </span>
                      </div>
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="text-text-muted">Integrity</span>
                          <span className={`font-mono ${statusColor}`}>{health}%</span>
                        </div>
                        <div className="h-1.5 w-full bg-background-primary rounded-full overflow-hidden">
                          <div className={`h-full ${barColor} transition-all duration-500`} style={{ width: `${health}%` }} />
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default IoTMapPanel
