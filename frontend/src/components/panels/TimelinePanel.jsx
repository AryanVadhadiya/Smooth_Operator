import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const eventTypes = {
  auth: { icon: 'auth', color: 'text-accent-cyan', label: 'Auth' },
  network: { icon: 'network', color: 'text-accent-purple', label: 'Network' },
  device: { icon: 'device', color: 'text-status-info', label: 'Device' },
  alert: { icon: 'alert', color: 'text-status-warning', label: 'Alert' },
  action: { icon: 'action', color: 'text-status-normal', label: 'Action' },
  error: { icon: 'error', color: 'text-status-critical', label: 'Error' },
}

const EventIcon = ({ type }) => {
  const icons = {
    auth: <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>,
    network: <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" /></svg>,
    device: <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" /></svg>,
    alert: <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>,
    action: <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>,
    error: <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
  }
  return icons[type] || icons.network
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
          <svg className="w-5 h-5 text-accent-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
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
            {isPaused ? <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg> : <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
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
                  <span className={`mt-0.5 ${config.color}`}><EventIcon type={event.type} /></span>
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
