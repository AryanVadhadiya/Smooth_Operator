// ============================================
// THREAT_OPS.AI - API Service
// All HTTP calls isolated in this module
// ============================================

// Mock mode toggle - set via environment variable
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

// Base API URL for production
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:3001/api'

// ============================================
// Mock Data Imports
// ============================================
import {
  mockAlerts,
  mockDevices,
  mockTelemetry,
  mockSystemStatus,
  mockPlaybooks
} from '@mock/data'

// ============================================
// Response Helper
// ============================================
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms))

const mockResponse = async (data, delayMs = 200) => {
  await delay(delayMs)
  return { data, success: true }
}

const apiRequest = async (endpoint, options = {}) => {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`)
    }

    const data = await response.json()
    return { data, success: true }
  } catch (error) {
    console.error(`API request failed: ${endpoint}`, error)
    return { data: null, success: false, error: error.message }
  }
}

// ============================================
// Alert APIs
// ============================================
export const fetchAlerts = async (filters = {}) => {
  if (USE_MOCK) {
    let alerts = [...mockAlerts]
    if (filters.severity) {
      alerts = alerts.filter(a => a.severity === filters.severity)
    }
    return mockResponse(alerts)
  }
  return apiRequest('/alerts')
}

export const acknowledgeAlert = async (alertId) => {
  if (USE_MOCK) {
    return mockResponse({ id: alertId, acknowledged: true })
  }
  return apiRequest(`/alerts/${alertId}/acknowledge`, { method: 'POST' })
}

export const dismissAlert = async (alertId) => {
  if (USE_MOCK) {
    return mockResponse({ id: alertId, dismissed: true })
  }
  return apiRequest(`/alerts/${alertId}/dismiss`, { method: 'POST' })
}

// ============================================
// Device APIs
// ============================================
export const fetchDevices = async () => {
  if (USE_MOCK) {
    return mockResponse(mockDevices)
  }
  return apiRequest('/devices')
}

export const fetchDeviceById = async (deviceId) => {
  if (USE_MOCK) {
    const device = mockDevices.find(d => d.id === deviceId)
    return mockResponse(device)
  }
  return apiRequest(`/devices/${deviceId}`)
}

export const updateDeviceStatus = async (deviceId, status) => {
  if (USE_MOCK) {
    return mockResponse({ id: deviceId, status })
  }
  return apiRequest(`/devices/${deviceId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  })
}

// ============================================
// Telemetry APIs
// ============================================
export const fetchTelemetry = async (timeRange = '1h') => {
  if (USE_MOCK) {
    return mockResponse(mockTelemetry)
  }
  return apiRequest(`/telemetry?range=${timeRange}`)
}

export const fetchTelemetryByDevice = async (deviceId, timeRange = '1h') => {
  if (USE_MOCK) {
    const filtered = mockTelemetry.filter(t => t.deviceId === deviceId)
    return mockResponse(filtered)
  }
  return apiRequest(`/telemetry/${deviceId}?range=${timeRange}`)
}

// ============================================
// System Status APIs
// ============================================
export const fetchSystemStatus = async () => {
  if (USE_MOCK) {
    return mockResponse(mockSystemStatus)
  }
  return apiRequest('/system/status')
}

// ============================================
// Playbook APIs
// ============================================
export const fetchPlaybooks = async () => {
  if (USE_MOCK) {
    return mockResponse(mockPlaybooks)
  }
  return apiRequest('/playbooks')
}

export const executePlaybook = async (playbookId, params = {}) => {
  if (USE_MOCK) {
    return mockResponse({
      playbookId,
      executionId: `exec-${Date.now()}`,
      status: 'running',
      startedAt: new Date().toISOString()
    }, 500)
  }
  return apiRequest(`/playbooks/${playbookId}/execute`, {
    method: 'POST',
    body: JSON.stringify(params),
  })
}

// ============================================
// Response Action APIs
// ============================================
export const blockIP = async (ipAddress, reason) => {
  if (USE_MOCK) {
    return mockResponse({
      action: 'block',
      target: ipAddress,
      reason,
      executedAt: new Date().toISOString()
    }, 300)
  }
  return apiRequest('/actions/block-ip', {
    method: 'POST',
    body: JSON.stringify({ ipAddress, reason }),
  })
}

export const isolateDevice = async (deviceId, reason) => {
  if (USE_MOCK) {
    return mockResponse({
      action: 'isolate',
      target: deviceId,
      reason,
      executedAt: new Date().toISOString()
    }, 300)
  }
  return apiRequest('/actions/isolate-device', {
    method: 'POST',
    body: JSON.stringify({ deviceId, reason }),
  })
}

export const throttleService = async (serviceId, limit) => {
  if (USE_MOCK) {
    return mockResponse({
      action: 'throttle',
      target: serviceId,
      limit,
      executedAt: new Date().toISOString()
    }, 300)
  }
  return apiRequest('/actions/throttle', {
    method: 'POST',
    body: JSON.stringify({ serviceId, limit }),
  })
}
