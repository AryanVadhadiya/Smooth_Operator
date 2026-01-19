#!/bin/bash

# Cleanup Kubernetes resources
# Usage: ./cleanup.sh

echo "🧹 Cleaning up Kubernetes resources..."

# Delete deployments and services
echo "Deleting deployments and services..."
kubectl delete deployment --all
kubectl delete service --all
kubectl delete ingress --all

# Delete dashboard
echo "Deleting Kubernetes Dashboard..."
kubectl delete -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml

# Delete configmaps and secrets (optional)
echo "Deleting configmaps and secrets..."
kubectl delete configmap --all
kubectl delete secret --all

# Delete PVCs if any
echo "Deleting persistent volume claims..."
kubectl delete pvc --all

echo "✅ Cleanup complete!"
echo "💡 To redeploy: ./kuber_start.sh"