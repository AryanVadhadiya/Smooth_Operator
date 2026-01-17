// ============================================
// THREAT_OPS.AI - Mock Data
// Sample data for development and demos
// ============================================

// ============================================
// Mock Devices
// ============================================
export const mockDevices = [
  {
    id: 'dev-001',
    name: 'Auth Server',
    type: 'server',
    category: 'authentication',
    status: 'online',
    ip: '10.0.1.10',
    location: 'Data Center A',
    lastSeen: new Date().toISOString(),
    metrics: {
      cpu: 45,
      memory: 62,
      uptime: 99.9,
    }
  },
  {
    id: 'dev-002',
    name: 'Database Cluster',
    type: 'server',
    category: 'database',
    status: 'online',
    ip: '10.0.1.20',
    location: 'Data Center A',
    lastSeen: new Date().toISOString(),
    metrics: {
      cpu: 72,
      memory: 85,
      uptime: 99.8,
    }
  },
  {
    id: 'dev-003',
    name: 'API Gateway',
    type: 'server',
    category: 'network',
    status: 'online',
    ip: '10.0.1.5',
    location: 'Edge',
    lastSeen: new Date().toISOString(),
    metrics: {
      cpu: 38,
      memory: 45,
      uptime: 99.99,
    }
  },
  {
    id: 'dev-004',
    name: 'Medical Device Hub',
    type: 'iot-gateway',
    category: 'healthcare',
    status: 'online',
    ip: '10.0.2.100',
    location: 'Hospital Wing A',
    lastSeen: new Date().toISOString(),
    metrics: {
      cpu: 25,
      memory: 40,
      uptime: 99.5,
    }
  },
  {
    id: 'dev-005',
    name: 'Patient Monitor #1',
    type: 'iot-device',
    category: 'healthcare',
    status: 'online',
    ip: '10.0.2.101',
    location: 'ICU Room 101',
    lastSeen: new Date().toISOString(),
    metrics: {
      cpu: 15,
      memory: 30,
      uptime: 98.5,
    }
  },
  {
    id: 'dev-006',
    name: 'Patient Monitor #2',
    type: 'iot-device',
    category: 'healthcare',
    status: 'degraded',
    ip: '10.0.2.102',
    location: 'ICU Room 102',
    lastSeen: new Date(Date.now() - 300000).toISOString(),
    metrics: {
      cpu: 88,
      memory: 92,
      uptime: 95.2,
    }
  },
  {
    id: 'dev-007',
    name: 'Edge Gateway',
    type: 'network',
    category: 'network',
    status: 'online',
    ip: '10.0.0.1',
    location: 'Edge',
    lastSeen: new Date().toISOString(),
    metrics: {
      cpu: 32,
      memory: 55,
      uptime: 99.99,
    }
  },
  {
    id: 'dev-008',
    name: 'Backup Server',
    type: 'server',
    category: 'storage',
    status: 'online',
    ip: '10.0.1.100',
    location: 'Data Center B',
    lastSeen: new Date().toISOString(),
    metrics: {
      cpu: 18,
      memory: 35,
      uptime: 99.95,
    }
  },
]

// ============================================
// Mock Alerts
// ============================================
export const mockAlerts = [
  {
    id: 'alert-001',
    title: 'Unusual login pattern detected',
    description: 'Multiple failed login attempts followed by successful authentication from a new IP address.',
    severity: 'warning',
    source: 'Auth Server',
    sourceId: 'dev-001',
    category: 'authentication',
    timestamp: new Date(Date.now() - 120000).toISOString(),
    acknowledged: false,
    evidence: {
      failedAttempts: 5,
      sourceIP: '192.168.1.45',
      targetUser: 'admin@hospital.local',
    }
  },
  {
    id: 'alert-002',
    title: 'High CPU usage on Database Cluster',
    description: 'CPU utilization has exceeded 90% for more than 5 minutes.',
    severity: 'normal',
    source: 'Database Cluster',
    sourceId: 'dev-002',
    category: 'performance',
    timestamp: new Date(Date.now() - 300000).toISOString(),
    acknowledged: false,
    evidence: {
      cpuUsage: 92,
      duration: '5m 23s',
      topProcess: 'mysql',
    }
  },
  {
    id: 'alert-003',
    title: 'Failed SSH attempts from external IP',
    description: 'Repeated SSH brute force attempts detected from external IP address.',
    severity: 'critical',
    source: 'Edge Gateway',
    sourceId: 'dev-007',
    category: 'intrusion',
    timestamp: new Date(Date.now() - 720000).toISOString(),
    acknowledged: false,
    evidence: {
      attempts: 47,
      sourceIP: '45.33.32.156',
      targetPort: 22,
      blocked: true,
    }
  },
  {
    id: 'alert-004',
    title: 'Medical device communication timeout',
    description: 'Patient Monitor #2 has not sent telemetry in the last 5 minutes.',
    severity: 'warning',
    source: 'Patient Monitor #2',
    sourceId: 'dev-006',
    category: 'connectivity',
    timestamp: new Date(Date.now() - 180000).toISOString(),
    acknowledged: true,
    evidence: {
      lastContact: new Date(Date.now() - 480000).toISOString(),
      expectedInterval: '30s',
    }
  },
  {
    id: 'alert-005',
    title: 'Anomalous API request pattern',
    description: 'Unusual spike in API requests from a single source.',
    severity: 'warning',
    source: 'API Gateway',
    sourceId: 'dev-003',
    category: 'traffic',
    timestamp: new Date(Date.now() - 600000).toISOString(),
    acknowledged: false,
    evidence: {
      requestCount: 1247,
      timeWindow: '60s',
      sourceIP: '10.0.5.88',
      endpoint: '/api/patients',
    }
  },
]

// ============================================
// Mock Telemetry (Time Series)
// ============================================
const generateTelemetryPoints = () => {
  const points = []
  const now = Date.now()

  for (let i = 60; i >= 0; i--) {
    const timestamp = new Date(now - i * 60000).toISOString()
    points.push({
      timestamp,
      deviceId: 'dev-001',
      metrics: {
        cpu: 30 + Math.random() * 40,
        memory: 50 + Math.random() * 30,
        network: 100 + Math.random() * 200,
        requests: 50 + Math.floor(Math.random() * 150),
      }
    })
  }

  return points
}

export const mockTelemetry = generateTelemetryPoints()

// ============================================
// Mock System Status
// ============================================
export const mockSystemStatus = {
  overall: 'normal', // normal | warning | critical
  components: {
    ingest: { status: 'healthy', latency: 12 },
    detection: { status: 'healthy', latency: 45 },
    alerting: { status: 'healthy', latency: 8 },
    response: { status: 'healthy', latency: 15 },
  },
  stats: {
    activeDevices: 128,
    eventsPerMinute: 2847,
    activeAlerts: 7,
    blockedThreats: 23,
  },
  lastUpdated: new Date().toISOString(),
}

// ============================================
// Mock Playbooks
// ============================================
export const mockPlaybooks = [
  {
    id: 'pb-001',
    name: 'Block Malicious IP',
    description: 'Automatically blocks an IP address across all edge gateways.',
    triggers: ['manual', 'alert:intrusion'],
    actions: ['firewall:block', 'notify:slack', 'log:audit'],
    enabled: true,
    lastRun: new Date(Date.now() - 3600000).toISOString(),
    runCount: 47,
  },
  {
    id: 'pb-002',
    name: 'Isolate Compromised Device',
    description: 'Quarantines a device by restricting network access.',
    triggers: ['manual', 'alert:critical'],
    actions: ['network:isolate', 'notify:email', 'ticket:create'],
    enabled: true,
    lastRun: new Date(Date.now() - 86400000).toISOString(),
    runCount: 12,
  },
  {
    id: 'pb-003',
    name: 'Rate Limit Service',
    description: 'Applies rate limiting to a service endpoint.',
    triggers: ['manual', 'alert:traffic'],
    actions: ['gateway:throttle', 'notify:slack'],
    enabled: true,
    lastRun: null,
    runCount: 0,
  },
  {
    id: 'pb-004',
    name: 'Emergency Lockdown',
    description: 'Restricts all external access to critical systems.',
    triggers: ['manual'],
    actions: ['firewall:lockdown', 'notify:all', 'ticket:create'],
    enabled: false,
    lastRun: null,
    runCount: 0,
  },
]

// ============================================
// Mock Recent Actions
// ============================================
export const mockRecentActions = [
  {
    id: 'action-001',
    type: 'block',
    target: '45.33.32.156',
    reason: 'SSH brute force attempt',
    playbook: 'Block Malicious IP',
    executedBy: 'system',
    executedAt: new Date(Date.now() - 720000).toISOString(),
    status: 'completed',
  },
  {
    id: 'action-002',
    type: 'throttle',
    target: 'API Gateway',
    reason: 'Unusual request spike',
    playbook: 'Rate Limit Service',
    executedBy: 'admin@hospital.local',
    executedAt: new Date(Date.now() - 1800000).toISOString(),
    status: 'completed',
  },
  {
    id: 'action-003',
    type: 'alert',
    target: 'Security Team',
    reason: 'Critical system alert',
    playbook: null,
    executedBy: 'system',
    executedAt: new Date(Date.now() - 3600000).toISOString(),
    status: 'completed',
  },
]
