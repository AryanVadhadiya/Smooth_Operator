#!/bin/bash

# Deploy to Kubernetes

kubectl apply --validate=false -f ingest-service.yaml
kubectl apply --validate=false -f api-gateway.yaml
kubectl apply --validate=false -f detection-engine.yaml
kubectl apply --validate=false -f alert-manager.yaml
kubectl apply --validate=false -f response-engine.yaml
kubectl apply --validate=false -f frontend.yaml
kubectl apply --validate=false -f model-microservice.yaml
kubectl apply --validate=false -f systemapp.yaml
kubectl apply --validate=false -f ingress.yaml

echo "All services deployed to Kubernetes."