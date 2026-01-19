#!/bin/bash

cd "$(dirname "$0")"

# Enable auto-scaling (HPA) for services
# Usage: ./autoscale.sh [enable|disable|status]

ACTION=${1:-enable}

case $ACTION in
  enable)
    echo "📈 Enabling auto-scaling for key services..."
    kubectl apply -f hpa.yaml
    echo "✅ Auto-scaling enabled!"
    echo "📊 Check status: ./autoscale.sh status"
    ;;
  disable)
    echo "📉 Disabling auto-scaling..."
    kubectl delete hpa --all
    echo "✅ Auto-scaling disabled"
    ;;
  status)
    echo "📊 HPA Status:"
    kubectl get hpa
    ;;
  *)
    echo "Usage: $0 [enable|disable|status]"
    echo "  enable  - Enable auto-scaling (default)"
    echo "  disable - Disable auto-scaling"
    echo "  status  - Show HPA status"
    ;;
esac