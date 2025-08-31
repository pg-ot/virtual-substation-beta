#!/bin/bash

echo "📋 Fixed Formal Test Cases"
echo "=========================="
echo "Handles GOOSE communication timing"
echo ""

if ! docker ps | grep -q "protection_relay_ied\|circuit_breaker_ied\|hmi_scada\|substation_web_ui"; then
    echo "❌ Virtual Substation not running!"
    echo "💡 Start with: ./start_all.sh"
    exit 1
fi

echo "✅ System ready"
echo ""

echo "🧪 Running Fixed Formal Test Cases..."
echo "====================================="

python3 test_cases_formal_fixed.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 ALL FORMAL TEST CASES PASSED!"
    echo ""
    echo "✅ Fixed Issues:"
    echo "   • GOOSE communication timing handled"
    echo "   • Trip command processing validated"
    echo "   • Breaker response timing accounted for"
    echo ""
    echo "📋 All 15 test cases meet specifications"
else
    echo ""
    echo "❌ Some tests still failing"
fi