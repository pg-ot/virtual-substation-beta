#!/bin/bash

echo "📋 Formal Test Cases Execution"
echo "=============================="
echo "Running official test case specifications"
echo ""

# System check
if ! docker ps | grep -q "protection_relay_ied\|circuit_breaker_ied\|hmi_scada\|substation_web_ui"; then
    echo "❌ Virtual Substation not running!"
    echo "💡 Start with: ./start_all.sh"
    exit 1
fi

echo "✅ System ready for formal testing"
echo ""

# Run formal test cases
echo "🧪 Executing Formal Test Cases..."
echo "=================================="

python3 test_cases_formal.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 ALL FORMAL TEST CASES PASSED!"
    echo ""
    echo "📋 Test Coverage Summary:"
    echo "   A. Simulation Control Panel: 7 test cases"
    echo "   B. Protection Relay IED: 2 test cases"  
    echo "   C. Circuit Breaker IED: 2 test cases"
    echo "   D. HMI/SCADA MMS Client: 4 test cases"
    echo ""
    echo "✅ All button functions meet official specifications"
else
    echo ""
    echo "❌ Some formal test cases failed!"
    echo "📋 Review test results above for details"
fi