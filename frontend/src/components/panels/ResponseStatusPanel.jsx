import React, { useState, useEffect } from 'react'

const RESPONSE_ENGINE_URL = 'http://localhost:8004'

function ResponseStatusPanel() {
  const [status, setStatus] = useState(null)
  const [actions, setActions] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchStatus = async () => {
    try {
      const [statusRes, actionsRes] = await Promise.all([
        fetch(`${RESPONSE_ENGINE_URL}/status`),
        fetch(`${RESPONSE_ENGINE_URL}/actions?limit=10`)
      ])

      if (!statusRes.ok || !actionsRes.ok) throw new Error('Failed to fetch')

      const statusData = await statusRes.json()
      const actionsData = await actionsRes.json()

      setStatus(statusData)
      setActions(actionsData.actions || [])
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 5000)
    return () => clearInterval(interval)
  }, [])

  const handleUnblock = async (ip) => {
    try {
      await fetch(`${RESPONSE_ENGINE_URL}/block/${ip}`, { method: 'DELETE' })
      fetchStatus()
    } catch (err) {
      console.error('Failed to unblock:', err)
    }
  }

  const handleRestore = async (service) => {
    try {
      await fetch(`${RESPONSE_ENGINE_URL}/isolate/${service}`, { method: 'DELETE' })
      fetchStatus()
    } catch (err) {
      console.error('Failed to restore:', err)
    }
  }

  const getActionIcon = (type) => {
    const icons = {
      block_ip: <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" /></svg>,
      throttle: <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
      isolate_service: <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>,
      alert_only: <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>,
    }
    return icons[type] || <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
  }

  const getActionColor = (status) => {
    if (status === 'success') return 'text-accent-green'
    if (status === 'failed') return 'text-status-critical'
    if (status === 'skipped') return 'text-text-muted'
    return 'text-status-warning'
  }

  const handleClearAll = async () => {
    if (!confirm('Clear all blocked IPs, rate limits, and service isolations?')) return
    try {
      await fetch(`${RESPONSE_ENGINE_URL}/reset`, { method: 'DELETE' })
      fetchStatus()
    } catch (err) {
      console.error('Failed to reset:', err)
    }
  }

  const [manualIp, setManualIp] = useState('')
  const [throttleIp, setThrottleIp] = useState('')

  const handleManualBlock = async (e) => {
    e.preventDefault()
    if (!manualIp) return
    try {
      await fetch(`${RESPONSE_ENGINE_URL}/block/${manualIp}`, { method: 'POST' })
      setManualIp('')
      fetchStatus()
    } catch (err) {
      console.error('Failed to block:', err)
    }
  }

  const handleManualThrottle = async (e) => {
    e.preventDefault()
    if (!throttleIp) return
    try {
      await fetch(`${RESPONSE_ENGINE_URL}/throttle/${throttleIp}?limit=10`, { method: 'POST' })
      setThrottleIp('')
      fetchStatus()
    } catch (err) {
      console.error('Failed to throttle:', err)
    }
  }

  const handleRemoveThrottle = async (ip) => {
    try {
      await fetch(`${RESPONSE_ENGINE_URL}/throttle/${ip}`, { method: 'DELETE' })
      fetchStatus()
    } catch (err) {
      console.error('Failed to remove throttle:', err)
    }
  }

  if (isLoading) {
    return (
      <div className="glass-panel p-4 h-full flex items-center justify-center">
        <svg className="w-8 h-8 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
      </div>
    )
  }

  if (error) {
    return (
      <div className="glass-panel p-4">
        <div className="text-status-critical text-center">
          <svg className="w-8 h-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          <div className="text-sm">{error}</div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4 h-full overflow-y-auto">
      {/* Active Protections Summary */}
      <div className="glass-panel p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold text-text-primary flex items-center gap-2">
            <span></span> Active Protections
          </h3>
          <button
            onClick={handleClearAll}
            className="text-xs px-2 py-1 rounded bg-status-critical/20 text-status-critical hover:bg-status-critical/30 transition-colors flex items-center gap-1"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
            Clear All
          </button>
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-status-critical/10 p-3 rounded-lg text-center">
            <div className="text-2xl font-bold text-status-critical">{status?.blocked_ips?.length || 0}</div>
            <div className="text-xs text-text-muted">Blocked IPs</div>
          </div>
          <div className="bg-status-warning/10 p-3 rounded-lg text-center">
            <div className="text-2xl font-bold text-status-warning">{Object.keys(status?.throttled_ips || {}).length || 0}</div>
            <div className="text-xs text-text-muted">Rate Limited</div>
          </div>
          <div className="bg-accent-purple/10 p-3 rounded-lg text-center">
            <div className="text-2xl font-bold text-accent-purple">{status?.isolated_services?.length || 0}</div>
            <div className="text-xs text-text-muted">Isolated</div>
          </div>
        </div>
      </div>

      {/* Blocked IPs List */}
      <div className="glass-panel p-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-xs font-bold text-text-muted uppercase">Blocked IPs</h4>
        </div>

        <form onSubmit={handleManualBlock} className="flex gap-2 mb-3">
          <input
            type="text"
            value={manualIp}
            onChange={(e) => setManualIp(e.target.value)}
            placeholder="Enter IP to block..."
            className="flex-1 bg-black/20 border border-white/10 rounded px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:border-status-critical/50"
          />
          <button
            type="submit"
            disabled={!manualIp}
            className="px-3 py-1.5 rounded bg-status-critical/20 text-status-critical hover:bg-status-critical/30 text-sm font-medium transition-colors disabled:opacity-50"
          >
            Block
          </button>
        </form>

        {status?.blocked_ips?.length > 0 ? (
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {status.blocked_ips.map(ip => (
              <div key={ip} className="flex justify-between items-center bg-status-critical/5 px-2 py-1 rounded">
                <span className="font-mono text-sm text-status-critical">{ip}</span>
                <button
                  onClick={() => handleUnblock(ip)}
                  className="text-xs text-text-muted hover:text-white transition-colors flex items-center gap-1"
                >
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                  Unblock
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center text-text-muted text-xs py-2 italic">
            No IPs currently blocked
          </div>
        )}
      </div>

      {/* Rate Limited IPs */}
      <div className="glass-panel p-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-xs font-bold text-text-muted uppercase flex items-center gap-1">
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            Rate Limited IPs
          </h4>
        </div>

        <form onSubmit={handleManualThrottle} className="flex gap-2 mb-3">
          <input
            type="text"
            value={throttleIp}
            onChange={(e) => setThrottleIp(e.target.value)}
            placeholder="Enter IP to throttle..."
            className="flex-1 bg-black/20 border border-white/10 rounded px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:border-status-warning/50"
          />
          <button
            type="submit"
            disabled={!throttleIp}
            className="px-3 py-1.5 rounded bg-status-warning/20 text-status-warning hover:bg-status-warning/30 text-sm font-medium transition-colors disabled:opacity-50"
          >
            Throttle
          </button>
        </form>

        {Object.keys(status?.throttled_ips || {}).length > 0 ? (
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {Object.entries(status.throttled_ips).map(([ip, limit]) => (
              <div key={ip} className="flex justify-between items-center bg-status-warning/5 px-2 py-1 rounded">
                <div>
                  <span className="font-mono text-sm text-status-warning">{ip}</span>
                  <span className="text-xs text-text-muted ml-2">({limit} req/min)</span>
                </div>
                <button
                  onClick={() => handleRemoveThrottle(ip)}
                  className="text-xs text-text-muted hover:text-white transition-colors flex items-center gap-1"
                >
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                  Remove
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center text-text-muted text-xs py-2 italic">
            No IPs currently rate limited
          </div>
        )}
      </div>

      {/* Isolated Services List */}
      {status?.isolated_services?.length > 0 && (
        <div className="glass-panel p-4">
          <h4 className="text-xs font-bold text-text-muted uppercase mb-2 flex items-center gap-1">
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
            Isolated Services
          </h4>
          <div className="space-y-1">
            {status.isolated_services.map(svc => (
              <div key={svc} className="flex justify-between items-center bg-accent-purple/5 px-2 py-1 rounded">
                <span className="font-mono text-sm text-accent-purple">{svc}</span>
                <button
                  onClick={() => handleRestore(svc)}
                  className="text-xs text-text-muted hover:text-accent-green"
                >
                  Restore
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Actions */}
      <div className="glass-panel p-4">
        <h4 className="text-xs font-bold text-text-muted uppercase mb-2 flex items-center gap-1">
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
          Recent Response Actions
        </h4>
        {actions.length === 0 ? (
          <div className="text-center text-text-muted text-sm py-4">
            No response actions yet
          </div>
        ) : (
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {actions.map((action, idx) => (
              <div key={idx} className="flex items-start gap-2 text-xs border-b border-white/5 pb-2">
                <span>{getActionIcon(action.action_type)}</span>
                <div className="flex-1 min-w-0">
                  <div className={getActionColor(action.status)}>{action.message}</div>
                  <div className="text-text-muted font-mono truncate">{action.target}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ResponseStatusPanel
