import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const eventTypes = {
  auth: { icon: '🔐', color: 'text-accent-cyan', label: 'Auth' },
  network: { icon: '🌐', color: 'text-accent-purple', label: 'Network' },
  device: { icon: '📟', color: 'text-status-info', label: 'Device' },
  alert: { icon: '⚠️', color: 'text-status-warning', label: 'Alert' },
  action: { icon: '🛡️', color: 'text-status-normal', label: 'Action' },
  error: { icon: '❌', color: 'text-status-critical', label: 'Error' },
}

const initialEvents = [
  { id: 1, type: 'auth', message: 'User admin@hospital.local authenticated successfully', source: 'Auth Server', timestamp: Date.now() - 60000 },
  { id: 2, type: 'network', message: 'New connection from 192.168.1.45', source: 'Edge Gateway', timestamp: Date.now() - 55000 },
  { id: 3, type: 'device', message: 'Patient Monitor #3 came online', source: 'IoT Hub', timestamp: Date.now() - 50000 },
  { id: 4, type: 'alert', message: 'Unusual login pattern detected', source: 'Detection Engine', timestamp: Date.now() - 45000 },
  { id: 5, type: 'action', message: 'Rate limiting applied to 10.0.5.88', source: 'Response Engine', timestamp: Date.now() - 40000 },
  { id: 6, type: 'network', message: 'SSL certificate verified for api.hospital.local', source: 'API Gateway', timestamp: Date.now() - 35000 },
  { id: 7, type: 'device', message: 'Database cluster health check passed', source: 'DB Monitor', timestamp: Date.now() - 30000 },
  { id: 8, type: 'error', message: 'Connection timeout to backup server', source: 'Storage', timestamp: Date.now() - 25000 },
]

const generateRandomEvent = (id) => {
  const types = Object.keys(eventTypes)
  const messages = [
    { type: 'auth', msg: 'Authentication attempt from new IP', src: 'Auth Server' },
    { type: 'network', msg: 'Packet inspection completed', src: 'Firewall' },
    { type: 'device', msg: 'Telemetry received from medical device', src: 'IoT Hub' },
    { type: 'alert', msg: 'High CPU usage detected on server', src: 'Monitor' },
    { type: 'action', msg: 'Automated cleanup triggered', src: 'Response Engine' },
    { type: 'network', msg: 'DNS query resolved', src: 'DNS Server' },
    { type: 'device', msg: 'Heartbeat received', src: 'Device Manager' },
    { type: 'auth', msg: 'Session refreshed', src: 'Auth Server' },
  ]
  const selected = messages[Math.floor(Math.random() * messages.length)]
  return {
    id,
    type: selected.type,
    message: selected.msg,
    source: selected.src,
    timestamp: Date.now(),
  }
}

export default function TimelinePanel() {
  const [events, setEvents] = useState(initialEvents)
  const [isPaused, setIsPaused] = useState(false)
  const [isHovered, setIsHovered] = useState(false)
  const scrollRef = useRef(null)
  const eventIdRef = useRef(initialEvents.length + 1)

  useEffect(() => {
    if (isPaused) return

    const interval = setInterval(() => {
      setEvents(prev => {
        const newEvent = generateRandomEvent(eventIdRef.current++)
        const updated = [newEvent, ...prev.slice(0, 49)]
        return updated
      })
    }, 3000)

    return () => clearInterval(interval)
  }, [isPaused])

  useEffect(() => {
    if (scrollRef.current && !isHovered) {
      scrollRef.current.scrollTop = 0
    }
  }, [events, isHovered])

  const formatTime = (timestamp) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const getRelativeTime = (timestamp) => {
    const seconds = Math.floor((Date.now() - timestamp) / 1000)
    if (seconds < 60) return `${seconds}s ago`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    return `${Math.floor(seconds / 3600)}h ago`
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-section font-medium text-text-primary flex items-center gap-2">
          <span className="text-accent-cyan">⚡</span>
          Live Timeline
        </h3>
        <div className="flex items-center gap-2">
          <span className="text-caption text-text-muted">{events.length} events</span>
          <button
            onClick={() => setIsPaused(!isPaused)}
            className={`p-1.5 rounded-glass transition-colors ${
              isPaused
                ? 'bg-status-warning/20 text-status-warning'
                : 'hover:bg-surface-glass-hover text-text-secondary'
            }`}
            title={isPaused ? 'Resume Feed' : 'Pause Feed'}
          >
            {isPaused ? '▶' : '⏸'}
          </button>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-1 pr-1"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <AnimatePresence>
          {events.map((event, index) => {
            const config = eventTypes[event.type] || eventTypes.network
            return (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, y: -20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.2 }}
                className="glass-card-hover p-2.5 cursor-pointer"
              >
                <div className="flex items-start gap-2">
                  <span className="text-sm mt-0.5">{config.icon}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-body text-text-primary truncate">{event.message}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className={`text-caption ${config.color}`}>{config.label}</span>
                      <span className="text-caption text-text-muted">•</span>
                      <span className="text-caption text-text-muted">{event.source}</span>
                      <span className="text-caption text-text-muted ml-auto font-mono">
                        {getRelativeTime(event.timestamp)}
                      </span>
                    </div>
                  </div>
                </div>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>

      <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <motion.span
            className={`w-2 h-2 rounded-full ${isPaused ? 'bg-status-warning' : 'bg-status-normal'}`}
            animate={isPaused ? {} : { opacity: [1, 0.5, 1] }}
            transition={{ duration: 1, repeat: Infinity }}
          />
          <span className="text-caption text-text-muted">
            {isPaused ? 'Feed paused' : 'Live'}
          </span>
        </div>
        <span className="text-caption text-text-muted font-mono">~3 events/sec</span>
      </div>
    </div>
  )
}
