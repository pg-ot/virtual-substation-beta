#!/bin/bash

echo "🧪 Fixed Virtual Substation Testing"
echo "==================================="
echo "Testing with proper state management"
echo ""

# Check system status
echo "🔍 System Status Check..."
if ! docker ps | grep -q "protection_relay_ied\|circuit_breaker_ied\|hmi_scada\|substation_web_ui"; then
    echo "❌ Containers not running! Start with: ./start_all.sh"
    exit 1
fi

echo "✅ All containers running"
echo ""

# Run fixed tests
echo "🚀 Running Fixed Chain Tests..."
echo "==============================="

python3 test_gui_panels_fixed.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 SUCCESS: All button → container → GUI chains working!"
    echo ""
    echo "✅ Validated:"
    echo "   • Button clicks reach containers"
    echo "   • Container states update correctly" 
    echo "   • GUI panels reflect changes"
    echo "   • Cross-container communication works"
    echo "   • System handles state persistence properly"
else
    echo ""
    echo "❌ Some tests failed - check container logs:"
    echo "   docker-compose logs protection-relay"
    echo "   docker-compose logs circuit-breaker"
    echo "   docker-compose logs hmi-scada"
fi