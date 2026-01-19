#!/bin/bash

# Stop Kubernetes port-forwards and scale down deployments
# Usage: ./stop.sh

echo "🛑 Stopping port-forwards..."
pkill -f "kubectl port-forward" || echo "No port-forwards running"

echo "📉 Scaling all deployments to 0 replicas..."
kubectl scale deployment --all --replicas=0

echo "✅ All services stopped and scaled down"
echo "💡 To restart: ./kuber_start.sh"
echo "🧹 To cleanup completely: ./cleanup.sh"