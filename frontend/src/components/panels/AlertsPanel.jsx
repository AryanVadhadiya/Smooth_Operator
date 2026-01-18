import { memo, useState } from 'react'
import { AnimatePresence } from 'framer-motion'
import AlertCard from '@components/alerts/AlertCard'
import AlertDetailModal from '@components/alerts/AlertDetailModal'

const RESPONSE_ENGINE_URL = 'http://localhost:8004'

function AlertsPanel({ alertsData }) {
  const {
    alerts,
    selectedAlert,
    filter,
    stats,
    setFilter,
    setSelectedAlert,
    acknowledgeAlert,
    dismissAlert,
    acknowledgeAll,
    clearAcknowledged,
  } = alertsData

  const [isRunningPlaybook, setIsRunningPlaybook] = useState(false)
  const [playbookResult, setPlaybookResult] = useState(null)

  const runDefensePlaybook = async () => {
    // Get all unacknowledged alerts
    const activeAlerts = alerts.filter(a => !a.acknowledged)
    if (activeAlerts.length === 0) {
      setPlaybookResult({ success: false, message: 'No active alerts to respond to' })
      setTimeout(() => setPlaybookResult(null), 3000)
      return
    }

    setIsRunningPlaybook(true)
    setPlaybookResult(null)

    let totalActions = 0
    let results = []

    for (const alert of activeAlerts) {
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
          totalActions += data.actions_executed || 0
          results.push(...(data.actions || []))
        }
      } catch (err) {
        console.error('Playbook error:', err)
      }
    }

    let msg = ''

    if (totalActions > 0) {
      msg = `Defense Active! Executed ${totalActions} actions on ${activeAlerts.length} alerts.`
    } else {
      msg = `Analysis Complete. ${activeAlerts.length} alerts scanned, no new actions required.`
    }

    setIsRunningPlaybook(false)
    setPlaybookResult({
      success: totalActions > 0,
      message: msg,
      actions: results
    })

    // Auto-acknowledge after running playbook
    acknowledgeAll()

    // NOTE: Result banner stays visible until user dismisses it
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-section font-medium text-text-primary flex items-center gap-2">
          <svg className="w-5 h-5 text-status-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
          Alerts
          {stats.critical > 0 && (
            <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-status-critical/20 text-status-critical animate-pulse">
              {stats.critical} critical
            </span>
          )}
        </h3>
        <span className="text-caption text-text-muted">{stats.active} active</span>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-3">
        <div className="glass-card p-2 text-center">
          <p className="text-lg font-semibold text-text-primary">{stats.total}</p>
          <p className="text-caption text-text-muted">Total</p>
        </div>
        <div className="glass-card p-2 text-center">
          <p className="text-lg font-semibold text-status-warning">{stats.warning}</p>
          <p className="text-caption text-text-muted">Warning</p>
        </div>
        <div className="glass-card p-2 text-center">
          <p className="text-lg font-semibold text-status-critical">{stats.critical}</p>
          <p className="text-caption text-text-muted">Critical</p>
        </div>
      </div>

      <div className="flex gap-1 mb-3 p-1 rounded-glass bg-surface-glass flex-wrap">
        {['all', 'active', 'blocked', 'ml', 'acknowledged'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`flex-1 py-1.5 text-caption rounded-glass transition-colors capitalize flex items-center justify-center gap-1 ${
              filter === f
                ? 'bg-surface-glass-active text-text-primary'
                : 'text-text-muted hover:text-text-secondary'
            }`}
          >
            {f === 'ml' ? <><svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg> ML</> : f === 'blocked' ? <><svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg> Blocked</> : f}
          </button>
        ))}
      </div>

      {/* Playbook Result Modal - Full Screen Centered Popup */}
      {playbookResult && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            onClick={() => setPlaybookResult(null)}
          />

          {/* Modal */}
          <div className={`relative w-full max-w-2xl max-h-[80vh] rounded-3xl overflow-hidden shadow-2xl ${
            playbookResult.success
              ? 'bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border-2 border-accent-green/50'
              : 'bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border-2 border-status-warning/50'
          }`}>
            {/* Glow Effect */}
            <div className={`absolute -inset-1 rounded-3xl blur-xl opacity-30 ${
              playbookResult.success ? 'bg-accent-green' : 'bg-status-warning'
            }`} />

            {/* Content */}
            <div className="relative bg-slate-900/95 rounded-3xl">
              {/* Header */}
              <div className={`p-6 border-b ${
                playbookResult.success ? 'border-accent-green/20' : 'border-status-warning/20'
              }`}>
                {/* Close Button */}
                <button
                  onClick={() => setPlaybookResult(null)}
                  className="absolute top-4 right-4 w-10 h-10 flex items-center justify-center rounded-full bg-white/10 hover:bg-red-500/50 text-white transition-all hover:scale-110"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                </button>

                <div className="flex items-center gap-4">
                  <div className={`${playbookResult.success ? 'animate-bounce' : ''}`}>
                    {playbookResult.success ? <svg className="w-12 h-12 text-accent-green" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg> : <svg className="w-12 h-12 text-status-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>}
                  </div>
                  <div>
                    <h2 className={`text-2xl font-bold ${
                      playbookResult.success ? 'text-accent-green' : 'text-status-warning'
                    }`}>
                      {playbookResult.success ? 'Defense Active!' : 'Notice'}
                    </h2>
                    <p className="text-lg text-text-secondary mt-1">{playbookResult.message}</p>
                  </div>
                </div>
              </div>

              {playbookResult.actions?.length > 0 && (
                <div className="p-6 max-h-[50vh] overflow-y-auto">
                  <div className="text-sm uppercase text-text-muted mb-4 font-bold tracking-wider flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                    Actions Executed ({playbookResult.actions.length})
                  </div>
                  <div className="space-y-3">
                    {playbookResult.actions.map((action, i) => (
                      <div key={i} className={`flex items-center gap-4 p-4 rounded-xl transition-all ${
                        action.status === 'success'
                          ? 'bg-accent-green/10 border border-accent-green/30'
                          : action.status === 'skipped'
                            ? 'bg-white/5 border border-white/10'
                            : 'bg-status-warning/10 border border-status-warning/30'
                      }`}>
                        <span>
                          {action.status === 'success' ? <svg className="w-6 h-6 text-accent-green" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg> : action.status === 'skipped' ? <svg className="w-6 h-6 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" /></svg> : <svg className="w-6 h-6 text-status-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>}
                        </span>
                        <span className={`text-base font-medium flex-1 ${
                          action.status === 'success' ? 'text-accent-green'
                            : action.status === 'skipped' ? 'text-text-muted'
                            : 'text-status-warning'
                        }`}>
                          {action.message}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Footer */}
              <div className="p-4 border-t border-white/10 flex justify-center">
                <button
                  onClick={() => setPlaybookResult(null)}
                  className="px-8 py-3 bg-white/10 hover:bg-white/20 rounded-xl text-white font-bold transition-all hover:scale-105"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="flex-1 min-h-0 overflow-y-auto space-y-2 pr-1 thin-scrollbar relative">
        <AnimatePresence mode="popLayout">
          {alerts.length > 0 ? (
            alerts.map((alert) => (
              <AlertCard
                key={alert.id}
                alert={alert}
                onClick={() => setSelectedAlert(alert)}
                onAcknowledge={acknowledgeAlert}
                onDismiss={dismissAlert}
              />
            ))
          ) : (
            <div className="flex flex-col items-center justify-center h-32 text-text-muted">
              <svg className="w-8 h-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              <p className="text-caption">
                {filter === 'all'
                  ? 'No alerts'
                  : `No ${filter} alerts`
                }
              </p>
            </div>
          )}
        </AnimatePresence>
      </div>

      <div className="mt-3 pt-3 border-t border-white/5 space-y-2">
        <div className="flex gap-2">
          <button
            onClick={acknowledgeAll}
            className="flex-1 btn-ghost text-sm py-2 flex items-center justify-center gap-1"
            disabled={stats.active === 0}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
            Ack All
          </button>
          <button
            onClick={clearAcknowledged}
            className="flex-1 btn-ghost text-sm py-2 flex items-center justify-center gap-1"
            disabled={stats.total === stats.active}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
            Clear Ack'd
          </button>
        </div>
        <button
          onClick={runDefensePlaybook}
          disabled={isRunningPlaybook}
          className={`w-full py-4 rounded-xl font-bold text-lg transition-all shadow-lg ${
            isRunningPlaybook
              ? 'bg-emerald-600/50 text-white animate-pulse cursor-wait'
              : 'bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 text-white hover:from-emerald-400 hover:via-teal-400 hover:to-cyan-400 hover:shadow-xl hover:shadow-emerald-500/30 hover:scale-[1.02] active:scale-[0.98]'
          }`}
        >
          {isRunningPlaybook ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
              Executing Playbook...
            </span>
          ) : (
            <span className="flex items-center justify-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
              Run Defense Playbook
            </span>
          )}
        </button>
      </div>

      <AlertDetailModal
        alert={selectedAlert}
        isOpen={!!selectedAlert}
        onClose={() => setSelectedAlert(null)}
        onAcknowledge={acknowledgeAlert}
        onDismiss={dismissAlert}
      />
    </div>
  )
}

export default memo(AlertsPanel)

