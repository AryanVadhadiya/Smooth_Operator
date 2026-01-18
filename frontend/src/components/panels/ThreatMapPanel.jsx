import { motion } from 'framer-motion'

export default function ThreatMapPanel({
  devices = [],
  activeDeviceId = null,
  onSelectDevice
}) {
  const totalDevices = devices.length

  const onlineCount = totalDevices
  const offlineCount = 0

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-section font-medium text-text-primary flex items-center gap-2">
          <span className="text-accent-purple">
            <svg className="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          </span>
          Connected Nodes
        </h3>
        <span className="text-caption text-text-muted bg-white/5 px-2 py-1 rounded-full">
          {totalDevices} Active
        </span>
      </div>

      <div className="flex-1 space-y-2 overflow-y-auto pr-1">
        {devices.length === 0 ? (
           <div className="flex flex-col items-center justify-center h-40 text-text-muted opacity-50">
             <span className="text-lg font-bold mb-2">MAP</span>
             <span className="text-caption">Scanning for devices...</span>
           </div>
        ) : (
          devices.map((device, index) => {
            const isActive = activeDeviceId === device.id
            return (
              <motion.div
                key={device.id}
                onClick={() => onSelectDevice && onSelectDevice(device.id)}
                className={`p-3 border-l-2 cursor-pointer transition-all relative overflow-hidden group ${
                  isActive
                    ? 'bg-accent-purple/10 border-accent-purple'
                    : 'glass-card-hover border-transparent hover:border-white/20'
                }`}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                {isActive && (
                  <div className="absolute inset-0 bg-accent-purple/5 pointer-events-none" />
                )}

                <div className="flex items-center justify-between mb-1 relative z-10">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${
                      isActive ? 'bg-status-normal shadow-glow-green' : 'bg-status-normal/50'
                    }`}></span>
                    <span className={`text-body font-medium truncate max-w-[180px] ${
                      isActive ? 'text-accent-purple' : 'text-text-primary'
                    }`}>
                      {device.name}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-4 text-caption text-text-muted relative z-10 pl-4">
                  <span className="font-mono text-[10px] opacity-70">{device.id}</span>
                  <span className="text-status-normal">Online</span>
                </div>
              </motion.div>
            )
          })
        )}
      </div>

      <div className="mt-4 pt-3 border-t border-white/5">
        <div className="grid grid-cols-2 gap-2 text-center">
          <div className="glass-card p-2">
            <p className="text-xl font-semibold text-text-primary">{totalDevices}</p>
            <p className="text-caption text-text-muted">Total Nodes</p>
          </div>
          <div className="glass-card p-2">
            <p className="text-xl font-semibold text-status-normal">100%</p>
            <p className="text-caption text-text-muted">Health</p>
          </div>
        </div>
      </div>
    </div>
  )
}
