import { useState, useEffect, useCallback, useRef } from 'react'
import {
  connectSocket,
  disconnectSocket,
  subscribeToTelemetry,
  onConnect,
  onDisconnect
} from '@services/socket'

const MAX_DATA_POINTS = 120

export function useTelemetry() {
  const [isConnected, setIsConnected] = useState(false)
  const [isPaused, setIsPaused] = useState(false)

  const [deviceDataMap, setDeviceDataMap] = useState({})
  const [devices, setDevices] = useState([])
  const [activeDeviceId, setActiveDeviceId] = useState(null)

  const [latestPoint, setLatestPoint] = useState(null)
  const [rawEvents, setRawEvents] = useState([])

  const eventIdRef = useRef(0)

  useEffect(() => {
    const socket = connectSocket()

    const unsubConnect = onConnect(() => {
      setIsConnected(true)
    })

    const unsubDisconnect = onDisconnect(() => {
      setIsConnected(false)
    })

    return () => {
      unsubConnect()
      unsubDisconnect()
      disconnectSocket()
    }
  }, [])

  useEffect(() => {
    if (isPaused) return

    const unsubscribe = subscribeToTelemetry((data) => {
      const timestamp = new Date(data.timestamp)
      const timeLabel = timestamp.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })

      const chartPoint = {
        time: timeLabel,
        timestamp: timestamp.getTime(),
        cpu: Math.round(data.metrics.cpu * 10) / 10,
        memory: Math.round(data.metrics.memory * 10) / 10,
        network: Math.round(data.metrics.network),
        requests: data.metrics.requests,
        deviceId: data.deviceId,
        deviceName: data.deviceName,
        devices: data.metrics.devices || {},
        sector: data.metrics.sector || 'unknown'
      }

      setDevices(prev => {
        if (!prev.find(d => d.id === data.deviceId)) {
          return [...prev, { id: data.deviceId, name: data.deviceName }]
        }
        return prev
      })

      setActiveDeviceId(prev => prev || data.deviceId)

      setDeviceDataMap(prev => {
        const currentBuffer = prev[data.deviceId] || []
        const newBuffer = [...currentBuffer, chartPoint].slice(-MAX_DATA_POINTS)
        return { ...prev, [data.deviceId]: newBuffer }
      })

      setActiveDeviceId(currentActive => {
        if (currentActive === data.deviceId) {
          setLatestPoint(chartPoint)
        }
        return currentActive
      })

      const rawEvent = {
        id: eventIdRef.current++,
        timestamp: timestamp.toISOString(),
        deviceId: data.deviceId,
        deviceName: data.deviceName,
        metrics: data.metrics,
      }

      setRawEvents(prev => {
        const updated = [rawEvent, ...prev]
        return updated.slice(0, 100)
      })
    })

    return unsubscribe
  }, [isPaused])

  const activeDeviceData = activeDeviceId ? (deviceDataMap[activeDeviceId] || []) : []

  const pause = useCallback(() => setIsPaused(true), [])
  const resume = useCallback(() => setIsPaused(false), [])
  const toggle = useCallback(() => setIsPaused(prev => !prev), [])

  const clearData = useCallback(() => {
    setDeviceDataMap({})
    setRawEvents([])
    setLatestPoint(null)
  }, [])

  return {
    isConnected,
    isPaused,
    telemetryData: activeDeviceData,
    latestPoint,
    rawEvents,
    devices,
    activeDeviceId,
    setActiveDeviceId,
    pause,
    resume,
    toggle,
    clearData,
  }
}

export default useTelemetry
