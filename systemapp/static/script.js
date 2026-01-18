document.addEventListener('DOMContentLoaded', () => {
    const consoleBody = document.getElementById('console-output');

    // Get server IP from localStorage or use default
    let serverIP = localStorage.getItem('serverIP') || 'localhost:8001';
    document.getElementById('server-ip').value = serverIP;

    // Current sector and devices
    let currentSector = localStorage.getItem('sector') || 'healthcare';
    let devices = {};
    let selectedDevice = localStorage.getItem('selectedDevice') || null;

    // Set sector dropdown to current value
    const sectorSelect = document.getElementById('sector-select');
    sectorSelect.value = currentSector;

    // Auto-update server config on page load if localStorage has a value
    if (localStorage.getItem('serverIP') || localStorage.getItem('sector')) {
        fetch('/config', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ server_ip: serverIP, sector: currentSector })
        }).catch(err => console.error('Failed to auto-update server config:', err));
    }

    // Logger function
    function log(msg, type = 'system') {
        const line = document.createElement('div');
        line.className = `log-line ${type}`;
        const time = new Date().toLocaleTimeString('en-US', {hour12: false});
        line.innerHTML = `<span style="opacity:0.5">[${time}]</span> ${msg}`;
        consoleBody.appendChild(line);
        consoleBody.scrollTop = consoleBody.scrollHeight;
    }

    // Get device icon based on type
    function getDeviceIcon(type) {
        const icons = {
            'pacemaker': '❤️',
            'mri_scanner': '🔬',
            'infusion_pump': '💉',
            'soil_sensor': '🌱',
            'drone_scout': '🚁',
            'irrigation_valve': '💧',
            'traffic_light': '🚦',
            'smart_meter': '⚡'
        };
        return icons[type] || '📟';
    }

    // Render devices grid
    function renderDevices() {
        const grid = document.getElementById('device-grid');
        const sectorLabel = document.getElementById('current-sector-label');

        sectorLabel.textContent = `SECTOR: ${currentSector.toUpperCase()}`;

        if (Object.keys(devices).length === 0) {
            grid.innerHTML = `<div class="no-devices"><span>📡</span>Loading devices...</div>`;
            return;
        }

        grid.innerHTML = '';
        Object.entries(devices).forEach(([id, info]) => {
            const health = info.health || 100;
            const status = info.status || 'online';
            const type = info.type || 'unknown';

            let healthClass = 'healthy';
            let cardClass = '';
            if (health < 70) { healthClass = 'warning'; cardClass = 'warning'; }
            if (health < 30) { healthClass = 'critical'; cardClass = 'critical'; }

            const isSelected = selectedDevice === id;
            if (isSelected) cardClass += ' selected target-indicator';

            const card = document.createElement('div');
            card.className = `device-card ${cardClass}`;
            card.dataset.deviceId = id;
            card.innerHTML = `
                <div class="device-icon">${getDeviceIcon(type)}</div>
                <div class="device-name">${id}</div>
                <div class="device-type">${type.replace('_', ' ')}</div>
                <div class="device-health">
                    <div class="health-bar">
                        <div class="health-fill ${healthClass}" style="width: ${health}%"></div>
                    </div>
                    <span class="health-value ${healthClass}">${health}%</span>
                </div>
                <div class="device-status ${status}">${status.toUpperCase()}</div>
            `;

            // Click to select as target
            card.addEventListener('click', () => {
                selectedDevice = isSelected ? null : id;
                localStorage.setItem('selectedDevice', selectedDevice || '');
                renderDevices();
                if (selectedDevice) {
                    log(`🎯 Target device set: ${selectedDevice}`, 'success');
                    // Notify backend of selected target
                    fetch('/config', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ target_device: selectedDevice })
                    });
                } else {
                    log(`🎯 Target device cleared`, 'system');
                }
            });

            grid.appendChild(card);
        });
    }

    // Fetch devices from server
    async function fetchDevices() {
        try {
            const res = await fetch('/devices');
            const data = await res.json();
            devices = data.devices || {};
            currentSector = data.sector || currentSector;
            sectorSelect.value = currentSector;
            renderDevices();
        } catch (e) {
            console.error('Failed to fetch devices:', e);
        }
    }

    // Fetch System Status
    async function fetchStatus() {
        try {
            const res = await fetch('/status');
            const data = await res.json();

            document.getElementById('device-name').innerText = data.device.toUpperCase();
            document.getElementById('conn-status').innerText = "CONNECTED // ONLINE";
            document.getElementById('conn-status').style.borderColor = "var(--primary)";
            document.getElementById('conn-status').style.color = "var(--primary)";

        } catch (e) {
            document.getElementById('conn-status').innerText = "CONNECTION LOST";
            document.getElementById('conn-status').style.borderColor = "var(--alert)";
            document.getElementById('conn-status').style.color = "var(--alert)";
            log("FAILED TO CONTACT AGENT...", "error");
        }
    }

    // Fetch System Health Metrics
    async function fetchHealth() {
        try {
            const res = await fetch('/health');
            const data = await res.json();

            if (data.error) return;

            // Basic metrics
            document.getElementById('cpu-usage').innerText = `${data.cpu}%`;
            document.getElementById('memory-usage').innerText = `${data.memory}%`;
            document.getElementById('disk-usage').innerText = `${data.disk}%`;
            document.getElementById('device-ip').innerText = data.device_ip;

            // System resources
            document.getElementById('cpu-cores').innerText = `${data.cpu_cores} / ${data.cpu_threads}`;
            document.getElementById('total-memory').innerText = `${data.total_memory_gb} GB`;

            // Process and load
            document.getElementById('processes').innerText = data.processes;
            document.getElementById('load-avg').innerText = data.load_avg !== null ? data.load_avg : 'N/A';

            // Network stats
            document.getElementById('network-sent').innerText = `${data.network_sent_mb} MB`;
            document.getElementById('network-recv').innerText = `${data.network_recv_mb} MB`;

            // Update uptime from server
            if (data.uptime_seconds) {
                seconds = data.uptime_seconds;
            }

        } catch (e) {
            // Silently fail - health metrics are non-critical
        }
    }

    // Polling Status, Health and Devices
    fetchStatus();
    fetchHealth();
    fetchDevices();
    setInterval(fetchStatus, 5000);
    setInterval(fetchHealth, 2000);
    setInterval(fetchDevices, 3000); // Update devices every 3 seconds

    // Update Uptime (Mock)
    let seconds = 0;
    setInterval(() => {
        seconds++;
        const h = Math.floor(seconds / 3600).toString().padStart(2, '0');
        const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
        const s = (seconds % 60).toString().padStart(2, '0');
        document.getElementById('uptime').innerText = `${h}:${m}:${s}`;
    }, 1000);


    // Handle Server Configuration
    document.getElementById('server-config-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        serverIP = document.getElementById('server-ip').value;
        const newSector = document.getElementById('sector-select').value;

        localStorage.setItem('serverIP', serverIP);
        localStorage.setItem('sector', newSector);

        try {
            const res = await fetch('/config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ server_ip: serverIP, sector: newSector })
            });

            const data = await res.json();

            if (res.ok) {
                log(`✅ TARGET SERVER UPDATED: ${serverIP}`, 'success');
                if (newSector !== currentSector) {
                    currentSector = newSector;
                    selectedDevice = null; // Clear selection on sector change
                    localStorage.removeItem('selectedDevice');
                    log(`🔄 SECTOR CHANGED: ${currentSector.toUpperCase()}`, 'success');
                    fetchDevices(); // Refresh devices
                }
            } else {
                log(`❌ FAILED TO UPDATE SERVER: ${JSON.stringify(data)}`, 'error');
            }
        } catch (err) {
            log(`❌ ERROR UPDATING SERVER: ${err}`, 'error');
        }
    });

    // Heal All Devices
    document.getElementById('heal-all-btn').addEventListener('click', async () => {
        try {
            const res = await fetch('/devices/heal', { method: 'POST' });
            if (res.ok) {
                log(`🔧 All devices healed`, 'success');
                fetchDevices();
            }
        } catch (err) {
            log(`❌ Failed to heal devices: ${err}`, 'error');
        }
    });

    // Reset Fleet
    document.getElementById('reset-devices-btn').addEventListener('click', async () => {
        try {
            const res = await fetch('/devices/reset', { method: 'POST' });
            if (res.ok) {
                log(`🔄 Fleet reset to defaults`, 'success');
                selectedDevice = null;
                localStorage.removeItem('selectedDevice');
                fetchDevices();
            }
        } catch (err) {
            log(`❌ Failed to reset fleet: ${err}`, 'error');
        }
    });

    // Clear Console
    document.getElementById('clear-console').addEventListener('click', () => {
        consoleBody.innerHTML = '';
        log("CONSOLE CLEARED.", 'system');
    });

    // Initial render
    renderDevices();
});
