import { memo, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const severityConfig = {
  critical: {
    color: 'text-status-critical',
    bg: 'bg-status-critical/10',
    border: 'border-status-critical/30',
    icon: '🔴',
    label: 'Critical',
  },
  warning: {
    color: 'text-status-warning',
    bg: 'bg-status-warning/10',
    border: 'border-status-warning/30',
    icon: '🟡',
    label: 'Warning',
  },
  normal: {
    color: 'text-status-normal',
    bg: 'bg-status-normal/10',
    border: 'border-status-normal/30',
    icon: '🟢',
    label: 'Normal',
  },
}

function AlertDetailModal({
  alert,
  isOpen,
  onClose,
  onAcknowledge,
  onDismiss,
}) {
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose()
    }
    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
    }
    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = ''
    }
  }, [isOpen, onClose])

  if (!alert) return null

  const config = severityConfig[alert.severity] || severityConfig.normal

  const formatTimestamp = (iso) => {
    const date = new Date(iso)
    return date.toLocaleString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    })
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed inset-4 md:inset-auto md:top-1/2 md:left-1/2 md:-translate-x-1/2 md:-translate-y-1/2 md:w-[600px] md:max-h-[80vh] z-50 flex flex-col glass-panel overflow-hidden"
          >
            <div className={`p-4 border-b ${config.border} ${config.bg}`}>
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">{config.icon}</span>
                  <div>
                    <h2 className="text-title text-text-primary">{alert.title}</h2>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.color}`}>
                        {config.label}
                      </span>
                      <span className="text-caption text-text-muted">
                        {alert.source}
                      </span>
                      {alert.acknowledged && (
                        <span className="text-caption text-status-normal">✓ Acknowledged</span>
                      )}
                    </div>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 rounded-glass hover:bg-surface-glass-hover transition-colors text-text-muted"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              <section>
                <h3 className="text-caption text-text-muted uppercase tracking-wider mb-2">
                  What Happened
                </h3>
                <p className="text-body text-text-primary">
                  {alert.description}
                </p>
              </section>

              <section>
                <h3 className="text-caption text-text-muted uppercase tracking-wider mb-2">
                  When
                </h3>
                <p className="text-body text-text-primary font-mono">
                  {formatTimestamp(alert.timestamp)}
                </p>
              </section>

              {alert.evidence && (
                <section>
                  <h3 className="text-caption text-text-muted uppercase tracking-wider mb-2">
                    Evidence
                  </h3>
                  <div className="glass-card p-3 space-y-2">
                    {Object.entries(alert.evidence).map(([key, value]) => (
                      <div key={key} className="flex justify-between items-center">
                        <span className="text-caption text-text-muted capitalize">
                          {key.replace(/([A-Z])/g, ' $1').trim()}
                        </span>
                        <span className="text-body text-text-primary font-mono">
                          {typeof value === 'object' ? JSON.stringify(value) : value}
                        </span>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {alert.recommendation && (
                <section>
                  <h3 className="text-caption text-text-muted uppercase tracking-wider mb-2">
                    Recommended Action
                  </h3>
                  <div className="glass-card p-3 border-l-2 border-accent-cyan">
                    <p className="text-body text-text-primary">
                      {alert.recommendation}
                    </p>
                  </div>
                </section>
              )}

              {alert.ruleName && (
                <section>
                  <h3 className="text-caption text-text-muted uppercase tracking-wider mb-2">
                    Detection Rule
                  </h3>
                  <div className="flex items-center gap-2">
                    <span className="text-body text-text-primary">{alert.ruleName}</span>
                    <span className="text-caption text-text-muted font-mono">({alert.ruleId})</span>
                  </div>
                </section>
              )}
            </div>

            <div className="p-4 border-t border-white/5 flex items-center justify-between gap-3">
              <div className="flex gap-2">
                {!alert.acknowledged && (
                  <>
                    <button
                      onClick={() => onAcknowledge?.(alert.id)}
                      className="btn-primary"
                    >
                      ✓ Acknowledge
                    </button>
                    <button
                      onClick={() => {
                        onDismiss?.(alert.id)
                        onClose()
                      }}
                      className="btn-danger"
                    >
                      Dismiss
                    </button>
                  </>
                )}
              </div>

              <div className="flex gap-2">
                <button className="btn-ghost">
                  🛡️ Run Playbook
                </button>
                <button
                  onClick={onClose}
                  className="btn-ghost"
                >
                  Close
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

export default memo(AlertDetailModal)
