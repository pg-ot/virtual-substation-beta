#!/bin/bash

cd "$(dirname "$0")"/.. || exit 1

echo "Building Virtual Substation with IEC 61850..."

# Build Docker images
echo "Building Protection Relay IED..."
docker build -f config/Dockerfile.protection-relay -t protection-relay:latest .

echo "Building Circuit Breaker IED..."
docker build -f config/Dockerfile.circuit-breaker -t circuit-breaker:latest .

echo "Building HMI/SCADA..."
docker build -f config/Dockerfile.hmi-scada -t hmi-scada:latest .

echo "Build complete!"
echo ""
echo "To start the virtual substation:"
echo "  docker-compose up"
echo ""
echo "To stop the virtual substation:"
echo "  docker-compose down"