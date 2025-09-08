#!/bin/bash

# Simple GOOSE Test Script
set -e

echo "=== GOOSE Communication Test ==="

# Test 1: System Health
echo "TEST 1: System Health"
if curl -s http://localhost:8082 >/dev/null && curl -s http://localhost:8081 >/dev/null; then
    echo "✅ APIs responding"
else
    echo "❌ API failure"
    exit 1
fi

# Test 2: Initial Status
echo -e "\nTEST 2: Initial Status"
echo "Relay:" && curl -s http://localhost:8082 | jq '{tripCommand,breakerStatus,rxOk,txOk}'
echo "Breaker:" && curl -s http://localhost:8081 | jq '{position,rxOk}'

# Test 3: Breaker Close
echo -e "\nTEST 3: Breaker Close"
curl -s -X POST http://localhost:8081/close
sleep 2
echo "After close:" && curl -s http://localhost:8081 | jq '{position}'

# Test 4: Relay Trip
echo -e "\nTEST 4: Relay Trip"
curl -s -X POST http://localhost:8082/trip
sleep 2
echo "After trip:" && curl -s http://localhost:8081 | jq '{position}'

# Test 5: Relay Reset
echo -e "\nTEST 5: Relay Reset"
curl -s -X POST http://localhost:8082/reset
sleep 2
echo "After reset:" && curl -s http://localhost:8082 | jq '{tripCommand}'

# Test 6: GOOSE Statistics
echo -e "\nTEST 6: GOOSE Statistics"
echo "Relay TX/RX:" && curl -s http://localhost:8082 | jq '{txCount,rxCount,txOk,rxOk}'
echo "Breaker RX:" && curl -s http://localhost:8081 | jq '{messageCount,rxOk}'

echo -e "\n✅ All tests completed successfully!"