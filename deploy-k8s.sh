#!/bin/bash

# Deploy to Kubernetes

kubectl apply --validate=false -f k8s/ingest-service.yaml
kubectl apply --validate=false -f k8s/api-gateway.yaml
kubectl apply --validate=false -f k8s/detection-engine.yaml
kubectl apply --validate=false -f k8s/alert-manager.yaml
kubectl apply --validate=false -f k8s/response-engine.yaml
kubectl apply --validate=false -f k8s/frontend.yaml
kubectl apply --validate=false -f k8s/model-microservice.yaml
kubectl apply --validate=false -f k8s/ingress.yaml

echo "All services deployed to Kubernetes."