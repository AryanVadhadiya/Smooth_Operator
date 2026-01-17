import { memo, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
  ReferenceLine,
} from 'recharts'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null

  const formatTime = (timestamp) => {
    if (!timestamp) return '--:--:--'
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  return (
    <div className="glass-card p-3 border border-white/10">
      <p className="text-caption text-text-muted mb-2 font-mono">{formatTime(label)}</p>
      {payload.map((entry, index) => (
        <div key={index} className="flex items-center gap-2 text-body">
          <span
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-text-secondary">{entry.name}:</span>
          <span className="text-text-primary font-mono">
            {typeof entry.value === 'number' ? entry.value.toFixed(1) : '0'}
            {entry.dataKey === 'cpu' || entry.dataKey === 'memory' ? '%' : ''}
            {entry.dataKey === 'networkScaled' ? ' KB/s' : ''}
          </span>
        </div>
      ))}
    </div>
  )
}

const formatXAxisTick = (timestamp) => {
  if (!timestamp || timestamp === 0) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', {
    hour12: false,
    minute: '2-digit',
    second: '2-digit',
  })
}

function TelemetryChart({
  data = [],
  latestPoint = null,
  isPaused = false,
  onTogglePause,
  devices = [],
  activeDeviceId = null,
  onSelectDevice,
}) {
  const [activeMetrics, setActiveMetrics] = useState({
    cpu: true,
    memory: true,
    network: true,
  })

  const metrics = useMemo(() => [
    { key: 'cpu', label: 'CPU', color: '#22c55e', unit: '%' },
    { key: 'memory', label: 'Memory', color: '#f59e0b', unit: '%' },
    { key: 'network', label: 'Network', color: '#3b82f6', unit: 'KB/s' },
  ], [])

  const chartData = useMemo(() => {
    if (data.length === 0) {
      const now = Date.now()
      return Array.from({ length: 30 }, (_, i) => ({
        timestamp: now - (29 - i) * 2000,
        cpu: 0,
        memory: 0,
        network: 0,
        networkScaled: 0,
      }))
    }

    const maxNetwork = Math.max(...data.map(d => d.network || 0), 100)

    return data.map(point => ({
      ...point,
      timestamp: point.timestamp || Date.now(),
      networkScaled: ((point.network || 0) / maxNetwork) * 100,
    }))
  }, [data])

  const xDomain = useMemo(() => {
    if (chartData.length === 0) {
      const now = Date.now()
      return [now - 60000, now]
    }
    const timestamps = chartData.map(d => d.timestamp).filter(Boolean)
    if (timestamps.length === 0) {
      const now = Date.now()
      return [now - 60000, now]
    }
    const max = Math.max(...timestamps)
    const min = Math.min(...timestamps)
    const range = Math.max(max - min, 30000)
    return [max - range, max]
  }, [chartData])

  const xTicks = useMemo(() => {
    const [min, max] = xDomain
    const range = max - min
    const tickCount = 6
    const step = range / (tickCount - 1)
    return Array.from({ length: tickCount }, (_, i) => Math.round(min + i * step))
  }, [xDomain])

  const toggleMetric = (key) => {
    setActiveMetrics(prev => ({ ...prev, [key]: !prev[key] }))
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="flex-shrink-0 flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <h3 className="text-section font-medium text-text-primary flex items-center gap-2">
            <span className="text-accent-cyan">📊</span>
            System Telemetry
          </h3>

          <div className="flex items-center gap-2">
            {devices.length > 0 ? (
              <div className="flex bg-surface-glass rounded-lg p-1">
                {devices.map(device => (
                  <button
                    key={device.id}
                    onClick={() => onSelectDevice && onSelectDevice(device.id)}
                    className={`px-3 py-1 rounded-md text-caption transition-all ${
                      activeDeviceId === device.id
                        ? 'bg-accent-cyan/20 text-accent-cyan font-medium shadow-sm'
                        : 'text-text-muted hover:text-text-secondary hover:bg-white/5'
                    }`}
                  >
                    {device.name}
                  </button>
                ))}
              </div>
            ) : (
              <span className="text-caption text-text-muted italic">Waiting for devices...</span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-caption text-text-muted">
            {data.length} pts
          </span>
          <div className="flex items-center gap-2">
            <motion.span
              className={`w-2 h-2 rounded-full ${isPaused ? 'bg-status-warning' : 'bg-status-normal'}`}
              animate={isPaused ? {} : { opacity: [1, 0.5, 1] }}
              transition={{ duration: 1, repeat: Infinity }}
            />
            <span className="text-caption text-text-muted">
              {isPaused ? 'Paused' : 'Live'}
            </span>
          </div>
          <button
            onClick={onTogglePause}
            className={`p-1.5 rounded-glass transition-colors ${
              isPaused
                ? 'bg-status-warning/20 text-status-warning'
                : 'hover:bg-surface-glass-hover text-text-secondary'
            }`}
          >
            {isPaused ? '▶' : '⏸'}
          </button>
        </div>
      </div>

      {latestPoint && (
        <div className="flex-shrink-0 grid grid-cols-3 gap-2 mb-3">
          {metrics.map((metric) => (
            <div
              key={metric.key}
              className={`glass-card p-2 cursor-pointer transition-opacity ${
                activeMetrics[metric.key] ? '' : 'opacity-40'
              }`}
              onClick={() => toggleMetric(metric.key)}
            >
              <div className="flex items-center gap-2 mb-0.5">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: metric.color }} />
                <span className="text-xs text-text-muted">{metric.label}</span>
              </div>
              <p
                className="text-lg font-semibold font-mono"
                style={{ color: metric.color }}
              >
                {latestPoint[metric.key]?.toFixed(1) || '0.0'}
                <span className="text-xs ml-1">{metric.unit}</span>
              </p>
            </div>
          ))}
        </div>
      )}

      <div className="flex-1 min-h-0 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={chartData}
            margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
          >
            <defs>
              <linearGradient id="gradientCpu" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gradientMemory" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gradientNetwork" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>

            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(255,255,255,0.08)"
              vertical={true}
              horizontal={true}
            />

            <XAxis
              dataKey="timestamp"
              type="number"
              domain={xDomain}
              ticks={xTicks}
              tickFormatter={formatXAxisTick}
              stroke="#64748b"
              fontSize={10}
              tickLine={false}
              axisLine={{ stroke: 'rgba(255,255,255,0.15)' }}
              tick={{ fill: '#94a3b8' }}
              height={20}
            />

            <YAxis
              stroke="#64748b"
              fontSize={10}
              tickLine={false}
              axisLine={false}
              domain={[0, 100]}
              ticks={[0, 25, 50, 75, 100]}
              tickFormatter={(value) => `${value}%`}
              tick={{ fill: '#94a3b8' }}
              width={35}
            />

            <Tooltip content={<CustomTooltip />} />

            <ReferenceLine y={85} stroke="#f59e0b" strokeDasharray="5 5" strokeOpacity={0.4} />
            <ReferenceLine y={90} stroke="#ef4444" strokeDasharray="5 5" strokeOpacity={0.4} />

            {activeMetrics.cpu && (
              <Area
                type="monotone"
                dataKey="cpu"
                name="CPU"
                stroke="#22c55e"
                strokeWidth={2}
                fill="url(#gradientCpu)"
                dot={false}
                isAnimationActive={false}
                connectNulls
              />
            )}

            {activeMetrics.memory && (
              <Area
                type="monotone"
                dataKey="memory"
                name="Memory"
                stroke="#f59e0b"
                strokeWidth={2}
                fill="url(#gradientMemory)"
                dot={false}
                isAnimationActive={false}
                connectNulls
              />
            )}

            {activeMetrics.network && (
              <Line
                type="monotone"
                dataKey="networkScaled"
                name="Network"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
                connectNulls
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="flex-shrink-0 flex items-center justify-center gap-4 mt-2 pt-2 border-t border-white/5">
        {metrics.map((metric) => (
          <button
            key={metric.key}
            onClick={() => toggleMetric(metric.key)}
            className={`flex items-center gap-1.5 text-xs transition-opacity ${
              activeMetrics[metric.key] ? 'text-text-secondary' : 'text-text-muted opacity-50'
            }`}
          >
            <span className="w-3 h-0.5 rounded" style={{ backgroundColor: metric.color }} />
            {metric.label}
          </button>
        ))}
      </div>
    </div>
  )
}

export default memo(TelemetryChart)
