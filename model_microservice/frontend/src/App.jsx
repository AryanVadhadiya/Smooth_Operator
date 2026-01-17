import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts';
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Heart,
  Sprout,
  Building2,
  Server,
  BarChart3
} from 'lucide-react';
import './App.css';

const API_URL = 'http://127.0.0.1:5000/api/dashboard';
const POLL_INTERVAL = 1500; // 1.5 seconds

// ═══════════════════════════════════════════════════════════════
// HEADER COMPONENT
// ═══════════════════════════════════════════════════════════════
function Header({ isConnected }) {
  return (
    <header className="header">
      <div className="header-content">
        <div className="logo">
          <h1>PROJECT A.E.G.I.S.</h1>
          <span className="subtitle">// ADVANCED GUARDIAN INTELLIGENCE SYSTEM</span>
        </div>
        <div className="status-indicator">
          <div className={`status-dot ${isConnected ? '' : 'offline'}`}></div>
          <span className="status-text">
            {isConnected ? 'SYSTEM ONLINE' : 'DISCONNECTED'}
          </span>
        </div>
      </div>
    </header>
  );
}

// ═══════════════════════════════════════════════════════════════
// SECTOR CARD COMPONENT
// ═══════════════════════════════════════════════════════════════
function SectorCard({ sector, icon: IconComponent, logs }) {
  const sectorLogs = logs.filter(log => log.sector === sector);
  const recentLog = sectorLogs[sectorLogs.length - 1];
  const isCritical = recentLog && ['blocked', 'quarantined', 'isolated'].includes(recentLog.status);
  
  const threatCount = sectorLogs.filter(
    log => ['blocked', 'quarantined', 'isolated'].includes(log.status)
  ).length;
  
  const descriptions = {
    healthcare: 'IoMT Medical Device Network',
    agriculture: 'Smart Farming Sensors',
    urban: 'Smart City Infrastructure'
  };

  return (
    <div className={`sector-card ${isCritical ? 'critical' : ''}`}>
      <div className="sector-header">
        <div className={`sector-icon ${sector}`}>
          <IconComponent size={24} />
        </div>
        <span className={`sector-status ${isCritical ? 'critical' : 'safe'}`}>
          {isCritical ? 'CRITICAL' : 'SAFE'}
        </span>
      </div>
      <h3 className="sector-name">{sector.toUpperCase()}</h3>
      <p className="sector-description">{descriptions[sector]}</p>
      <div className="sector-metrics">
        <div className="metric">
          <div className="metric-label">Total Packets</div>
          <div className="metric-value">{sectorLogs.length}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Threats</div>
          <div className={`metric-value ${threatCount > 0 ? 'danger' : ''}`}>
            {threatCount}
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// THREAT LOG COMPONENT
// ═══════════════════════════════════════════════════════════════
function ThreatLog({ logs }) {
  const formatTime = (timestamp) => {
    if (!timestamp) return '--:--:--';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour12: false });
  };

  return (
    <div className="threat-log">
      <div className="terminal-header">
        <div className="terminal-dots">
          <span className="terminal-dot red"></span>
          <span className="terminal-dot yellow"></span>
          <span className="terminal-dot green"></span>
        </div>
        <span className="terminal-title">THREAT_MONITOR.exe — Live Feed</span>
      </div>
      <div className="terminal-body">
        {logs.length === 0 ? (
          <div className="connection-error">
            <AlertTriangle size={32} className="error-icon" />
            <p className="error-message">AWAITING DATA STREAM...</p>
            <p className="error-hint">Start simulation_driver.py to begin</p>
          </div>
        ) : (
          [...logs].reverse().map((log, index) => (
            <div key={log.id || index} className="log-entry">
              <span className="log-timestamp">{formatTime(log.timestamp)}</span>
              <span className={`log-sector ${log.sector}`}>
                [{log.sector?.toUpperCase() || 'UNKNOWN'}]
              </span>
              <span className={`log-status ${log.status}`}>
                {log.status?.toUpperCase() || 'N/A'}
              </span>
              <span className="log-message">
                {log.message || log.messages?.[0] || 'Packet analyzed'}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// NETWORK CHART COMPONENT
// ═══════════════════════════════════════════════════════════════
function NetworkChart({ logs }) {
  // Process logs into time-series data using useMemo
  const chartData = useMemo(() => {
    const timeSlots = {};
    
    logs.forEach(log => {
      if (!log.timestamp) return;
      const time = new Date(log.timestamp);
      const key = time.toLocaleTimeString('en-US', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
      });
      
      if (!timeSlots[key]) {
        timeSlots[key] = { time: key, traffic: 0, threats: 0 };
      }
      
      timeSlots[key].traffic += 1;
      if (['blocked', 'quarantined', 'isolated'].includes(log.status)) {
        timeSlots[key].threats += 1;
      }
    });

    return Object.values(timeSlots).slice(-20);
  }, [logs]);

  return (
    <div className="network-chart">
      <div className="chart-header">
        <h3 className="chart-title">
          <BarChart3 size={16} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
          NETWORK ACTIVITY
        </h3>
        <div className="chart-legend">
          <div className="legend-item">
            <span className="legend-dot traffic"></span>
            Traffic
          </div>
          <div className="legend-item">
            <span className="legend-dot threats"></span>
            Threats
          </div>
        </div>
      </div>
      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="trafficGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#00ff41" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#00ff41" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="threatGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ff003c" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#ff003c" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis 
              dataKey="time" 
              stroke="#52525b"
              tick={{ fill: '#52525b', fontSize: 10 }}
              tickLine={{ stroke: '#52525b' }}
            />
            <YAxis 
              stroke="#52525b"
              tick={{ fill: '#52525b', fontSize: 10 }}
              tickLine={{ stroke: '#52525b' }}
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: '#0d1117',
                border: '1px solid rgba(0, 255, 65, 0.2)',
                borderRadius: '4px',
                color: '#e4e4e7'
              }}
            />
            <Area
              type="monotone"
              dataKey="traffic"
              stroke="#00ff41"
              strokeWidth={2}
              fill="url(#trafficGradient)"
            />
            <Area
              type="monotone"
              dataKey="threats"
              stroke="#ff003c"
              strokeWidth={2}
              fill="url(#threatGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// STATS BAR COMPONENT
// ═══════════════════════════════════════════════════════════════
function StatsBar({ logs }) {
  const totalPackets = logs.length;
  const blockedCount = logs.filter(
    log => ['blocked', 'quarantined', 'isolated'].includes(log.status)
  ).length;
  const allowedCount = totalPackets - blockedCount;
  const threatRate = totalPackets > 0 
    ? ((blockedCount / totalPackets) * 100).toFixed(1) 
    : '0.0';

  return (
    <div className="stats-bar">
      <div className="stat-item">
        <Server size={24} className="stat-icon" />
        <div className="stat-content">
          <span className="stat-value">{totalPackets}</span>
          <span className="stat-label">Total Packets</span>
        </div>
      </div>
      <div className="stat-item">
        <CheckCircle size={24} className="stat-icon" style={{ color: '#00ff41' }} />
        <div className="stat-content">
          <span className="stat-value" style={{ color: '#00ff41' }}>{allowedCount}</span>
          <span className="stat-label">Allowed</span>
        </div>
      </div>
      <div className="stat-item">
        <XCircle size={24} className="stat-icon" style={{ color: '#ff003c' }} />
        <div className="stat-content">
          <span className="stat-value" style={{ color: '#ff003c' }}>{blockedCount}</span>
          <span className="stat-label">Blocked</span>
        </div>
      </div>
      <div className="stat-item">
        <AlertTriangle size={24} className="stat-icon" style={{ color: '#ffcc00' }} />
        <div className="stat-content">
          <span className="stat-value" style={{ color: '#ffcc00' }}>{threatRate}%</span>
          <span className="stat-label">Threat Rate</span>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// MAIN APP COMPONENT
// ═══════════════════════════════════════════════════════════════
function App() {
  const [logs, setLogs] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const fetchDashboard = useCallback(async () => {
    try {
      const response = await fetch(API_URL);
      if (!response.ok) throw new Error('Network response was not ok');
      
      const data = await response.json();
      setLogs(data.logs || []);
      setIsConnected(true);
      setIsLoading(false);
    } catch (error) {
      console.error('Failed to fetch dashboard:', error);
      setIsConnected(false);
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchDashboard]);

  if (isLoading) {
    return (
      <div className="loading">
        <div className="loading-spinner"></div>
        <span className="loading-text">INITIALIZING A.E.G.I.S...</span>
      </div>
    );
  }

  return (
    <div className="app">
      <Header isConnected={isConnected} />
      
      <main className="dashboard">
        {/* Sector Status Cards */}
        <div className="sector-cards">
          <SectorCard 
            sector="healthcare" 
            icon={Heart} 
            color="cyan"
            logs={logs}
          />
          <SectorCard 
            sector="agriculture" 
            icon={Sprout} 
            color="yellow"
            logs={logs}
          />
          <SectorCard 
            sector="urban" 
            icon={Building2} 
            color="purple"
            logs={logs}
          />
        </div>

        {/* Threat Log Terminal */}
        <ThreatLog logs={logs} />

        {/* Network Activity Chart */}
        <NetworkChart logs={logs} />

        {/* Stats Bar */}
        <StatsBar logs={logs} />
      </main>
    </div>
  );
}

export default App;
