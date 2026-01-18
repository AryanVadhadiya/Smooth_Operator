import { memo } from 'react'
import { motion } from 'framer-motion'

const severityConfig = {
  critical: {
    color: 'text-status-critical',
    bg: 'bg-status-critical/10',
    border: 'border-l-status-critical',
    badge: 'bg-status-critical/20 text-status-critical',
    glow: 'shadow-glow-red',
    icon: '',
    label: 'Critical',
  },
  warning: {
    color: 'text-status-warning',
    bg: 'bg-status-warning/10',
    border: 'border-l-status-warning',
    badge: 'bg-status-warning/20 text-status-warning',
    glow: 'shadow-glow-amber',
    icon: '',
    label: 'Warning',
  },
  normal: {
    color: 'text-status-normal',
    bg: 'bg-status-normal/10',
    border: 'border-l-status-normal',
    badge: 'bg-status-normal/20 text-status-normal',
    glow: 'shadow-glow-green',
    icon: '',
    label: 'Normal',
  },
  info: {
    color: 'text-status-info',
    bg: 'bg-status-info/10',
    border: 'border-l-status-info',
    badge: 'bg-status-info/20 text-status-info',
    glow: '',
    icon: '',
    label: 'Info',
  },
}

function AlertCard({
  alert,
  onClick,
  onAcknowledge,
  onDismiss,
  compact = false,
}) {
  const config = severityConfig[alert.severity] || severityConfig.normal

  const getRelativeTime = (timestamp) => {
    const seconds = Math.floor((Date.now() - new Date(timestamp).getTime()) / 1000)
    if (seconds < 60) return `${seconds}s ago`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
    return `${Math.floor(seconds / 86400)}d ago`
  }

  // Get sector badge based on rule_id or evidence
  const getSectorBadge = () => {
    const ruleId = alert.rule_id || ''
    if (ruleId.includes('health') || alert.evidence?.ml_response?.sector === 'healthcare') {
      return { icon: <svg className="w-3 h-3 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" /></svg>, label: 'Healthcare', color: 'bg-pink-500/20 text-pink-400' }
    }
    if (ruleId.includes('agri') || alert.evidence?.ml_response?.sector === 'agriculture') {
      return { icon: <svg className="w-3 h-3 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>, label: 'Agriculture', color: 'bg-green-500/20 text-green-400' }
    }
    if (ruleId.includes('urban') || alert.evidence?.ml_response?.sector === 'urban') {
      return { icon: <svg className="w-3 h-3 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>, label: 'Urban', color: 'bg-cyan-500/20 text-cyan-400' }
    }
    return null
  }

  const sectorBadge = getSectorBadge()

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 20, scale: 0.95 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: -20, scale: 0.95 }}
      whileHover={{ x: 4 }}
      onClick={onClick}
      className={`
        glass-card p-3 border-l-2 cursor-pointer transition-all
        ${config.border}
        ${alert.acknowledged ? 'opacity-50' : ''}
        ${alert.severity === 'critical' && !alert.acknowledged ? 'animate-pulse-slow' : ''}
      `}
    >
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-sm shrink-0">{config.icon}</span>
          <span className={`text-body font-medium truncate ${
            alert.acknowledged ? 'text-text-muted' : 'text-text-primary'
          }`}>
            {alert.title}
          </span>
          {alert.title?.includes('ML:') && (
            <span className="shrink-0 px-1.5 py-0.5 rounded text-[10px] font-bold bg-accent-purple/20 text-accent-purple flex items-center gap-0.5">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
              AI
            </span>
          )}
          {sectorBadge && (
            <span className={`shrink-0 px-1.5 py-0.5 rounded text-[10px] font-bold ${sectorBadge.color}`}>
              {sectorBadge.icon} {sectorBadge.label}
            </span>
          )}
        </div>
        <span className={`shrink-0 px-2 py-0.5 rounded-full text-xs font-medium ${config.badge}`}>
          {config.label}
        </span>
      </div>

      {!compact && (
        <>
          <p className="text-caption text-text-muted mb-2 line-clamp-2">
            {alert.description}
          </p>
          {alert.evidence?.ml_response?.score && (
            <div className="mb-2 text-caption text-accent-cyan">
              Confidence: {(alert.evidence.ml_response.score * 100).toFixed(0)}%
            </div>
          )}
          {(alert.evidence?.action === 'BLOCKED' || alert.action === 'BLOCKED') && (
            <div className="mb-2 px-2 py-1 rounded text-xs font-medium bg-green-500/20 text-green-400 inline-flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              NEUTRALIZED by {alert.evidence?.blocked_by || alert.blocked_by || 'WAF'}
            </div>
          )}
          {(alert.evidence?.action === 'DETECTED' || alert.action === 'DETECTED') && !alert.evidence?.blocked_by && (
            <div className="mb-2 px-2 py-1 rounded text-xs font-medium bg-red-500/20 text-red-400 inline-flex items-center gap-1">
              DETECTED - Slipped Through
            </div>
          )}
        </>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-caption text-text-muted">
          <span>{alert.source}</span>
          <span>•</span>
          <span className="font-mono">{getRelativeTime(alert.timestamp)}</span>
        </div>

        {!alert.acknowledged && (
          <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={() => onAcknowledge?.(alert.id)}
              className="px-2 py-1 text-xs rounded bg-surface-glass-hover hover:bg-surface-glass-active transition-colors flex items-center gap-1"
              title="Acknowledge"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
              Ack
            </button>
            <button
              onClick={() => onDismiss?.(alert.id)}
              className="px-2 py-1 text-xs rounded text-status-critical bg-status-critical/10 hover:bg-status-critical/20 transition-colors flex items-center"
              title="Dismiss"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>
        )}

        {alert.acknowledged && (
          <span className="text-xs text-text-muted">Acknowledged</span>
        )}
      </div>
    </motion.div>
  )
}

export default memo(AlertCard)
