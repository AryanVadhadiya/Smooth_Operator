#!/bin/bash

# KUBER START SCRIPT
# Starts Kubernetes deployment (run after building images)

cd "$(dirname "$0")"

set -e  # Exit on error

echo "🚀 Starting Threat Ops Kubernetes Deployment..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install Docker Desktop with Kubernetes enabled."
    exit 1
fi

# Check if K8s is running
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Kubernetes cluster not running. Please enable Kubernetes in Docker Desktop and try again."
    exit 1
fi

echo "✅ Kubernetes cluster detected"

# Check if images exist
if ! docker images | grep -q "ingest-service"; then
    echo "❌ Images not found. Please run ./build-images.sh first."
    exit 1
fi

echo "✅ Docker images found"

# Deploy services
echo "🚢 Deploying to Kubernetes..."
./deploy-k8s.sh

# Wait for deployments to be available
echo "⏳ Waiting for deployments to be available..."
kubectl wait --for=condition=available deployment --all --timeout=300s

# Wait for pods to be ready
echo "⏳ Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod --all --timeout=300s

# Install Dashboard
echo "📊 Installing Kubernetes Dashboard..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml

# Wait for dashboard to be ready
echo "⏳ Waiting for dashboard to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/kubernetes-dashboard -n kubernetes-dashboard

# Create admin access
echo "🔑 Setting up dashboard access..."
kubectl create serviceaccount dashboard-admin -n kubernetes-dashboard --dry-run=client -o yaml | kubectl apply -f -
kubectl create clusterrolebinding dashboard-admin-binding --clusterrole=cluster-admin --serviceaccount=kubernetes-dashboard:dashboard-admin --dry-run=client -o yaml | kubectl apply -f -

# Create token secret
kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: dashboard-admin-token
  namespace: kubernetes-dashboard
  annotations:
    kubernetes.io/service-account.name: dashboard-admin
type: kubernetes.io/service-account-token
EOF

# Wait for token
sleep 5

# Get token
echo "🔑 Dashboard Token:"
TOKEN=$(kubectl get secret dashboard-admin-token -n kubernetes-dashboard -o jsonpath="{.data.token}" | base64 --decode)
echo "$TOKEN"
echo ""

# Start port-forwards
echo "🌐 Starting port-forwards..."
pkill -f "kubectl port-forward" || true  # Kill any existing port-forwards
sleep 2

kubectl port-forward -n kubernetes-dashboard svc/kubernetes-dashboard 8443:443 >/dev/null 2>&1 &
kubectl port-forward svc/frontend 8080:80 >/dev/null 2>&1 &
kubectl port-forward svc/api-gateway 3001:3001 >/dev/null 2>&1 &
kubectl port-forward svc/ingest-service 8001:8001 >/dev/null 2>&1 &
kubectl port-forward svc/systemapp 5001:5050 >/dev/null 2>&1 &

echo ""
echo "✅ Deployment complete!"
echo "Port-Forwards Active:"
echo "  Frontend: http://localhost:8080"
echo "  API Gateway: http://localhost:3001"
echo "  Ingest Service: http://localhost:8001 (for headless agents)"
echo "  System App: http://localhost:5001"
echo "  Dashboard: https://localhost:8443"
echo "  Token: $TOKEN"
echo ""
echo "🛑 To stop: pkill -f port-forward"
echo "📊 To scale: kubectl scale deployment <service> --replicas=<num>"