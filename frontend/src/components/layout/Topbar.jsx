import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'

export default function Topbar({ connectionStatus = 'connected', stats }) {
  const [currentTime, setCurrentTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const formatDate = (date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  const statusConfig = {
    connected: { color: 'bg-status-normal', text: 'Connected', glow: 'shadow-glow-green' },
    degraded: { color: 'bg-status-warning', text: 'Degraded', glow: 'shadow-glow-amber' },
    disconnected: { color: 'bg-status-critical', text: 'Disconnected', glow: 'shadow-glow-red' },
  }

  const status = statusConfig[connectionStatus] || statusConfig.connected

  return (
    <header className="h-14 px-4 flex items-center justify-between border-b border-white/5 bg-background-secondary/80 backdrop-blur-lg">
      <div className="flex items-center gap-3">
        <motion.div
          className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-cyan to-accent-purple flex items-center justify-center"
          whileHover={{ scale: 1.05 }}
        >
          <span className="text-white font-bold text-sm">TO</span>
        </motion.div>
        <div>
          <h1 className="text-body font-semibold text-text-primary">Threat_Ops.ai</h1>
          <p className="text-caption text-text-muted -mt-0.5">Security Operations Center</p>
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-glass border border-white/5">
          <motion.span
            className={`w-2 h-2 rounded-full ${status.color} ${status.glow}`}
            animate={{ opacity: [1, 0.5, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          <span className="text-caption text-text-secondary">{status.text}</span>
        </div>

        <div className="hidden md:flex items-center gap-4 text-caption">
          <div className="flex items-center gap-1.5">
            <span className="text-text-muted">Events:</span>
            <span className="text-status-normal font-mono">
              {stats?.eventsRate > 999 ? (stats.eventsRate / 1000).toFixed(1) + 'k' : stats?.eventsRate || '0'}/min
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-text-muted">Alerts:</span>
            <span className={`font-mono ${stats?.activeAlerts > 0 ? 'text-status-warning' : 'text-text-secondary'}`}>
              {stats?.activeAlerts || '0'}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-text-muted">Blocked:</span>
            <span className={`font-mono ${stats?.blockedCount > 0 ? 'text-status-critical' : 'text-text-secondary'}`}>
              {stats?.blockedCount || '0'}
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="text-right hidden sm:block">
          <p className="text-body font-mono text-text-primary tabular-nums">{formatTime(currentTime)}</p>
          <p className="text-caption text-text-muted -mt-0.5">{formatDate(currentTime)}</p>
        </div>

        <div className="flex items-center gap-2">
          <button className="p-2 rounded-glass hover:bg-surface-glass-hover transition-colors" title="Pause Feed">
            <span className="text-text-secondary">⏸</span>
          </button>
          <button className="p-2 rounded-glass hover:bg-surface-glass-hover transition-colors" title="Settings">
            <span className="text-text-secondary">⚙</span>
          </button>
          <button className="btn-primary text-sm py-1.5">
            + Alert
          </button>
        </div>
      </div>
    </header>
  )
}
