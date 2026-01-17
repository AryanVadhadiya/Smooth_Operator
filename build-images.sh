#!/bin/bash

set -e  # Exit on any error

# Build Docker images for all services

cd backend/ingest-service
docker build -t ingest-service:latest .

cd ../api-gateway
docker build -t api-gateway:latest .

cd ../detection-engine
docker build -t detection-engine:latest .

cd ../alert-manager
docker build -t alert-manager:latest .

cd ../response-engine
docker build -t response-engine:latest .

cd ../../frontend
docker build -t frontend:latest .

cd ../model_microservice
docker build -t model-microservice:latest .

echo "All images built successfully."