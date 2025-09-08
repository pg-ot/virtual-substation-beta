#!/bin/bash

# IEC 61850 GOOSE Communication Test Suite
# Tests all GOOSE functionalities between Protection Relay and Circuit Breaker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
RELAY_URL="http://localhost:8082"
BREAKER_URL="http://localhost:8081"
HMI_URL="http://localhost:8080"
WEB_URL="http://localhost:3000"

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=0

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_test() {
    echo -e "\n${YELLOW}TEST $((++TOTAL_TESTS)): $1${NC}"
}

print_pass() {
    echo -e "${GREEN}✅ PASS: $1${NC}"
    ((TESTS_PASSED++))
}

print_fail() {
    echo -e "${RED}❌ FAIL: $1${NC}"
    ((TESTS_FAILED++))
}

wait_for_goose() {
    echo "Waiting for GOOSE propagation..."
    sleep 2
}

get_relay_status() {
    curl -s "$RELAY_URL" | jq -r "$1"
}

get_breaker_status() {
    curl -s "$BREAKER_URL" | jq -r "$1"
}

# Test functions
test_system_health() {
    print_test "System Health Check"
    
    # Check container status
    if ! docker ps --format "{{.Names}}" | grep -q "protection_relay_ied"; then
        print_fail "Protection relay container not running"
        return 1
    fi
    
    if ! docker ps --format "{{.Names}}" | grep -q "circuit_breaker_ied"; then
        print_fail "Circuit breaker container not running"
        return 1
    fi
    
    # Check API endpoints
    if ! curl -s "$RELAY_URL" >/dev/null; then
        print_fail "Relay API not responding"
        return 1
    fi
    
    if ! curl -s "$BREAKER_URL" >/dev/null; then
        print_fail "Breaker API not responding"
        return 1
    fi
    
    print_pass "All systems operational"
}

test_initial_goose_communication() {
    print_test "Initial GOOSE Communication"
    
    local relay_rx_ok=$(get_relay_status '.rxOk')
    local relay_tx_ok=$(get_relay_status '.txOk')
    local breaker_rx_ok=$(get_breaker_status '.rxOk')
    
    if [[ "$relay_rx_ok" == "true" && "$relay_tx_ok" == "true" && "$breaker_rx_ok" == "true" ]]; then
        print_pass "GOOSE communication established"
    else
        print_fail "GOOSE communication issues (Relay RX:$relay_rx_ok TX:$relay_tx_ok, Breaker RX:$breaker_rx_ok)"
    fi
}

test_breaker_close_operation() {
    print_test "Circuit Breaker Close Operation"
    
    # Record initial state
    local initial_position=$(get_breaker_status '.position')
    
    # Close breaker
    curl -s -X POST "$BREAKER_URL/close" >/dev/null
    wait_for_goose
    
    # Verify breaker closed
    local new_position=$(get_breaker_status '.position')
    local relay_breaker_status=$(get_relay_status '.breakerStatus')
    
    if [[ "$new_position" == "CLOSED" ]]; then
        print_pass "Breaker closed successfully"
        
        # Check GOOSE feedback to relay
        if [[ "$relay_breaker_status" == "false" ]]; then
            print_pass "GOOSE status feedback to relay working"
        else
            print_fail "GOOSE status feedback failed (relay sees: $relay_breaker_status)"
        fi
    else
        print_fail "Breaker close failed (position: $new_position)"
    fi
}

test_relay_manual_trip() {
    print_test "Protection Relay Manual Trip"
    
    # Ensure breaker is closed first
    curl -s -X POST "$BREAKER_URL/close" >/dev/null
    wait_for_goose
    
    # Record initial message counts
    local initial_tx_count=$(get_relay_status '.txCount')
    local initial_rx_count=$(get_breaker_status '.messageCount')
    
    # Trip relay
    curl -s -X POST "$RELAY_URL/trip" >/dev/null
    wait_for_goose
    
    # Verify trip command sent
    local new_tx_count=$(get_relay_status '.txCount')
    local new_rx_count=$(get_breaker_status '.messageCount')
    local breaker_position=$(get_breaker_status '.position')
    
    if [[ $new_tx_count -gt $initial_tx_count ]]; then
        print_pass "GOOSE trip message transmitted"
    else
        print_fail "No GOOSE trip message sent"
    fi
    
    if [[ $new_rx_count -gt $initial_rx_count ]]; then
        print_pass "GOOSE trip message received by breaker"
    else
        print_fail "Breaker did not receive GOOSE message"
    fi
    
    if [[ "$breaker_position" == "OPEN" ]]; then
        print_pass "Breaker opened on trip command"
    else
        print_fail "Breaker failed to open (position: $breaker_position)"
    fi
}

test_relay_reset_operation() {
    print_test "Protection Relay Reset Operation"
    
    # Ensure relay is tripped first
    curl -s -X POST "$RELAY_URL/trip" >/dev/null
    wait_for_goose
    
    local initial_trip_status=$(get_relay_status '.tripCommand')
    
    # Reset relay
    curl -s -X POST "$RELAY_URL/reset" >/dev/null
    wait_for_goose
    
    local new_trip_status=$(get_relay_status '.tripCommand')
    local fault_detected=$(get_relay_status '.faultDetected')
    
    if [[ "$new_trip_status" == "false" && "$fault_detected" == "false" ]]; then
        print_pass "Relay reset successfully"
    else
        print_fail "Relay reset failed (trip: $new_trip_status, fault: $fault_detected)"
    fi
}

test_complete_operation_cycle() {
    print_test "Complete Operation Cycle"
    
    echo "  Step 1: Close breaker"
    curl -s -X POST "$BREAKER_URL/close" >/dev/null
    wait_for_goose
    
    echo "  Step 2: Trip relay"
    curl -s -X POST "$RELAY_URL/trip" >/dev/null
    wait_for_goose
    
    echo "  Step 3: Reset relay"
    curl -s -X POST "$RELAY_URL/reset" >/dev/null
    wait_for_goose
    
    echo "  Step 4: Close breaker again"
    curl -s -X POST "$BREAKER_URL/close" >/dev/null
    wait_for_goose
    
    # Verify final state
    local breaker_position=$(get_breaker_status '.position')
    local relay_trip=$(get_relay_status '.tripCommand')
    local relay_fault=$(get_relay_status '.faultDetected')
    
    if [[ "$breaker_position" == "CLOSED" && "$relay_trip" == "false" && "$relay_fault" == "false" ]]; then
        print_pass "Complete cycle executed successfully"
    else
        print_fail "Cycle incomplete (breaker: $breaker_position, trip: $relay_trip, fault: $relay_fault)"
    fi
}

test_goose_message_statistics() {
    print_test "GOOSE Message Statistics"
    
    local relay_tx_count=$(get_relay_status '.txCount')
    local relay_rx_count=$(get_relay_status '.rxCount')
    local breaker_rx_count=$(get_breaker_status '.messageCount')
    local breaker_stnum=$(get_breaker_status '.stNum')
    
    echo "  Relay TX: $relay_tx_count messages"
    echo "  Relay RX: $relay_rx_count messages"
    echo "  Breaker RX: $breaker_rx_count messages"
    echo "  Breaker State Changes: $breaker_stnum"
    
    if [[ $relay_tx_count -gt 0 && $relay_rx_count -gt 0 && $breaker_rx_count -gt 0 ]]; then
        print_pass "GOOSE message exchange active"
    else
        print_fail "Insufficient GOOSE message activity"
    fi
    
    # Check message consistency
    local tx_rx_diff=$((relay_tx_count - breaker_rx_count))
    if [[ $tx_rx_diff -ge -10 && $tx_rx_diff -le 10 ]]; then
        print_pass "Message counts consistent (diff: $tx_rx_diff)"
    else
        print_fail "Message count mismatch (TX: $relay_tx_count, RX: $breaker_rx_count)"
    fi
}

test_goose_supervision() {
    print_test "GOOSE Supervision and Health Monitoring"
    
    local relay_rx_ok=$(get_relay_status '.rxOk')
    local relay_tx_ok=$(get_relay_status '.txOk')
    local breaker_rx_ok=$(get_breaker_status '.rxOk')
    
    local relay_last_rx=$(get_relay_status '.lastRxMs')
    local relay_last_tx=$(get_relay_status '.lastTxMs')
    local breaker_last_rx=$(get_breaker_status '.lastRxMs')
    
    echo "  Relay RX Health: $relay_rx_ok (last: $relay_last_rx)"
    echo "  Relay TX Health: $relay_tx_ok (last: $relay_last_tx)"
    echo "  Breaker RX Health: $breaker_rx_ok (last: $breaker_last_rx)"
    
    if [[ "$relay_rx_ok" == "true" && "$relay_tx_ok" == "true" && "$breaker_rx_ok" == "true" ]]; then
        print_pass "GOOSE supervision healthy"
    else
        print_fail "GOOSE supervision issues detected"
    fi
}

test_bidirectional_communication() {
    print_test "Bidirectional GOOSE Communication"
    
    # Test Relay → Breaker direction
    curl -s -X POST "$RELAY_URL/trip" >/dev/null
    wait_for_goose
    local breaker_received_trip=$(get_breaker_status '.position')
    
    # Test Breaker → Relay direction  
    curl -s -X POST "$BREAKER_URL/close" >/dev/null
    wait_for_goose
    local relay_received_status=$(get_relay_status '.breakerStatus')
    
    if [[ "$breaker_received_trip" == "OPEN" ]]; then
        print_pass "Relay → Breaker communication working"
    else
        print_fail "Relay → Breaker communication failed"
    fi
    
    if [[ "$relay_received_status" == "false" ]]; then
        print_pass "Breaker → Relay communication working"
    else
        print_fail "Breaker → Relay communication failed"
    fi
}

# Performance test
test_goose_performance() {
    print_test "GOOSE Performance Test"
    
    echo "  Performing rapid operations..."
    
    local start_time=$(date +%s%N)
    
    # Rapid sequence of operations
    for i in {1..5}; do
        curl -s -X POST "$BREAKER_URL/close" >/dev/null
        sleep 0.5
        curl -s -X POST "$RELAY_URL/trip" >/dev/null
        sleep 0.5
        curl -s -X POST "$RELAY_URL/reset" >/dev/null
        sleep 0.5
    done
    
    local end_time=$(date +%s%N)
    local duration_ms=$(( (end_time - start_time) / 1000000 ))
    
    echo "  15 operations completed in ${duration_ms}ms"
    
    # Check system still healthy
    local relay_rx_ok=$(get_relay_status '.rxOk')
    local breaker_rx_ok=$(get_breaker_status '.rxOk')
    
    if [[ "$relay_rx_ok" == "true" && "$breaker_rx_ok" == "true" ]]; then
        print_pass "System stable under load"
    else
        print_fail "System degraded under load"
    fi
}

# Main test execution
main() {
    print_header "IEC 61850 GOOSE Communication Test Suite"
    
    echo "Testing GOOSE communication between Protection Relay and Circuit Breaker"
    echo "Relay API: $RELAY_URL"
    echo "Breaker API: $BREAKER_URL"
    
    # Execute all tests
    test_system_health
    test_initial_goose_communication
    test_breaker_close_operation
    test_relay_manual_trip
    test_relay_reset_operation
    test_complete_operation_cycle
    test_goose_message_statistics
    test_goose_supervision
    test_bidirectional_communication
    test_goose_performance
    
    # Final report
    print_header "Test Results Summary"
    echo -e "Total Tests: $TOTAL_TESTS"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "\n${GREEN}🎉 ALL TESTS PASSED - GOOSE Communication Fully Operational${NC}"
        exit 0
    else
        echo -e "\n${RED}⚠️  Some tests failed - Check GOOSE configuration${NC}"
        exit 1
    fi
}

# Run tests
main "$@"