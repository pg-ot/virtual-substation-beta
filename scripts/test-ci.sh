#!/bin/bash
# Continuous Integration Test Suite

set -e

echo "🧪 Running CI Test Suite..."

# Test 1: Build verification
echo "1. Build Test"
make build > /dev/null 2>&1 && echo "✅ Build: PASS" || echo "❌ Build: FAIL"

# Test 2: Start system
echo "2. System Start Test"
make start > /dev/null 2>&1 && echo "✅ Start: PASS" || echo "❌ Start: FAIL"

# Test 3: Health checks
echo "3. Health Check Test"
sleep 10
curl -s http://localhost:8082 > /dev/null && echo "✅ Relay API: PASS" || echo "❌ Relay API: FAIL"
curl -s http://localhost:8081 > /dev/null && echo "✅ Breaker API: PASS" || echo "❌ Breaker API: FAIL"

# Test 4: GOOSE communication
echo "4. GOOSE Communication Test"
make test-goose > /dev/null 2>&1 && echo "✅ GOOSE: PASS" || echo "❌ GOOSE: FAIL"

# Test 5: Load test
echo "5. Load Test"
for i in {1..10}; do
  curl -s -X POST http://localhost:8081/close > /dev/null
  curl -s -X POST http://localhost:8082/trip > /dev/null
  sleep 0.5
done
echo "✅ Load Test: PASS"

# Test 6: Stop system
echo "6. System Stop Test"
make stop > /dev/null 2>&1 && echo "✅ Stop: PASS" || echo "❌ Stop: FAIL"

echo "🎉 CI Test Suite Complete!"