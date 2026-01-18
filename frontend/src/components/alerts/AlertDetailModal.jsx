import { memo, useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const RESPONSE_ENGINE_URL = 'http://localhost:8004'

const severityConfig = {
  critical: {
    color: 'text-status-critical',
    bg: 'bg-status-critical/10',
    border: 'border-status-critical/30',
    icon: '',
    label: 'Critical',
  },
  warning: {
    color: 'text-status-warning',
    bg: 'bg-status-warning/10',
    border: 'border-status-warning/30',
    icon: '',
    label: 'Warning',
  },
  normal: {
    color: 'text-status-normal',
    bg: 'bg-status-normal/10',
    border: 'border-status-normal/30',
    icon: '',
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
  const [isRunningPlaybook, setIsRunningPlaybook] = useState(false)
  const [playbookResult, setPlaybookResult] = useState(null)

  const handleRunPlaybook = async () => {
    if (!alert || isRunningPlaybook) return

    setIsRunningPlaybook(true)
    setPlaybookResult(null)

    try {
      const res = await fetch(`${RESPONSE_ENGINE_URL}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: alert.id,
          title: alert.title,
          description: alert.description || '',
          severity: alert.severity,
          source: alert.source,
          timestamp: alert.timestamp,
          evidence: alert.evidence || {},
          recommendation: alert.recommendation || '',
          rule_id: alert.rule_id || 'manual_response',
        })
      })

      if (res.ok) {
        const data = await res.json()
        setPlaybookResult({
          success: true,
          actionsExecuted: data.actions_executed || 0,
          actions: data.actions || []
        })

        // Auto-acknowledge the alert after running playbook
        if (onAcknowledge) {
          onAcknowledge(alert.id)
        }
      } else {
        setPlaybookResult({ success: false, error: 'Failed to execute playbook' })
      }
    } catch (err) {
      console.error('Playbook execution error:', err)
      setPlaybookResult({ success: false, error: err.message })
    } finally {
      setIsRunningPlaybook(false)
    }
  }

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
                        <span className="text-caption text-status-normal flex items-center gap-1">
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                          Acknowledged
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 rounded-glass hover:bg-surface-glass-hover transition-colors text-text-muted"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
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

              {/* Playbook Execution Result */}
              {playbookResult && (
                <section>
                  <h3 className="text-caption text-text-muted uppercase tracking-wider mb-2">
                    Playbook Result
                  </h3>
                  <div className={`glass-card p-3 border-l-2 ${
                    playbookResult.success ? 'border-accent-green' : 'border-status-critical'
                  }`}>
                    {playbookResult.success ? (
                      <>
                        <p className="text-body text-accent-green mb-2 flex items-center gap-2">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                          Executed {playbookResult.actionsExecuted} action(s)
                        </p>
                        {playbookResult.actions?.length > 0 && (
                          <div className="space-y-1 text-sm">
                            {playbookResult.actions.map((action, i) => (
                              <div key={i} className="flex items-center gap-2">
                                <span className={action.status === 'success' ? 'text-accent-green' : 'text-status-warning'}>
                                  {action.status === 'success' ? <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg> : <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" /></svg>}
                                </span>
                                <span className="text-text-secondary">{action.message}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </>
                    ) : (
                      <p className="text-body text-status-critical flex items-center gap-2">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        {playbookResult.error || 'Playbook execution failed'}
                      </p>
                    )}
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
                      className="btn-primary flex items-center gap-1"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                      Acknowledge
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
                <button
                  onClick={handleRunPlaybook}
                  disabled={isRunningPlaybook}
                  className={`btn-ghost flex items-center gap-2 ${
                    isRunningPlaybook ? 'opacity-50 cursor-not-allowed' : 'hover:bg-accent-green/20'
                  }`}
                >
                  {isRunningPlaybook ? (
                    <>
                      <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                      Running...
                    </>
                  ) : (
                    <>
                      Run Playbook
                    </>
                  )}
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
