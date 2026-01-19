#!/bin/bash

# Scale Kubernetes deployments
# Usage: ./scale.sh <service-name> <replicas>

if [ $# -ne 2 ]; then
    echo "Usage: $0 <service-name> <replicas>"
    echo "Example: $0 api-gateway 5"
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
REPLICAS=$2

echo "📊 Scaling $SERVICE to $REPLICAS replicas..."
kubectl scale deployment $SERVICE --replicas=$REPLICAS

if [ $? -eq 0 ]; then
    echo "✅ Scaled $SERVICE to $REPLICAS replicas"
    kubectl get pods -l app=$SERVICE
else
    echo "❌ Failed to scale $SERVICE"
fi