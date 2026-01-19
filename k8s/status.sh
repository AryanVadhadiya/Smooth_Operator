#!/bin/bash

# Check status of Kubernetes pods and services

echo "📊 Pod Status:"
kubectl get pods

echo ""
echo "🔗 Service Status:"
kubectl get svc

echo ""
echo "📈 Deployment Status:"
kubectl get deployments

echo ""
echo "🌐 Ingress Status:"
kubectl get ingress