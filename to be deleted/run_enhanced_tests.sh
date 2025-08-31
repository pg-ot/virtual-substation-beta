#!/bin/bash

echo "🧪 Enhanced Virtual Substation Testing"
echo "======================================"
echo "Testing: Button Press → Container Effect → GUI Update"
echo ""

# Check if system is running
echo "🔍 Checking system status..."

# Check containers
containers=("protection_relay_ied" "circuit_breaker_ied" "hmi_scada" "substation_web_ui")
all_running=true

for container in "${containers[@]}"; do
    if docker ps --format "table {{.Names}}" | grep -q "$container"; then
        echo "✅ $container: Running"
    else
        echo "❌ $container: Not running"
        all_running=false
    fi
done

if [ "$all_running" = false ]; then
    echo ""
    echo "💡 Start the system first: ./start_all.sh"
    exit 1
fi

# Check ports
echo ""
echo "🔌 Checking port accessibility..."
ports=(3000 102 8080 8081)
for port in "${ports[@]}"; do
    if nc -z localhost $port 2>/dev/null; then
        echo "✅ Port $port: Accessible"
    else
        echo "⚠️  Port $port: Not accessible"
    fi
done

echo ""
echo "🚀 Running Enhanced Chain Tests..."
echo "=================================="

# Run the enhanced test suite
python3 test_gui_panels_enhanced.py

# Check test result
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 All button → container → GUI chains working!"
    echo "📊 Complete integration validated"
else
    echo ""
    echo "❌ Some chain tests failed!"
    echo "📋 Check the detailed output above"
    exit 1
fi

echo ""
echo "📝 Test validates:"
echo "   • Button clicks trigger correct commands"
echo "   • Commands reach target containers"
echo "   • Container states update correctly"
echo "   • GUI panels reflect container changes"
echo "   • Cross-container communication works"