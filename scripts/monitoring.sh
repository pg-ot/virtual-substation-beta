#!/bin/bash
# Production Monitoring Script

echo "📊 IEC 61850 System Monitoring"

while true; do
  echo "$(date): System Health Check"
  
  # Container health
  docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(protection|circuit|hmi|web)"
  
  # GOOSE statistics
  echo "GOOSE Stats:"
  echo "  Relay TX: $(curl -s http://localhost:8082 2>/dev/null | jq -r '.txCount // "N/A"')"
  echo "  Breaker RX: $(curl -s http://localhost:8081 2>/dev/null | jq -r '.messageCount // "N/A"')"
  
  # Resource usage
  echo "Resource Usage:"
  docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep -E "(protection|circuit|hmi|web)"
  
  echo "---"
  sleep 60
done