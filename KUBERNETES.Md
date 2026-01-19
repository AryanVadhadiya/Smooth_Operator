# Kubernetes Setup Guide for Threat Ops Application

This guide walks you through containerizing and deploying the Threat Ops application using Docker and Kubernetes.

## Prerequisites
- Docker Desktop (includes Kubernetes)
- Git
- kubectl (comes with Docker Desktop)

## Quick Start

### Step 1: Build Images (One-time)
```bash
cd k8s
./build-images.sh
```

### Step 2: Start Kubernetes Deployment
```bash
cd k8s
./kuber_start.sh
```
This deploys to K8s, installs dashboard, and starts port-forwards.

### 1. Enable Kubernetes
1. Open Docker Desktop
2. Settings > Kubernetes > Enable Kubernetes
3. Apply & Restart
4. Verify: `kubectl cluster-info`

### 2. Build and Deploy
```bash
# Build images
./build-images.sh

# Deploy to K8s
./deploy-k8s.sh

# Check status
kubectl get pods
kubectl get svc
```

### 3. Access Application
- **Frontend**: http://localhost:8080
- **API Gateway**: http://localhost:3001
- **System App**: http://localhost:5001
- **Dashboard**: https://localhost:8443 (token required)

## Architecture

### Services
- **frontend**: React app (LoadBalancer, port 80)
- **api-gateway**: FastAPI (ClusterIP, port 3001)
- **ingest-service**: FastAPI (ClusterIP, port 8001)
- **detection-engine**: FastAPI (ClusterIP, port 8002)
- **alert-manager**: FastAPI (ClusterIP, port 8003)
- **response-engine**: FastAPI (ClusterIP, port 8004)
- **systemapp**: Flask monitoring app (ClusterIP, port 5050)

### Load Balancing
- Services use round-robin load balancing
- Ingress routes HTTP traffic (/ → frontend, /api → api-gateway)
- Each service scales to 2 replicas by default

## Scaling

### Manual Scaling
```bash
kubectl scale deployment <service-name> --replicas=<number>
# Example: kubectl scale deployment api-gateway --replicas=5
```

### Auto-Scaling (HPA)
```bash
kubectl apply -f k8s/hpa.yaml  # Create HPA for CPU-based scaling
```

## Monitoring

### Kubernetes Dashboard
1. Install: Already done via deploy script
2. Access: `kubectl port-forward -n kubernetes-dashboard svc/kubernetes-dashboard 8443:443`
3. Login: Use token from `kubectl get secret dashboard-admin-token -n kubernetes-dashboard -o jsonpath="{.data.token}" | base64 --decode`

### Logs
```bash
kubectl logs -f deployment/<service-name>
```

## Custom Load Balancing

### Install NGINX Ingress (for advanced features)
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.10.1/deploy/static/provider/cloud/deploy.yaml
```

### Update Ingress for Custom Rules
Edit `k8s/ingress.yaml` with annotations:
```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/load-balance: "least_conn"
```

## Troubleshooting

### Pods Not Starting
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Images Not Pulling
Ensure `imagePullPolicy: Never` in YAMLs for local images.

### Dashboard Not Loading
Restart port-forward and check token.

## Production Deployment
- Push images to Docker Hub: `docker tag <image> <username>/<image> && docker push`
- Update YAMLs with registry URLs
- Use cloud K8s (EKS, GKE) instead of Docker Desktop
- Add persistent storage, secrets, and TLS

## Utility Scripts

### Scaling
```bash
./scale.sh <service-name> <replicas>
# Example: ./scale.sh api-gateway 5
```

### Viewing Logs
```bash
./logs.sh <service-name> [lines]
# Example: ./logs.sh api-gateway 50
```

### Checking Status
```bash
./status.sh
```

### Restarting Services
```bash
./restart.sh <service-name>
# Example: ./restart.sh api-gateway
```

### Stopping Services
```bash
./stop.sh
# Stops port-forwards and scales all deployments to 0
```

### Cleanup Everything
```bash
./cleanup.sh
# Deletes all deployments, services, ingress, and dashboard
```

## Auto-Scaling (HPA)

### Prerequisites
Metrics Server must be installed (done automatically):
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### Enable Auto-Scaling
```bash
./autoscale.sh enable
# Enables HPA for api-gateway, ingest-service, detection-engine
```

### Check Auto-Scaling Status
```bash
./autoscale.sh status
# Shows current replicas and scaling metrics
```

### Disable Auto-Scaling
```bash
./autoscale.sh disable
# Removes all HPAs, back to manual scaling
```

### How It Works
- **CPU Threshold**: Scales up when average CPU > 70%
- **Memory Threshold**: Scales up when average memory > 80%
- **Min/Max Replicas**: Prevents over/under scaling
- **Cooldown**: 5-minute stabilization period

### Custom HPA
Edit `hpa.yaml` to adjust thresholds or add more services.

## File Structure
```
k8s/
├── KUBERNETES.md
├── build-images.sh
├── deploy-k8s.sh
├── kuber_start.sh
├── scale.sh
├── logs.sh
├── status.sh
├── restart.sh
├── stop.sh
├── cleanup.sh
├── autoscale.sh
├── hpa.yaml
├── alert-manager.yaml
├── api-gateway.yaml
├── detection-engine.yaml
├── frontend.yaml
├── ingest-service.yaml
├── ingress.yaml
├── model-microservice.yaml
├── response-engine.yaml
└── systemapp.yaml
```

For questions, check the main README.md or open an issue.
