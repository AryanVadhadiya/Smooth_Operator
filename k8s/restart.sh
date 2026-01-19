#!/bin/bash

# Restart Kubernetes deployments
# Usage: ./restart.sh <service-name>

if [ $# -ne 1 ]; then
    echo "Usage: $0 <service-name>"
    echo "Example: $0 api-gateway"
    echo ""
    echo "Available services:"
    echo "  - frontend"
    echo "  - api-gateway"
    echo "  - ingest-service"
    echo "  - detection-engine"
    echo "  - alert-manager"
    echo "  - response-engine"
    echo "  - model-microservice"
    echo "  - systemapp"
    exit 1
fi

SERVICE=$1

echo "🔄 Restarting $SERVICE..."
kubectl rollout restart deployment $SERVICE

if [ $? -eq 0 ]; then
    echo "✅ Restarted $SERVICE"
    kubectl get pods -l app=$SERVICE
else
    echo "❌ Failed to restart $SERVICE"
fi