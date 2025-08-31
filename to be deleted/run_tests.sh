#!/bin/bash

echo "🧪 Virtual Substation GUI Panel Testing"
echo "========================================"

# Check if system is running
echo "🔍 Checking system status..."

# Check if containers are running
if ! docker ps | grep -q "protection_relay_ied\|circuit_breaker_ied\|hmi_scada\|substation_web_ui"; then
    echo "❌ Virtual Substation containers not running!"
    echo "💡 Start the system first: ./start_all.sh"
    exit 1
fi

# Check if ports are accessible
echo "🔌 Checking port accessibility..."

ports=(3000 102 8080 8081)
for port in "${ports[@]}"; do
    if ! nc -z localhost $port 2>/dev/null; then
        echo "⚠️  Port $port not accessible"
    else
        echo "✅ Port $port accessible"
    fi
done

echo ""
echo "🚀 Running GUI Panel Tests..."
echo "==============================="

# Run the test suite
python3 test_gui_panels.py

# Check test result
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 All tests completed successfully!"
    echo "📊 Test report generated above"
else
    echo ""
    echo "❌ Some tests failed!"
    echo "📋 Check the detailed output above for failure reasons"
    exit 1
fi

echo ""
echo "📝 For detailed test documentation, see: test_cases_documentation.md"