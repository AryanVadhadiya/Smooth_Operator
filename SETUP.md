# CyberThreat_Ops Setup Guide

## Complete Installation & Deployment Guide

This guide provides step-by-step instructions for setting up the CyberThreat_Ops system.

---

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Quick Start (Docker)](#quick-start-docker)
3. [Manual Installation](#manual-installation)
4. [Configuration](#configuration)
5. [Running the System](#running-the-system)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **OS**: macOS, Linux, or Windows 10/11 with WSL2
- **RAM**: 8GB
- **Disk**: 10GB free space
- **CPU**: 4 cores
- **Docker**: v20.10+
- **Docker Compose**: v2.0+
- **Python**: 3.11+ (for standalone scripts)

### Recommended
- **RAM**: 16GB
- **CPU**: 8 cores
- **SSD Storage**: For better performance

---

## Quick Start (Docker)

### Step 1: Clone Repository
```bash
git clone https://github.com/yourusername/CyberThreat_Ops.git
cd CyberThreat_Ops
```

### Step 2: Start Services
```bash
chmod +x start.sh
./start.sh
```

This will:
- Start InfluxDB, Redis, RabbitMQ, Grafana
- Launch the FastAPI backend
- Display access URLs

### Step 3: Access Dashboard
1. Open `src/dashboard/index.html` in your browser
2. Click "Train All Models"
3. Simulate an attack to test the system

**That's it! The system is now running.**

---

## Manual Installation

### Step 1: Install Python Dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Start Infrastructure Services

**Option A: Using Docker**
```bash
docker-compose up -d influxdb redis rabbitmq grafana
```

**Option B: Local Installation**
- Install InfluxDB 2.7+
- Install Redis 7+
- Install RabbitMQ 3+
- Configure according to `.env.example`

### Step 3: Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### Step 4: Start API Server
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Configuration

### 1. Environment Variables

Edit `.env` file:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# InfluxDB
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=cyberops-token-2026
INFLUXDB_ORG=cyberops
INFLUXDB_BUCKET=monitoring

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# Email Alerts (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL_TO=admin@example.com

# Slack Alerts (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK

# Detection Settings
ANOMALY_THRESHOLD=0.8
FALSE_POSITIVE_TARGET=0.01

# Response Settings
AUTO_RESPONSE_ENABLED=True
REQUIRE_APPROVAL_P0=True
REQUIRE_APPROVAL_P1=True
```

### 2. System Configuration

Edit `config/config.yaml` to customize:
- Sector-specific settings
- Detection algorithm parameters
- Alert severity levels
- Response action policies

### 3. Grafana Dashboards (Optional)

1. Access Grafana: http://localhost:3000
2. Login: admin/admin
3. Add InfluxDB data source
4. Import pre-built dashboards from `config/grafana/`

---

## Running the System

### Option 1: Full Demo Script
```bash
python demo.py
```

Demonstrates all features end-to-end.

### Option 2: Interactive API
```bash
# Start API server
uvicorn src.api.main:app --reload

# Access API docs
open http://localhost:8000/docs
```

### Option 3: Custom Integration
```python
from src.simulators import HealthcareSimulator
from src.detection import AnomalyDetectionEngine
import yaml

# Load config
with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

# Initialize components
simulator = HealthcareSimulator(num_devices=5)
engine = AnomalyDetectionEngine(config)

# Generate and analyze data
data = [simulator.generate_normal_data(simulator.devices[0]['id']) 
        for _ in range(100)]
engine.train(data, sector='healthcare')

# Test detection
test = [simulator.generate_anomalous_data(simulator.devices[0]['id'], 'ransomware')
        for _ in range(10)]
results = engine.detect(test)

print(f"Detected: {sum(1 for r in results if r['is_anomaly'])}/10 anomalies")
```

---

## Verification

### 1. Check Service Health
```bash
# Check Docker containers
docker-compose ps

# Check API health
curl http://localhost:8000/health

# Check system status
curl http://localhost:8000/system/status
```

Expected output:
```json
{
  "status": "operational",
  "monitoring_active": false,
  "sectors": ["healthcare", "agriculture", "urban"]
}
```

### 2. Run Tests
```bash
pytest tests/test_system.py -v
```

Expected: All tests should pass.

### 3. Test Detection Pipeline

**Train models:**
```bash
curl -X POST http://localhost:8000/train/healthcare?num_samples=500
```

**Simulate attack:**
```bash
curl -X POST http://localhost:8000/simulate-attack \
  -H "Content-Type: application/json" \
  -d '{
    "sector": "healthcare",
    "attack_type": "ransomware",
    "num_samples": 10
  }'
```

**Check alerts:**
```bash
curl http://localhost:8000/alerts
```

### 4. Verify Dashboard
1. Open `src/dashboard/index.html`
2. Check that "System Status" shows "Operational"
3. Click "Train All Models"
4. Simulate an attack
5. Verify alerts appear in real-time

---

## Troubleshooting

### Issue: Docker containers won't start

**Solution:**
```bash
# Stop all containers
docker-compose down

# Remove volumes
docker-compose down -v

# Restart
docker-compose up -d
```

### Issue: Port already in use

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process or change port in docker-compose.yml
```

### Issue: Models not training

**Solution:**
```bash
# Check Python dependencies
pip install --upgrade scikit-learn tensorflow

# Increase training samples
curl -X POST http://localhost:8000/train/healthcare?num_samples=1000

# Check logs
docker-compose logs api
```

### Issue: Alerts not being created

**Solution:**
1. Verify models are trained: `curl http://localhost:8000/system/status`
2. Check detection threshold in `config/config.yaml`
3. Simulate a high-severity attack
4. Check API logs: `docker-compose logs api`

### Issue: Dashboard not updating

**Solution:**
1. Open browser console (F12) for errors
2. Verify API is accessible: `curl http://localhost:8000/health`
3. Clear browser cache
4. Ensure CORS is enabled in API

### Issue: Low detection rates

**Solution:**
1. Increase training samples: `num_samples=2000`
2. Adjust contamination parameter in config
3. Enable more detection algorithms
4. Review false positive rate

---

## Performance Tuning

### 1. Optimize Detection Speed
```yaml
# config/config.yaml
detection:
  algorithms:
    - name: "isolation_forest"
      enabled: true
      n_estimators: 50  # Reduce for speed
      contamination: 0.1
```

### 2. Reduce False Positives
```yaml
detection:
  algorithms:
    - name: "statistical_zscore"
      threshold: 4.0  # Increase threshold
```

### 3. Scale Horizontally
```bash
# docker-compose.yml
api:
  deploy:
    replicas: 3
```

---

## Production Deployment

### 1. Kubernetes Deployment
```bash
# Create namespace
kubectl create namespace cyberops

# Deploy services
kubectl apply -f k8s/

# Expose API
kubectl port-forward svc/cyberops-api 8000:8000 -n cyberops
```

### 2. Environment Hardening
- Use secrets management (Vault, AWS Secrets Manager)
- Enable TLS/SSL for API
- Configure firewall rules
- Set up log aggregation
- Enable monitoring (Prometheus + Grafana)

### 3. Backup Strategy
```bash
# Backup InfluxDB
docker exec cyberops_influxdb influxd backup /backup

# Backup models
tar -czf models_backup.tar.gz models/

# Backup configuration
tar -czf config_backup.tar.gz config/
```

---

## Next Steps

1. **Explore API**: http://localhost:8000/docs
2. **Run Demo**: `python demo.py`
3. **Customize**: Edit `config/config.yaml`
4. **Test**: `pytest tests/ -v`
5. **Monitor**: http://localhost:3000 (Grafana)

---

## Support Resources

- **Documentation**: See README.md
- **API Reference**: http://localhost:8000/docs
- **Issues**: GitHub Issues
- **Email**: support@cyberops.example.com

---

## Quick Reference

### Useful Commands
```bash
# Start system
./start.sh

# Stop system
docker-compose down

# View logs
docker-compose logs -f api

# Run tests
pytest tests/ -v

# Run demo
python demo.py

# Train models
curl -X POST http://localhost:8000/train/{sector}

# Simulate attack
curl -X POST http://localhost:8000/simulate-attack

# Check status
curl http://localhost:8000/system/status
```

### Default Ports
- API: 8000
- InfluxDB: 8086
- Grafana: 3000
- RabbitMQ Management: 15672
- Redis: 6379

### Default Credentials
- Grafana: admin/admin
- RabbitMQ: guest/guest
- InfluxDB: admin/adminpassword

---

**You're all set! 🚀**
