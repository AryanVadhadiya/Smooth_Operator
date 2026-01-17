import { memo } from 'react'
import { AnimatePresence } from 'framer-motion'
import AlertCard from '@components/alerts/AlertCard'
import AlertDetailModal from '@components/alerts/AlertDetailModal'
import useAlerts from '@hooks/useAlerts'

function AlertsPanel() {
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
  } = useAlerts()

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-section font-medium text-text-primary flex items-center gap-2">
          <span className="text-status-warning">⚠</span>
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

      <div className="flex gap-1 mb-3 p-1 rounded-glass bg-surface-glass">
        {['all', 'active', 'acknowledged'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`flex-1 py-1.5 text-caption rounded-glass transition-colors capitalize ${
              filter === f
                ? 'bg-surface-glass-active text-text-primary'
                : 'text-text-muted hover:text-text-secondary'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto space-y-2 pr-1">
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
              <span className="text-2xl mb-2">✓</span>
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
            className="flex-1 btn-ghost text-sm py-2"
            disabled={stats.active === 0}
          >
            ✓ Ack All
          </button>
          <button
            onClick={clearAcknowledged}
            className="flex-1 btn-ghost text-sm py-2"
            disabled={stats.total === stats.active}
          >
            🗑 Clear Ack'd
          </button>
        </div>
        <button className="w-full btn-primary text-sm py-2">
          🛡️ Run Defense Playbook
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
