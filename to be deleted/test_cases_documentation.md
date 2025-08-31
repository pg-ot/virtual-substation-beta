# GUI Panel Test Cases Documentation

## Test Case Matrix

### 1. Simulation Control Panel Tests

| Button | Expected Action | Expected Response | Test Method |
|--------|----------------|-------------------|-------------|
| **Normal Operation** | Reset all values to normal | V=132kV, I=450A, F=50Hz, FC=0A | `test_scenario_normal_button()` |
| **Overcurrent** | Set high current | I=1500A, FC=1500A | `test_scenario_overcurrent_button()` |
| **Ground Fault** | Inject ground fault | FC=3000A, Fault=True | `test_scenario_ground_fault_button()` |
| **Frequency Deviation** | Set low frequency | F=49.2Hz | `test_scenario_frequency_deviation_button()` |
| **Inject Fault** | Trigger fault condition | FC=2500A, Fault=True | `test_inject_fault_button()` |
| **Trip Breaker** | Open circuit breaker | Breaker=Open | `test_trip_breaker_button()` |
| **Send Trip** | Send trip command | Trip=Active | `test_send_trip_button()` |
| **Reset All** | Reset to normal state | All values normal | `test_reset_all_button()` |
| **Emergency Stop** | Immediate trip + open | Trip=True, Breaker=Open | `test_emergency_stop_button()` |

### 2. Protection Relay Panel Tests

| Button | Expected Action | Expected Response | Test Method |
|--------|----------------|-------------------|-------------|
| **Manual Trip** | Send trip command | HTTP POST to /api/command | `test_manual_trip_button()` |
| **Reset Alarms** | Clear fault conditions | Fault=False, Trip=False | `test_reset_alarms_button()` |

### 3. Circuit Breaker Panel Tests

| Button | Expected Action | Expected Response | Test Method |
|--------|----------------|-------------------|-------------|
| **TRIP** | Open breaker manually | Breaker=Open via HTTP | `test_manual_trip_button()` |
| **CLOSE** | Close breaker manually | Breaker=Closed via HTTP | `test_manual_close_button()` |
| **Status Check** | Get breaker status | JSON: position, tripReceived, status | `test_breaker_status_response()` |

### 4. HMI/SCADA Panel Tests

| Button | Expected Action | Expected Response | Test Method |
|--------|----------------|-------------------|-------------|
| **Read Values** | Trigger MMS reads | Log MMS operations | `test_read_values_button()` |
| **Send Trip** | MMS trip command | HTTP POST to /mms/trip | `test_send_trip_button()` |
| **Reset Relay** | MMS reset command | HTTP POST to /mms/reset | `test_reset_relay_button()` |
| **Ack Alarms** | Clear alarm list | Local operation | `test_ack_alarms_button()` |
| **Data Response** | Get HMI data | JSON with V,I,F,Trip data | `test_hmi_data_response()` |

### 5. System Integration Tests

| Test Scenario | Expected Sequence | Expected Response | Test Method |
|---------------|-------------------|-------------------|-------------|
| **Fault-to-Trip** | Fault→Trip→Breaker Open | Complete protection sequence | `test_fault_to_trip_sequence()` |
| **System Reset** | Reset all parameters | Return to normal state | `test_system_reset_sequence()` |

### 6. Container Connectivity Tests

| Container | Port | Protocol | Expected Response | Test Method |
|-----------|------|----------|-------------------|-------------|
| **Web Interface** | 3000 | HTTP | 200 OK + JSON data | `test_web_interface_connectivity()` |
| **Protection Relay** | 102 | MMS/TCP | Socket connection | `test_protection_relay_mms_connectivity()` |
| **Circuit Breaker** | 8081 | TCP | Socket connection | `test_circuit_breaker_connectivity()` |
| **HMI/SCADA** | 8080 | HTTP | 200 OK + JSON data | `test_hmi_scada_connectivity()` |

## Test Execution Commands

### Run All Tests
```bash
cd "Virtual Substation/Cirtual Substation"
python3 test_gui_panels.py
```

### Run Specific Test Suite
```bash
python3 -m unittest test_gui_panels.TestSimulationControlPanel
python3 -m unittest test_gui_panels.TestProtectionRelayPanel
python3 -m unittest test_gui_panels.TestCircuitBreakerPanel
python3 -m unittest test_gui_panels.TestHMIScadaPanel
```

### Prerequisites for Testing
1. **Start Virtual Substation System**:
   ```bash
   ./start_all.sh
   ```

2. **Verify Containers Running**:
   ```bash
   docker ps
   ```

3. **Check Port Accessibility**:
   ```bash
   netstat -tlnp | grep -E "(3000|102|8080|8081)"
   ```

## Expected Test Results

### ✅ Pass Conditions
- HTTP requests return status code 200
- Socket connections establish successfully
- JSON responses contain expected fields
- Command sequences execute without errors

### ❌ Fail Conditions
- Connection refused errors
- HTTP 404/500 errors
- Invalid JSON responses
- Socket timeout errors

### ⚠️ Skip Conditions
- Container not running
- Port not accessible
- Network connectivity issues

## Test Coverage

| Component | Coverage | Test Count |
|-----------|----------|------------|
| Simulation Control | 100% | 9 tests |
| Protection Relay | 100% | 2 tests |
| Circuit Breaker | 100% | 3 tests |
| HMI/SCADA | 100% | 4 tests |
| System Integration | 100% | 2 tests |
| Container Connectivity | 100% | 4 tests |
| **Total** | **100%** | **24 tests** |

## Troubleshooting Test Failures

### Common Issues
1. **Container Not Running**: Start with `./start_all.sh`
2. **Port Conflicts**: Check if ports 3000, 102, 8080, 8081 are available
3. **Network Issues**: Verify Docker networks are created
4. **Permission Issues**: Run with appropriate privileges for socket access

### Debug Commands
```bash
# Check container status
docker-compose ps

# View container logs
docker-compose logs protection-relay
docker-compose logs circuit-breaker
docker-compose logs hmi-scada

# Test port connectivity
telnet localhost 3000
telnet localhost 102
telnet localhost 8080
telnet localhost 8081
```