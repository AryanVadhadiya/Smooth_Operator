#!/bin/bash

# View logs for Kubernetes deployments
# Usage: ./logs.sh <service-name> [lines]

if [ $# -lt 1 ]; then
    echo "Usage: $0 <service-name> [lines]"
    echo "Example: $0 api-gateway 50"
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
LINES=${2:-20}  # Default to 20 lines

echo "📋 Showing last $LINES lines of logs for $SERVICE..."
kubectl logs deployment/$SERVICE --tail=$LINES