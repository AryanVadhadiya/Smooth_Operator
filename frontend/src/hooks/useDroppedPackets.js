import { useState, useEffect, useCallback, useRef } from 'react'
import { getSocket } from '../services/socket'

const API_GATEWAY_URL = 'http://localhost:3001'

/**
 * Hook for managing dropped packets state and real-time updates.
 * Provides:
 * - droppedPackets: Array of recent dropped packet records
 * - droppedStats: Statistics about dropped packets by type
 * - isConnected: Whether socket is connected for live updates
 */
function useDroppedPackets() {
  const [droppedPackets, setDroppedPackets] = useState([])
  const [droppedStats, setDroppedStats] = useState({
    total_dropped: 0,
    by_type: {}
  })
  const [isConnected, setIsConnected] = useState(false)

  // Track if we've already fetched initial data
  const initialFetchDone = useRef(false)

  // Fetch dropped packets from API
  const fetchDroppedPackets = useCallback(async () => {
    try {
      const res = await fetch(`${API_GATEWAY_URL}/ip/dropped?limit=50`)
      if (res.ok) {
        const data = await res.json()
        setDroppedPackets(data.packets || [])
        setDroppedStats(data.stats || { total_dropped: 0, by_type: {} })
      }
    } catch (err) {
      console.error('[useDroppedPackets] Failed to fetch:', err)
    }
  }, [])

  // Handle incoming dropped packet event
  const handleDroppedPacket = useCallback((packet) => {
    console.log('[useDroppedPackets] Received dropped packet:', packet)

    setDroppedPackets(prev => {
      // Add new packet at the beginning
      const updated = [packet, ...prev]
      // Keep only last 100 packets
      return updated.slice(0, 100)
    })

    // Update stats
    setDroppedStats(prev => ({
      total_dropped: (prev.total_dropped || 0) + 1,
      by_type: {
        ...prev.by_type,
        [packet.attack_type]: (prev.by_type[packet.attack_type] || 0) + 1
      }
    }))
  }, [])

  // Handle IP blocked event
  const handleIPBlocked = useCallback((data) => {
    console.log('[useDroppedPackets] IP blocked:', data)

    // Create a dropped packet entry for the block event
    const blockPacket = {
      timestamp: data.timestamp || new Date().toISOString(),
      source_ip: data.ip,
      attack_type: data.reason || 'blocked_ip',
      reason: 'blocked',
      endpoint: '*',
      method: '*',
      severity: data.severity || 'high',
      details: data.details || {}
    }

    handleDroppedPacket(blockPacket)
  }, [handleDroppedPacket])

  // Handle rate limited event
  const handleRateLimited = useCallback((data) => {
    console.log('[useDroppedPackets] IP rate limited:', data)

    const ratePacket = {
      timestamp: data.timestamp || new Date().toISOString(),
      source_ip: data.ip,
      attack_type: 'rate_limit',
      reason: 'rate-limited',
      endpoint: '*',
      method: '*',
      severity: 'medium',
      details: {
        new_limit: data.new_limit,
        duration: data.duration
      }
    }

    handleDroppedPacket(ratePacket)
  }, [handleDroppedPacket])

  // Setup socket listeners
  useEffect(() => {
    const socket = getSocket()

    if (!socket) {
      console.warn('[useDroppedPackets] Socket not available')
      return
    }

    // Connection status
    const handleConnect = () => {
      setIsConnected(true)
      console.log('[useDroppedPackets] Socket connected')
    }

    const handleDisconnect = () => {
      setIsConnected(false)
      console.log('[useDroppedPackets] Socket disconnected')
    }

    socket.on('connect', handleConnect)
    socket.on('disconnect', handleDisconnect)

    // Dropped packet events
    socket.on('ip:dropped', handleDroppedPacket)
    socket.on('ip:blocked', handleIPBlocked)
    socket.on('ip:rate_limited', handleRateLimited)

    // Check initial connection state
    if (socket.connected) {
      setIsConnected(true)
    }

    return () => {
      socket.off('connect', handleConnect)
      socket.off('disconnect', handleDisconnect)
      socket.off('ip:dropped', handleDroppedPacket)
      socket.off('ip:blocked', handleIPBlocked)
      socket.off('ip:rate_limited', handleRateLimited)
    }
  }, [handleDroppedPacket, handleIPBlocked, handleRateLimited])

  // Initial fetch and periodic polling
  useEffect(() => {
    // Initial fetch
    if (!initialFetchDone.current) {
      fetchDroppedPackets()
      initialFetchDone.current = true
    }

    // Poll for updates every 5 seconds as backup
    const interval = setInterval(fetchDroppedPackets, 5000)

    return () => clearInterval(interval)
  }, [fetchDroppedPackets])

  return {
    droppedPackets,
    droppedStats,
    isConnected,
    refresh: fetchDroppedPackets
  }
}

export default useDroppedPackets
