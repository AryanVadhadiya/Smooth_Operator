import React from 'react'

const IoTMapPanel = ({ latestPoint }) => {
  const devices = latestPoint?.devices || {}
  const sector = latestPoint?.sector || 'Unknown'
  const deviceCount = Object.keys(devices).length

  return (
    <div className="h-full flex flex-col">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
            <span className="text-2xl">
                {sector === 'healthcare' ? '🏥' : sector === 'agriculture' ? '🌾' : '🚦'}
            </span>
            {sector.toUpperCase()} NODE
          </h2>
          <p className="text-caption text-text-muted mt-1">
            Tracking <span className="text-accent-cyan font-bold">{deviceCount}</span> active sub-devices via Gateway
          </p>
        </div>
        <div className="px-3 py-1 rounded-full bg-accent-green/10 border border-accent-green/30 text-accent-green text-xs font-bold animate-pulse">
            GATEWAY ONLINE
        </div>
      </div>

      {deviceCount === 0 ? (
        <div className="flex-1 flex items-center justify-center text-text-muted flex-col gap-2">
          <div className="text-4xl opacity-50">📡</div>
          <p>Waiting for Telemetry...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 overflow-y-auto pr-2">
          {Object.entries(devices).map(([id, info]) => {
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
               <div key={id} className="glass-panel p-4 border border-white/5 relative overflow-hidden group hover:border-white/20 transition-all">
                  <div className="flex justify-between items-start mb-3">
                      <div className="flex items-center gap-2">
                          <div className={`w-2 h-2 rounded-full ${barColor} animate-pulse`}></div>
                          <span className="font-mono text-sm text-text-secondary">{id}</span>
                      </div>
                      <span className={`text-[10px] font-bold border px-1.5 py-0.5 rounded ${statusColor} border-current opacity-80`}>
                          {info.type.toUpperCase()}
                      </span>
                  </div>

                  {/* Health Bar */}
                  <div className="space-y-1">
                      <div className="flex justify-between text-xs">
                          <span className="text-text-muted">Integrity</span>
                          <span className={`font-mono ${statusColor}`}>{health}%</span>
                      </div>
                      <div className="h-2 w-full bg-background-primary rounded-full overflow-hidden">
                          <div
                             className={`h-full ${barColor} transition-all duration-500`}
                             style={{ width: `${health}%` }}
                          />
                      </div>
                  </div>

                  <div className={`mt-4 text-xs font-bold text-center py-1 rounded bg-white/5 ${statusColor}`}>
                      STATUS: {statusText}
                  </div>
               </div>
             )
          })}
        </div>
      )}
    </div>
  )
}

export default IoTMapPanel
