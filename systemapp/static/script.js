document.addEventListener('DOMContentLoaded', () => {
    const consoleBody = document.getElementById('console-output');
    
    // Get server IP from localStorage or use default
    let serverIP = localStorage.getItem('serverIP') || '10.110.5.98:8001';
    document.getElementById('server-ip').value = serverIP;
    
    // Auto-update server config on page load if localStorage has a value
    if (localStorage.getItem('serverIP')) {
        fetch('/config', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ server_ip: serverIP })
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

    // Polling Status and Health
    fetchStatus();
    fetchHealth();
    setInterval(fetchStatus, 5000);
    setInterval(fetchHealth, 2000); // Update health metrics every 2 seconds

    // Update Uptime (Mock)
    let seconds = 0;
    setInterval(() => {
        seconds++;
        const h = Math.floor(seconds / 3600).toString().padStart(2, '0');
        const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
        const s = (seconds % 60).toString().padStart(2, '0');
        document.getElementById('uptime').innerText = `${h}:${m}:${s}`;
    }, 1000);


    // Handle Forms
    const handleForm = async (formId, url, payloadBuilder) => {
        const form = document.getElementById(formId);
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const payload = payloadBuilder();
            
            log(`EXECUTING ATTACK ON ${url}...`, 'system');
            
            try {
                const res = await fetch(url, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                
                const data = await res.json();
                
                if (res.ok) {
                    log(`> RESPONSE: ${JSON.stringify(data)}`, 'success');
                } else {
                    log(`> ERROR [${res.status}]: ${JSON.stringify(data)}`, 'error');
                }
                
            } catch (err) {
                log(`> NETWORK ERROR: ${err}`, 'error');
            }
        });
    };

    handleForm('auth-form', '/login', () => ({
        username: document.getElementById('username').value
    }));

    handleForm('sql-form', '/data', () => ({
        query: document.getElementById('query').value
    }));

    // Handle Server Configuration
    document.getElementById('server-config-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        serverIP = document.getElementById('server-ip').value;
        localStorage.setItem('serverIP', serverIP);
        
        try {
            const res = await fetch('/config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ server_ip: serverIP })
            });
            
            const data = await res.json();
            
            if (res.ok) {
                log(`✅ TARGET SERVER UPDATED: ${serverIP}`, 'success');
            } else {
                log(`❌ FAILED TO UPDATE SERVER: ${JSON.stringify(data)}`, 'error');
            }
        } catch (err) {
            log(`❌ ERROR UPDATING SERVER: ${err}`, 'error');
        }
    });

    // Clear Console
    document.getElementById('clear-console').addEventListener('click', () => {
        consoleBody.innerHTML = '';
        log("CONSOLE CLEARED.", 'system');
    });
});
