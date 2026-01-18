import React, { useState, useEffect, useRef } from 'react'

const API_GATEWAY_URL = 'http://localhost:3001'

const DroppedPacketsPanel = ({ droppedPackets = [], stats = {} }) => {
  const [packets, setPackets] = useState([])
  const [localStats, setLocalStats] = useState({
    total_dropped: 0,
    by_type: {}
  })
  const [isLive, setIsLive] = useState(true)
  const listRef = useRef(null)

  // Merge props with local state
  useEffect(() => {
    if (droppedPackets.length > 0) {
      setPackets(prev => {
        const newPackets = [...droppedPackets, ...prev]
        // Keep only last 100 packets
        return newPackets.slice(0, 100)
      })
    }
  }, [droppedPackets])

  useEffect(() => {
    if (Object.keys(stats).length > 0) {
      setLocalStats(stats)
    }
  }, [stats])

  // Fetch initial data and poll for updates
  useEffect(() => {
    const fetchDropped = async () => {
      try {
        const res = await fetch(`${API_GATEWAY_URL}/ip/dropped?limit=50`)
        if (res.ok) {
          const data = await res.json()
          setPackets(data.packets || [])
          setLocalStats(data.stats || { total_dropped: 0, by_type: {} })
        }
      } catch (err) {
        console.error('Failed to fetch dropped packets:', err)
      }
    }

    fetchDropped()
    const interval = setInterval(fetchDropped, 3000) // Poll every 3 seconds
    return () => clearInterval(interval)
  }, [])

  // Auto-scroll to top when new packets arrive
  useEffect(() => {
    if (isLive && listRef.current) {
      listRef.current.scrollTop = 0
    }
  }, [packets, isLive])

  const getAttackIcon = (type) => {
    switch (type) {
      case 'sql_injection': return <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" /></svg>
      case 'brute_force': return <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" /></svg>
      case 'flooding': return <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
      case 'blocked_ip': return <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" /></svg>
      case 'rate_limit': return <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
      case 'xss': return <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>
      default: return <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
    }
  }

  const getAttackColor = (type) => {
    switch (type) {
      case 'sql_injection': return 'text-red-400 bg-red-400/10 border-red-400/30'
      case 'brute_force': return 'text-orange-400 bg-orange-400/10 border-orange-400/30'
      case 'flooding': return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30'
      case 'blocked_ip': return 'text-purple-400 bg-purple-400/10 border-purple-400/30'
      case 'rate_limit': return 'text-blue-400 bg-blue-400/10 border-blue-400/30'
      case 'xss': return 'text-pink-400 bg-pink-400/10 border-pink-400/30'
      default: return 'text-gray-400 bg-gray-400/10 border-gray-400/30'
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'text-red-500'
      case 'high': return 'text-orange-500'
      case 'medium': return 'text-yellow-500'
      case 'low': return 'text-green-500'
      default: return 'text-gray-500'
    }
  }

  const formatTime = (timestamp) => {
    if (!timestamp) return '--:--:--'
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', { hour12: false })
  }

  const formatAttackType = (type) => {
    return type?.replace(/_/g, ' ').toUpperCase() || 'UNKNOWN'
  }

  const totalDropped = localStats.total_dropped || 0
  const byType = localStats.by_type || {}

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
            <svg className="w-6 h-6 text-accent-green" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
            DROPPED PACKETS
          </h2>
          <p className="text-caption text-text-muted mt-1">
            <span className="text-status-critical font-bold">{totalDropped}</span> requests blocked
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsLive(!isLive)}
            className={`px-3 py-1.5 rounded-glass text-caption font-medium transition-all ${
              isLive
                ? 'bg-accent-green/20 text-accent-green border border-accent-green/30'
                : 'bg-white/5 text-text-muted border border-white/10'
            }`}
          >
            {isLive ? (
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-accent-green animate-pulse"></span>
                LIVE
              </span>
            ) : (
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full border border-current"></span>
                PAUSED
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2 mb-4">
        {[
          { type: 'sql_injection', label: 'SQL Injection' },
          { type: 'brute_force', label: 'Brute Force' },
          { type: 'flooding', label: 'Flooding' },
          { type: 'blocked_ip', label: 'Blocked IP' },
          { type: 'rate_limit', label: 'Rate Limited' },
          { type: 'xss', label: 'XSS' }
        ].map(({ type, label }) => (
          <div
            key={type}
            className={`glass-panel p-2 border ${getAttackColor(type)} rounded-lg`}
          >
            <div className="flex items-center gap-1.5 mb-1">
              <span className="text-lg">{getAttackIcon(type)}</span>
              <span className="text-[10px] uppercase tracking-wider opacity-70">{label}</span>
            </div>
            <div className="text-xl font-bold font-mono">
              {byType[type] || 0}
            </div>
          </div>
        ))}
      </div>

      {/* Live Feed */}
      <div className="flex-1 glass-panel p-3 overflow-hidden flex flex-col">
        <div className="flex items-center justify-between mb-2 pb-2 border-b border-white/5">
          <span className="text-xs uppercase text-text-muted tracking-widest">Live Feed</span>
          <span className="text-xs text-text-muted">{packets.length} events</span>
        </div>

        {packets.length === 0 ? (
          <div className="flex-1 flex items-center justify-center text-text-muted flex-col gap-2">
            <svg className="w-12 h-12 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
            <p>No dropped packets yet</p>
            <p className="text-xs">Attacks will appear here when blocked</p>
          </div>
        ) : (
          <div
            ref={listRef}
            className="flex-1 overflow-y-auto space-y-2 pr-2"
          >
            {packets.map((packet, index) => (
              <div
                key={`${packet.timestamp}-${index}`}
                className={`p-2 rounded-lg border ${getAttackColor(packet.attack_type)} animate-fadeIn`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{getAttackIcon(packet.attack_type)}</span>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm font-bold">
                          {packet.source_ip}
                        </span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded border ${getSeverityColor(packet.severity)} border-current bg-current/10`}>
                          {packet.severity?.toUpperCase()}
                        </span>
                      </div>
                      <div className="text-xs opacity-70 mt-0.5">
                        <span className="font-medium">{formatAttackType(packet.attack_type)}</span>
                        <svg className="w-3 h-3 mx-1 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                        <span className="font-mono">{packet.endpoint}</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-mono text-xs text-text-muted">
                      {formatTime(packet.timestamp)}
                    </div>
                    <div className={`text-[10px] uppercase tracking-wider ${
                      packet.reason === 'blocked' ? 'text-status-critical' : 'text-status-warning'
                    }`}>
                      {packet.reason}
                    </div>
                  </div>
                </div>

                {/* Details row */}
                {packet.details && Object.keys(packet.details).length > 0 && (
                  <div className="mt-2 pt-2 border-t border-current/20 text-xs opacity-60">
                    {packet.details.pattern && (
                      <span className="font-mono">Pattern: {packet.details.pattern}</span>
                    )}
                    {packet.details.rate && (
                      <span className="font-mono">Rate: {packet.details.rate.toFixed(1)} req/s</span>
                    )}
                    {packet.details.attempt_count && (
                      <span className="font-mono">Attempts: {packet.details.attempt_count}</span>
                    )}
                    {packet.details.confidence && (
                      <span className="font-mono ml-2">Confidence: {packet.details.confidence}%</span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="mt-2 flex items-center justify-between text-xs text-text-muted">
        <span className="flex items-center gap-1">
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
          All malicious requests are logged and blocked at the API Gateway
        </span>
        <span className="font-mono">Gateway: localhost:3001</span>
      </div>
    </div>
  )
}

export default DroppedPacketsPanel
