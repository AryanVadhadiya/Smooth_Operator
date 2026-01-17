import { useState, useCallback, useRef } from 'react'
import { getSocket } from '@services/socket'

// ============================================
// useScenarios Hook
// Mock scenario triggers with socket injection
// ============================================

// Scenario definitions
const SCENARIOS = {
  normal: {
    id: 'normal',
    name: 'Normal System',
    icon: '✅',
    description: 'Reset to calm operational state',
    duration: 2000,
  },
  sqlInjection: {
    id: 'sqlInjection',
    name: 'SQL Injection Attack',
    icon: '💉',
    description: 'Simulate malicious SQL injection attempt',
    duration: 5000,
  },
  flood: {
    id: 'flood',
    name: 'Burst / Flood Attack',
    icon: '🌊',
    description: 'Simulate DDoS traffic flood',
    duration: 8000,
  },
  replay: {
    id: 'replay',
    name: 'Replay Incident',
    icon: '⏮️',
    description: 'Step through historical attack timeline',
    duration: 10000,
  },
}

// Generate mock telemetry for scenarios
const generateScenarioTelemetry = (scenarioId) => {
  const socket = getSocket()
  if (!socket) return

  const devices = [
    { id: 'auth-server', name: 'Auth Server' },
    { id: 'api-gateway', name: 'API Gateway' },
    { id: 'db-primary', name: 'Database Primary' },
  ]

  switch (scenarioId) {
    case 'normal':
      // Emit calm telemetry
      devices.forEach(device => {
        socket.emit('telemetry', {
          deviceId: device.id,
          deviceName: device.name,
          timestamp: new Date().toISOString(),
          metrics: {
            cpu: 20 + Math.random() * 15,
            memory: 40 + Math.random() * 10,
            network: 50 + Math.random() * 50,
            requests: 50 + Math.floor(Math.random() * 50),
          }
        })
      })
      break

    case 'sqlInjection':
      // Emit attack telemetry
      socket.emit('telemetry', {
        deviceId: 'db-primary',
        deviceName: 'Database Primary',
        timestamp: new Date().toISOString(),
        metrics: {
          cpu: 85 + Math.random() * 15,
          memory: 75 + Math.random() * 20,
          network: 300 + Math.random() * 200,
          requests: 800 + Math.floor(Math.random() * 200),
        }
      })
      // Emit SQL injection alert
      socket.emit('alert', {
        id: `sql-${Date.now()}`,
        title: 'SQL Injection Attempt Detected',
        description: 'Malicious SQL patterns detected in query parameters. Attempted payload: \' OR 1=1; DROP TABLE users; --',
        severity: 'critical',
        source: 'API Gateway',
        timestamp: new Date().toISOString(),
        evidence: {
          attackType: 'SQL Injection',
          payload: "' OR 1=1; DROP TABLE users; --",
          sourceIP: '192.168.1.' + Math.floor(Math.random() * 255),
          targetEndpoint: '/api/users/login',
          blockedBy: 'WAF Rule #7',
        },
        recommendation: 'Block source IP and review parameterized queries.',
        acknowledged: false,
      })
      break

    case 'flood':
      // Emit flood telemetry
      const floodInterval = setInterval(() => {
        socket.emit('telemetry', {
          deviceId: 'api-gateway',
          deviceName: 'API Gateway',
          timestamp: new Date().toISOString(),
          metrics: {
            cpu: 95 + Math.random() * 5,
            memory: 88 + Math.random() * 10,
            network: 900 + Math.random() * 100,
            requests: 2000 + Math.floor(Math.random() * 500),
          }
        })
      }, 300)
      // Stop after 3 seconds
      setTimeout(() => clearInterval(floodInterval), 3000)

      // Emit flood alerts
      socket.emit('alert', {
        id: `flood-${Date.now()}`,
        title: 'DDoS Attack Detected',
        description: 'Abnormal traffic spike from multiple sources detected. Rate limiting activated.',
        severity: 'critical',
        source: 'API Gateway',
        timestamp: new Date().toISOString(),
        evidence: {
          attackType: 'DDoS / Traffic Flood',
          requestsPerSecond: 2500,
          uniqueSourceIPs: 847,
          avgResponseTime: '12.4s',
          droppedConnections: 1823,
        },
        recommendation: 'Enable CDN protection and geo-blocking for suspicious regions.',
        acknowledged: false,
      })
      break

    case 'replay':
      // Replay historical incident timeline
      const events = [
        { time: 0, alert: { title: 'Reconnaissance Scan Detected', severity: 'warning', source: 'Firewall' }},
        { time: 2000, alert: { title: 'Failed SSH Attempts', severity: 'warning', source: 'Auth Server' }},
        { time: 4000, alert: { title: 'Brute Force Attack', severity: 'critical', source: 'Auth Server' }},
        { time: 5500, alert: { title: 'Credential Compromise Suspected', severity: 'critical', source: 'SIEM' }},
        { time: 7000, alert: { title: 'Lateral Movement Detected', severity: 'critical', source: 'Network Monitor' }},
        { time: 8500, alert: { title: 'Data Exfiltration Attempt', severity: 'critical', source: 'DLP' }},
      ]

      events.forEach(({ time, alert }) => {
        setTimeout(() => {
          socket.emit('alert', {
            id: `replay-${Date.now()}`,
            ...alert,
            description: `Replay of historical incident at T+${time/1000}s`,
            timestamp: new Date().toISOString(),
            acknowledged: false,
          })
        }, time)
      })
      break
  }
}

export function useScenarios() {
  const [activeScenario, setActiveScenario] = useState(null)
  const [scenarioState, setScenarioState] = useState({}) // { [id]: 'idle' | 'loading' | 'active' | 'complete' }
  const timeoutRef = useRef(null)

  const triggerScenario = useCallback((scenarioId) => {
    const scenario = SCENARIOS[scenarioId]
    if (!scenario) return

    // Clear any previous timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    // Set loading state
    setScenarioState(prev => ({ ...prev, [scenarioId]: 'loading' }))
    setActiveScenario(scenarioId)

    // After 500ms, set to active and trigger effects
    setTimeout(() => {
      setScenarioState(prev => ({ ...prev, [scenarioId]: 'active' }))
      generateScenarioTelemetry(scenarioId)
    }, 500)

    // After duration, set to complete
    timeoutRef.current = setTimeout(() => {
      setScenarioState(prev => ({ ...prev, [scenarioId]: 'complete' }))

      // Reset to idle after showing complete
      setTimeout(() => {
        setScenarioState(prev => ({ ...prev, [scenarioId]: 'idle' }))
        setActiveScenario(null)
      }, 1500)
    }, scenario.duration)
  }, [])

  const stopScenario = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setActiveScenario(null)
    setScenarioState({})
  }, [])

  const getScenarioState = useCallback((scenarioId) => {
    return scenarioState[scenarioId] || 'idle'
  }, [scenarioState])

  return {
    scenarios: Object.values(SCENARIOS),
    activeScenario,
    triggerScenario,
    stopScenario,
    getScenarioState,
  }
}

export default useScenarios
