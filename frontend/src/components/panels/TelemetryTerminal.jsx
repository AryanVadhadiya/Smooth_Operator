import { useRef, useEffect, useState, memo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const highlightJSON = (obj) => {
  const json = JSON.stringify(obj, null, 2)
  return json
    .replace(/"([^"]+)":/g, '<span class="text-accent-purple">"$1"</span>:')
    .replace(/: "([^"]+)"/g, ': <span class="text-status-normal">"$1"</span>')
    .replace(/: (\d+\.?\d*)/g, ': <span class="text-status-warning">$1</span>')
    .replace(/: (true|false)/g, ': <span class="text-accent-cyan">$1</span>')
}

function TelemetryTerminal({
  events = [],
  isPaused = false,
  onTogglePause,
  onClear,
}) {
  const scrollRef = useRef(null)
  const [isHovered, setIsHovered] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)
  const [viewMode, setViewMode] = useState('compact')

  useEffect(() => {
    if (scrollRef.current && !isHovered && !isPaused) {
      scrollRef.current.scrollTop = 0
    }
  }, [events, isHovered, isPaused])

  const formatTimestamp = (isoString) => {
    const date = new Date(isoString)
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3,
    })
  }

  return (
    <div className={`flex flex-col transition-all duration-300 ${isExpanded ? 'h-80' : 'h-48'}`}>
      <div className="flex items-center justify-between px-3 py-2 bg-background-secondary border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-status-critical/80"></span>
            <span className="w-3 h-3 rounded-full bg-status-warning/80"></span>
            <span className="w-3 h-3 rounded-full bg-status-normal/80"></span>
          </div>
          <span className="text-caption text-text-muted font-mono">telemetry.stream</span>

          <div className="flex items-center gap-1 ml-2 p-0.5 rounded-glass bg-surface-glass">
            <button
              onClick={() => setViewMode('compact')}
              className={`px-2 py-0.5 text-caption rounded transition-colors ${
                viewMode === 'compact'
                  ? 'bg-surface-glass-active text-text-primary'
                  : 'text-text-muted hover:text-text-secondary'
              }`}
            >
              Compact
            </button>
            <button
              onClick={() => setViewMode('json')}
              className={`px-2 py-0.5 text-caption rounded transition-colors ${
                viewMode === 'json'
                  ? 'bg-surface-glass-active text-text-primary'
                  : 'text-text-muted hover:text-text-secondary'
              }`}
            >
              JSON
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-caption text-text-muted">{events.length} events</span>

          <button
            onClick={onTogglePause}
            className={`p-1 rounded transition-colors ${
              isPaused
                ? 'bg-status-warning/20 text-status-warning'
                : 'hover:bg-surface-glass-hover text-text-muted'
            }`}
            title={isPaused ? 'Resume' : 'Pause'}
          >
            {isPaused ? '▶' : '⏸'}
          </button>

          <button
            onClick={onClear}
            className="p-1 rounded hover:bg-surface-glass-hover text-text-muted transition-colors"
            title="Clear"
          >
            🗑
          </button>

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 rounded hover:bg-surface-glass-hover text-text-muted transition-colors"
            title={isExpanded ? 'Collapse' : 'Expand'}
          >
            {isExpanded ? '▼' : '▲'}
          </button>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto bg-[#0d1117] p-2 font-mono text-xs"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <AnimatePresence>
          {events.length === 0 ? (
            <div className="flex items-center justify-center h-full text-text-muted">
              Waiting for telemetry data...
            </div>
          ) : viewMode === 'compact' ? (
            events.map((event) => (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0 }}
                className="py-0.5 hover:bg-white/5 flex gap-2"
              >
                <span className="text-text-muted shrink-0">
                  {formatTimestamp(event.timestamp)}
                </span>
                <span className="text-accent-cyan shrink-0">[{event.deviceId}]</span>
                <span className="text-text-secondary">
                  CPU: <span className="text-status-normal">{event.metrics.cpu.toFixed(1)}%</span>
                  {' | '}
                  MEM: <span className="text-status-warning">{event.metrics.memory.toFixed(1)}%</span>
                  {' | '}
                  NET: <span className="text-status-info">{event.metrics.network.toFixed(0)}KB/s</span>
                  {' | '}
                  REQ: <span className="text-accent-purple">{event.metrics.requests}</span>
                </span>
              </motion.div>
            ))
          ) : (
            events.slice(0, 20).map((event) => (
              <motion.div
                key={event.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mb-2 p-2 rounded bg-white/5"
              >
                <div className="text-text-muted mb-1 text-xs">
                  {formatTimestamp(event.timestamp)} — {event.deviceName}
                </div>
                <pre
                  className="text-xs whitespace-pre-wrap"
                  dangerouslySetInnerHTML={{
                    __html: highlightJSON({
                      deviceId: event.deviceId,
                      metrics: event.metrics,
                    })
                  }}
                />
              </motion.div>
            ))
          )}
        </AnimatePresence>

        {!isPaused && events.length > 0 && (
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

export default memo(TelemetryTerminal)
