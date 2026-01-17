import { io } from 'socket.io-client'
import { mockAlerts, mockTelemetry, mockDevices } from '@mock/data'

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'
const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || 'http://localhost:3001'

class MockEventEmitter {
  constructor() {
    this.listeners = new Map()
    this.connected = false
    this.intervals = []
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event).push(callback)
    return this
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event)
      const index = callbacks.indexOf(callback)
      if (index > -1) {
        callbacks.splice(index, 1)
      }
    }
    return this
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => callback(data))
    }
    return this
  }

  connect() {
    this.connected = true
    setTimeout(() => this.emit('connect'), 100)
    this._startMockStreams()
    return this
  }

  disconnect() {
    this.connected = false
    this.intervals.forEach(clearInterval)
    this.intervals = []
    this.emit('disconnect')
    return this
  }

  _prevMetrics = { cpu: 50, memory: 55, network: 500 }

  _startMockStreams() {
    const telemetryInterval = setInterval(() => {
      if (!this.connected) return

      const randomDevice = mockDevices[Math.floor(Math.random() * mockDevices.length)]

      const lerp = (current, target, factor) => current + (target - current) * factor
      const targetCpu = 30 + Math.random() * 60
      const targetMemory = 40 + Math.random() * 45
      const targetNetwork = 100 + Math.random() * 800

      this._prevMetrics = {
        cpu: lerp(this._prevMetrics.cpu, targetCpu, 0.3),
        memory: lerp(this._prevMetrics.memory, targetMemory, 0.2),
        network: lerp(this._prevMetrics.network, targetNetwork, 0.25),
      }

      const telemetryPoint = {
        deviceId: randomDevice.id,
        deviceName: randomDevice.name,
        timestamp: new Date().toISOString(),
        metrics: {
          cpu: this._prevMetrics.cpu,
          memory: this._prevMetrics.memory,
          network: this._prevMetrics.network,
          requests: Math.floor(Math.random() * 500),
        }
      }
      this.emit('telemetry', telemetryPoint)
    }, 500)
    this.intervals.push(telemetryInterval)

    const alertInterval = setInterval(() => {
      if (!this.connected) return

      if (Math.random() > 0.3) return

      const severities = ['normal', 'warning', 'critical']
      const alertTypes = [
        'Unusual login pattern detected',
        'High CPU usage spike',
        'Failed authentication attempts',
        'Suspicious network traffic',
        'Service response timeout',
        'Memory threshold exceeded',
        'Unauthorized access attempt',
      ]

      const newAlert = {
        id: `alert-${Date.now()}`,
        title: alertTypes[Math.floor(Math.random() * alertTypes.length)],
        severity: severities[Math.floor(Math.random() * severities.length)],
        source: mockDevices[Math.floor(Math.random() * mockDevices.length)].name,
        timestamp: new Date().toISOString(),
        acknowledged: false,
      }
      this.emit('alert', newAlert)
    }, 15000 + Math.random() * 15000)
    this.intervals.push(alertInterval)

    const deviceInterval = setInterval(() => {
      if (!this.connected) return

      if (Math.random() > 0.2) return

      const device = mockDevices[Math.floor(Math.random() * mockDevices.length)]
      const statuses = ['online', 'degraded', 'offline']

      this.emit('device:status', {
        deviceId: device.id,
        status: statuses[Math.floor(Math.random() * statuses.length)],
        timestamp: new Date().toISOString(),
      })
    }, 30000)
    this.intervals.push(deviceInterval)
  }
}

let socket = null
let mockSocket = null

export const connectSocket = () => {
  if (USE_MOCK) {
    if (!mockSocket) {
      mockSocket = new MockEventEmitter()
    }
    mockSocket.connect()
    return mockSocket
  }

  if (!socket) {
    socket = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
      autoConnect: true,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    })
  }

  socket.connect()
  return socket
}

export const disconnectSocket = () => {
  if (USE_MOCK && mockSocket) {
    mockSocket.disconnect()
    return
  }

  if (socket) {
    socket.disconnect()
  }
}

export const getSocket = () => {
  if (USE_MOCK) {
    return mockSocket
  }
  return socket
}

export const subscribeToTelemetry = (callback) => {
  const s = getSocket()
  if (s) {
    s.on('telemetry', callback)
  }
  return () => {
    if (s) s.off('telemetry', callback)
  }
}

export const subscribeToAlerts = (callback) => {
  const s = getSocket()
  if (s) {
    s.on('alert', callback)
  }
  return () => {
    if (s) s.off('alert', callback)
  }
}

export const subscribeToDeviceStatus = (callback) => {
  const s = getSocket()
  if (s) {
    s.on('device:status', callback)
  }
  return () => {
    if (s) s.off('device:status', callback)
  }
}

export const subscribeToSystemStatus = (callback) => {
  const s = getSocket()
  if (s) {
    s.on('system:status', callback)
  }
  return () => {
    if (s) s.off('system:status', callback)
  }
}

export const onConnect = (callback) => {
  const s = getSocket()
  if (s) {
    s.on('connect', callback)
  }
  return () => {
    if (s) s.off('connect', callback)
  }
}

export const onDisconnect = (callback) => {
  const s = getSocket()
  if (s) {
    s.on('disconnect', callback)
  }
  return () => {
    if (s) s.off('disconnect', callback)
  }
}

export const onError = (callback) => {
  const s = getSocket()
  if (s) {
    s.on('error', callback)
  }
  return () => {
    if (s) s.off('error', callback)
  }
}
