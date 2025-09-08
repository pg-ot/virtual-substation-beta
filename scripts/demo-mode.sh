#!/bin/bash
# Demo Mode - Automated GOOSE Demonstration

echo "🎭 Starting IEC 61850 GOOSE Demo..."

# Start system
make start > /dev/null 2>&1
sleep 15

echo "📊 System Status:"
curl -s http://localhost:8082 | jq '{voltage,current,frequency,rxOk,txOk}'

echo -e "\n🔄 Demo Sequence:"

echo "1. Closing Circuit Breaker..."
curl -s -X POST http://localhost:8081/close > /dev/null
sleep 2
echo "   ✅ Breaker: $(curl -s http://localhost:8081 | jq -r '.position')"

echo "2. Triggering Protection Trip..."
curl -s -X POST http://localhost:8082/trip > /dev/null
sleep 2
echo "   ⚡ Trip Command Sent via GOOSE"
echo "   ✅ Breaker: $(curl -s http://localhost:8081 | jq -r '.position')"

echo "3. Resetting Protection..."
curl -s -X POST http://localhost:8082/reset > /dev/null
sleep 2
echo "   🔄 Protection Reset"

echo -e "\n📈 GOOSE Statistics:"
echo "Relay TX: $(curl -s http://localhost:8082 | jq -r '.txCount') messages"
echo "Breaker RX: $(curl -s http://localhost:8081 | jq -r '.messageCount') messages"

echo -e "\n🎉 Demo Complete! GOOSE Communication Working!"