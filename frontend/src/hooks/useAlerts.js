import { useState, useEffect, useCallback, useRef } from 'react'
import {
  connectSocket,
  subscribeToAlerts,
  subscribeToTelemetry,
} from '@services/socket'

// ============================================
// useAlerts Hook
// Alert state management with mock detection logic
// ============================================

// Detection rules - derive alerts from telemetry
const DETECTION_RULES = {
  highCpu: {
    id: 'rule-cpu-high',
    name: 'High CPU Usage',
    check: (metrics) => metrics.cpu > 85,
    severity: 'warning',
    generateAlert: (data) => ({
      title: 'High CPU Usage Detected',
      description: `CPU utilization exceeded 85% threshold on ${data.deviceName}.`,
      evidence: {
        metric: 'cpu',
        value: `${data.metrics.cpu.toFixed(1)}%`,
        threshold: '85%',
        deviceId: data.deviceId,
        deviceName: data.deviceName,
      },
      recommendation: 'Check for runaway processes or consider scaling resources.',
    }),
  },
  criticalMemory: {
    id: 'rule-mem-critical',
    name: 'Critical Memory Usage',
    check: (metrics) => metrics.memory > 90,
    severity: 'critical',
    generateAlert: (data) => ({
      title: 'Critical Memory Usage',
      description: `Memory usage exceeded 90% on ${data.deviceName}. System may become unresponsive.`,
      evidence: {
        metric: 'memory',
        value: `${data.metrics.memory.toFixed(1)}%`,
        threshold: '90%',
        deviceId: data.deviceId,
        deviceName: data.deviceName,
      },
      recommendation: 'Immediate action required. Consider restarting services or adding memory.',
    }),
  },
  highNetworkSpike: {
    id: 'rule-net-spike',
    name: 'Network Traffic Spike',
    check: (metrics) => metrics.network > 800,
    severity: 'warning',
    generateAlert: (data) => ({
      title: 'Unusual Network Traffic Spike',
      description: `Network throughput spike detected on ${data.deviceName}.`,
      evidence: {
        metric: 'network',
        value: `${data.metrics.network.toFixed(0)} KB/s`,
        threshold: '800 KB/s',
        deviceId: data.deviceId,
        deviceName: data.deviceName,
      },
      recommendation: 'Investigate for potential data exfiltration or DDoS activity.',
    }),
  },
  requestFlood: {
    id: 'rule-req-flood',
    name: 'Request Flood',
    check: (metrics) => metrics.requests > 400,
    severity: 'warning',
    generateAlert: (data) => ({
      title: 'Elevated Request Volume',
      description: `Unusual request volume detected on ${data.deviceName}.`,
      evidence: {
        metric: 'requests',
        value: `${data.metrics.requests} req/min`,
        threshold: '400 req/min',
        deviceId: data.deviceId,
        deviceName: data.deviceName,
      },
      recommendation: 'Consider enabling rate limiting or investigating the source.',
    }),
  },
}

// Cooldown tracking to prevent alert spam
const alertCooldowns = new Map()
const COOLDOWN_MS = 30000 // 30 seconds between same alert type

export function useAlerts() {
  const [alerts, setAlerts] = useState([])
  const [selectedAlert, setSelectedAlert] = useState(null)
  const [filter, setFilter] = useState('all') // all | active | acknowledged
  const alertIdRef = useRef(0)

  // Subscribe to socket alerts
  useEffect(() => {
    const unsubscribe = subscribeToAlerts((alert) => {
      const newAlert = {
        ...alert,
        id: `alert-${alertIdRef.current++}`,
        acknowledged: false,
        timestamp: new Date().toISOString(),
      }
      setAlerts(prev => [newAlert, ...prev].slice(0, 50))
    })

    return unsubscribe
  }, [])

  // Subscribe to telemetry and run detection rules
  useEffect(() => {
    const unsubscribe = subscribeToTelemetry((data) => {
      Object.values(DETECTION_RULES).forEach((rule) => {
        if (rule.check(data.metrics)) {
          // Check cooldown
          const cooldownKey = `${rule.id}-${data.deviceId}`
          const lastAlert = alertCooldowns.get(cooldownKey)

          if (lastAlert && Date.now() - lastAlert < COOLDOWN_MS) {
            return // Skip, still in cooldown
          }

          // Generate alert
          const alertData = rule.generateAlert(data)
          const newAlert = {
            id: `alert-${alertIdRef.current++}`,
            ...alertData,
            severity: rule.severity,
            source: data.deviceName,
            sourceId: data.deviceId,
            ruleId: rule.id,
            ruleName: rule.name,
            timestamp: new Date().toISOString(),
            acknowledged: false,
          }

          setAlerts(prev => [newAlert, ...prev].slice(0, 50))
          alertCooldowns.set(cooldownKey, Date.now())
        }
      })
    })

    return unsubscribe
  }, [])

  // Actions
  const acknowledgeAlert = useCallback((alertId) => {
    setAlerts(prev => prev.map(a =>
      a.id === alertId ? { ...a, acknowledged: true, acknowledgedAt: new Date().toISOString() } : a
    ))
    if (selectedAlert?.id === alertId) {
      setSelectedAlert(prev => ({ ...prev, acknowledged: true }))
    }
  }, [selectedAlert])

  const dismissAlert = useCallback((alertId) => {
    setAlerts(prev => prev.filter(a => a.id !== alertId))
    if (selectedAlert?.id === alertId) {
      setSelectedAlert(null)
    }
  }, [selectedAlert])

  const acknowledgeAll = useCallback(() => {
    setAlerts(prev => prev.map(a => ({ ...a, acknowledged: true, acknowledgedAt: new Date().toISOString() })))
  }, [])

  const clearAcknowledged = useCallback(() => {
    setAlerts(prev => prev.filter(a => !a.acknowledged))
  }, [])

  // Filtered alerts
  const filteredAlerts = alerts.filter(alert => {
    if (filter === 'active') return !alert.acknowledged
    if (filter === 'acknowledged') return alert.acknowledged
    return true
  })

  // Stats
  const stats = {
    total: alerts.length,
    active: alerts.filter(a => !a.acknowledged).length,
    critical: alerts.filter(a => a.severity === 'critical' && !a.acknowledged).length,
    warning: alerts.filter(a => a.severity === 'warning' && !a.acknowledged).length,
  }

  return {
    // State
    alerts: filteredAlerts,
    allAlerts: alerts,
    selectedAlert,
    filter,
    stats,

    // Actions
    setFilter,
    setSelectedAlert,
    acknowledgeAlert,
    dismissAlert,
    acknowledgeAll,
    clearAcknowledged,
  }
}

export default useAlerts
