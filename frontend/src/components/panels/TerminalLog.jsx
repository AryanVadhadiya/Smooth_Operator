import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

// ============================================
// TerminalLog Component
// Terminal-style log output with colored entries
// ============================================

const logLevels = {
  INFO: { color: 'text-text-secondary', prefix: '[INFO]' },
  WARN: { color: 'text-status-warning', prefix: '[WARN]' },
  ERROR: { color: 'text-status-critical', prefix: '[ERROR]' },
  SUCCESS: { color: 'text-status-normal', prefix: '[OK]' },
  DEBUG: { color: 'text-text-muted', prefix: '[DEBUG]' },
  SYSTEM: { color: 'text-accent-cyan', prefix: '[SYSTEM]' },
}

// Initial log entries
const initialLogs = [
  { id: 1, level: 'SYSTEM', message: 'Threat_Ops.ai initialized', timestamp: Date.now() - 60000 },
  { id: 2, level: 'INFO', message: 'Connected to ingest service at 10.0.1.1:8080', timestamp: Date.now() - 55000 },
  { id: 3, level: 'INFO', message: 'Detection engine online - 12 rules loaded', timestamp: Date.now() - 50000 },
  { id: 4, level: 'SUCCESS', message: 'All 8 devices reporting healthy', timestamp: Date.now() - 45000 },
  { id: 5, level: 'INFO', message: 'Alert manager ready', timestamp: Date.now() - 40000 },
  { id: 6, level: 'WARN', message: 'High latency detected on Database Cluster (245ms)', timestamp: Date.now() - 35000 },
  { id: 7, level: 'INFO', message: 'Response engine armed - 4 playbooks active', timestamp: Date.now() - 30000 },
  { id: 8, level: 'ERROR', message: 'SSH brute force detected from 45.33.32.156', timestamp: Date.now() - 25000 },
  { id: 9, level: 'SUCCESS', message: 'IP 45.33.32.156 blocked via firewall rule #127', timestamp: Date.now() - 20000 },
  { id: 10, level: 'INFO', message: 'Telemetry stream active - 2847 events/min', timestamp: Date.now() - 15000 },
]

// Random log generator
const generateRandomLog = (id) => {
  const logs = [
    { level: 'INFO', msg: 'Heartbeat received from edge gateway' },
    { level: 'INFO', msg: 'SSL handshake completed' },
    { level: 'DEBUG', msg: 'Cache hit ratio: 94.2%' },
    { level: 'INFO', msg: 'Telemetry batch processed (128 events)' },
    { level: 'WARN', msg: 'Connection retry to backup server' },
    { level: 'SUCCESS', msg: 'Device authentication verified' },
    { level: 'INFO', msg: 'Rule evaluation completed in 12ms' },
    { level: 'DEBUG', msg: 'Memory usage: 2.1GB / 8GB' },
    { level: 'INFO', msg: 'API request processed: GET /api/status' },
    { level: 'WARN', msg: 'Rate limit threshold at 80%' },
  ]
  const selected = logs[Math.floor(Math.random() * logs.length)]
  return {
    id,
    level: selected.level,
    message: selected.msg,
    timestamp: Date.now(),
  }
}

export default function TerminalLog() {
  const [logs, setLogs] = useState(initialLogs)
  const [isPaused, setIsPaused] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)
  const scrollRef = useRef(null)
  const logIdRef = useRef(initialLogs.length + 1)

  // Add new logs periodically
  useEffect(() => {
    if (isPaused) return

    const interval = setInterval(() => {
      setLogs(prev => {
        const newLog = generateRandomLog(logIdRef.current++)
        return [...prev.slice(-99), newLog] // Keep last 100 logs
      })
    }, 2000)

    return () => clearInterval(interval)
  }, [isPaused])

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current && !isPaused) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [logs, isPaused])

  const formatTime = (timestamp) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3
    })
  }

  const clearLogs = () => {
    setLogs([{
      id: logIdRef.current++,
      level: 'SYSTEM',
      message: 'Log cleared',
      timestamp: Date.now(),
    }])
  }

  return (
    <div className={`flex flex-col transition-all duration-300 ${isExpanded ? 'h-80' : 'h-40'}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-background-secondary border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-status-critical/80"></span>
            <span className="w-3 h-3 rounded-full bg-status-warning/80"></span>
            <span className="w-3 h-3 rounded-full bg-status-normal/80"></span>
          </div>
          <span className="text-caption text-text-muted font-mono">system.log</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-caption text-text-muted">{logs.length} entries</span>
          <button
            onClick={() => setIsPaused(!isPaused)}
            className={`p-1 rounded transition-colors ${
              isPaused
                ? 'bg-status-warning/20 text-status-warning'
                : 'hover:bg-surface-glass-hover text-text-muted'
            }`}
            title={isPaused ? 'Resume' : 'Pause'}
          >
            {isPaused ? <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg> : <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
          </button>
          <button
            onClick={clearLogs}
            className="p-1 rounded hover:bg-surface-glass-hover text-text-muted transition-colors"
            title="Clear"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
          </button>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 rounded hover:bg-surface-glass-hover text-text-muted transition-colors"
            title={isExpanded ? 'Collapse' : 'Expand'}
          >
            {isExpanded ? <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg> : <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" /></svg>}
          </button>
        </div>
      </div>

      {/* Log Output */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto bg-[#0d1117] p-2 font-mono text-xs"
      >
        <AnimatePresence>
          {logs.map((log) => {
            const config = logLevels[log.level] || logLevels.INFO
            return (
              <motion.div
                key={log.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex gap-2 py-0.5 hover:bg-white/5"
              >
                <span className="text-text-muted shrink-0">{formatTime(log.timestamp)}</span>
                <span className={`shrink-0 ${config.color}`}>{config.prefix}</span>
                <span className="text-text-secondary">{log.message}</span>
              </motion.div>
            )
          })}
        </AnimatePresence>

        {/* Cursor blink */}
        {!isPaused && (
          <motion.span
            className="inline-block w-2 h-4 bg-accent-cyan ml-1"
            animate={{ opacity: [1, 0, 1] }}
            transition={{ duration: 1, repeat: Infinity }}
          />
        )}
      </div>
    </div>
  )
}
