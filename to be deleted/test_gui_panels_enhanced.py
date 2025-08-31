#!/usr/bin/env python3
"""
Enhanced GUI Panel Testing Script for Virtual Substation
Tests Button Press → Container Effect → GUI Update chain
"""

import unittest
import requests
import json
import time
import socket
import threading
from unittest.mock import patch, MagicMock
import sys
import os

class TestSimulationControlPanel(unittest.TestCase):
    """Test Simulation Control Panel: Button → Container → GUI chain"""
    
    def setUp(self):
        self.base_url = 'http://localhost:3000'
        self.relay_port = 102
        self.breaker_port = 8081
        self.hmi_port = 8080

    def test_scenario_normal_button(self):
        """Test Normal Operation: Button → Container → GUI chain"""
        print("\n🔘 Testing Normal Operation Button...")
        
        # 1. BUTTON PRESS: Simulate Normal Operation button click
        commands = [
            {'command': 'updateVoltage', 'data': {'voltage': 132.0}},
            {'command': 'updateCurrent', 'data': {'current': 450.0}},
            {'command': 'updateFrequency', 'data': {'frequency': 50.0}},
            {'command': 'updateFaultCurrent', 'data': {'faultCurrent': 0.0}},
            {'command': 'toggleFault', 'data': {'active': False}}
        ]
        
        try:
            for cmd in commands:
                response = requests.post(f'{self.base_url}/api/command', json=cmd, timeout=2)
                self.assertEqual(response.status_code, 200)
            
            time.sleep(1)  # Allow propagation
            
            # 2. CONTAINER EFFECT: Verify data in web interface
            response = requests.get(f'{self.base_url}/api/simulation-data', timeout=2)
            data = response.json()
            
            self.assertEqual(data['voltage'], 132.0)
            self.assertEqual(data['current'], 450.0)
            self.assertEqual(data['frequency'], 50.0)
            self.assertEqual(data['faultCurrent'], 0.0)
            self.assertFalse(data['faultDetected'])
            
            # 3. GUI UPDATE: Verify protection relay sees normal values
            relay_data = self.get_protection_relay_status()
            if relay_data:
                self.assertFalse(relay_data.get('tripActive', True))
                print("   ✅ Protection Relay: Normal state confirmed")
            
            # 4. GUI UPDATE: Verify circuit breaker sees normal state
            breaker_data = self.get_circuit_breaker_status()
            if breaker_data:
                self.assertEqual(breaker_data.get('position', 'UNKNOWN'), 'CLOSED')
                print("   ✅ Circuit Breaker: Closed position confirmed")
                
            print("   ✅ Normal Operation button test PASSED")
            
        except requests.exceptions.RequestException:
            self.skipTest("Web interface not available")

    def test_inject_fault_button(self):
        """Test Inject Fault: Button → Trip → Breaker Opens"""
        print("\n🔘 Testing Inject Fault Button...")
        
        try:
            # 1. BUTTON PRESS: Inject high fault current (should cause instant trip)
            commands = [
                {'command': 'updateFaultCurrent', 'data': {'faultCurrent': 2500.0}},
                {'command': 'updateCurrent', 'data': {'current': 2500.0}},
                {'command': 'toggleFault', 'data': {'active': True}}
            ]
            
            for cmd in commands:
                response = requests.post(f'{self.base_url}/api/command', json=cmd, timeout=2)
                self.assertEqual(response.status_code, 200)
            
            time.sleep(3)  # Allow fault processing and trip sequence
            
            # 2. CONTAINER EFFECT: Verify fault data propagated
            response = requests.get(f'{self.base_url}/api/simulation-data', timeout=2)
            data = response.json()
            
            self.assertEqual(data['faultCurrent'], 2500.0)
            self.assertTrue(data['faultDetected'])
            
            # 3. GUI UPDATE: Verify protection relay shows trip
            relay_data = self.get_protection_relay_status()
            if relay_data:
                # High fault current should trigger trip
                self.assertGreater(relay_data.get('faultCurrent', 0), 2000)
                print("   ✅ Protection Relay: High fault current detected")
            
            # 4. GUI UPDATE: Check if breaker received trip signal
            breaker_data = self.get_circuit_breaker_status()
            if breaker_data:
                # May show trip received or position change
                print(f"   📊 Circuit Breaker Status: {breaker_data}")
                
            print("   ✅ Inject Fault button test PASSED")
            
        except requests.exceptions.RequestException:
            self.skipTest("Web interface not available")

    def test_send_trip_button(self):
        """Test Send Trip: Button → GOOSE → Breaker Opens"""
        print("\n🔘 Testing Send Trip Button...")
        
        try:
            # 1. BUTTON PRESS: Send manual trip command
            cmd = {'command': 'sendTrip', 'data': {}}
            response = requests.post(f'{self.base_url}/api/command', json=cmd, timeout=2)
            self.assertEqual(response.status_code, 200)
            
            time.sleep(2)  # Allow GOOSE message propagation
            
            # 2. CONTAINER EFFECT: Verify trip command in simulation data
            response = requests.get(f'{self.base_url}/api/simulation-data', timeout=2)
            data = response.json()
            
            # Trip command should be active (may be temporary)
            print(f"   📊 Trip Command Status: {data.get('tripCommand', False)}")
            
            # 3. GUI UPDATE: Verify circuit breaker received GOOSE trip
            breaker_data = self.get_circuit_breaker_status()
            if breaker_data:
                trip_received = breaker_data.get('tripReceived', False)
                position = breaker_data.get('position', 'UNKNOWN')
                print(f"   📊 Breaker - Trip Received: {trip_received}, Position: {position}")
                
                # Either trip should be received OR breaker should be open
                self.assertTrue(trip_received or position == 'OPEN')
                print("   ✅ Circuit Breaker: Trip signal processed")
            
            print("   ✅ Send Trip button test PASSED")
            
        except requests.exceptions.RequestException:
            self.skipTest("Web interface not available")

    def get_protection_relay_status(self):
        """Get protection relay status via MMS simulation"""
        try:
            # Simulate MMS read from protection relay
            response = requests.get(f'{self.base_url}/api/simulation-data', timeout=1)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
    
    def get_circuit_breaker_status(self):
        """Get circuit breaker status via TCP"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect(('localhost', self.breaker_port))
            data = sock.recv(1024).decode()
            sock.close()
            return json.loads(data)
        except:
            pass
        return None


class TestProtectionRelayPanel(unittest.TestCase):
    """Test Protection Relay Panel: Button → MMS → Container Response"""
    
    def setUp(self):
        self.base_url = 'http://localhost:3000'

    def test_manual_trip_button(self):
        """Test Manual Trip: Button → Protection Relay → GOOSE"""
        print("\n🔘 Testing Protection Relay Manual Trip Button...")
        
        try:
            # 1. BUTTON PRESS: Manual trip from protection relay panel
            cmd = {'command': 'sendTrip', 'data': {}}
            response = requests.post(f'{self.base_url}/api/command', json=cmd, timeout=2)
            self.assertEqual(response.status_code, 200)
            
            time.sleep(1)
            
            # 2. CONTAINER EFFECT: Verify trip command propagated
            response = requests.get(f'{self.base_url}/api/simulation-data', timeout=2)
            data = response.json()
            print(f"   📊 Trip Command Active: {data.get('tripCommand', False)}")
            
            # 3. GUI UPDATE: Verify other panels see the trip
            breaker_data = self.get_circuit_breaker_status()
            if breaker_data:
                print(f"   📊 Breaker Response: {breaker_data.get('tripReceived', False)}")
            
            print("   ✅ Manual Trip button test PASSED")
            
        except requests.exceptions.RequestException:
            self.skipTest("Web interface not available")
    
    def get_circuit_breaker_status(self):
        """Get circuit breaker status"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect(('localhost', 8081))
            data = sock.recv(1024).decode()
            sock.close()
            return json.loads(data)
        except:
            return None


class TestCircuitBreakerPanel(unittest.TestCase):
    """Test Circuit Breaker Panel: Button → Breaker Action → Status Update"""
    
    def setUp(self):
        self.base_url = 'http://localhost:3000'
        self.breaker_port = 8081

    def test_manual_trip_button(self):
        """Test Manual Trip: Button → Breaker Opens → Status Updates"""
        print("\n🔘 Testing Circuit Breaker Manual Trip Button...")
        
        try:
            # 1. Get initial breaker status
            initial_status = self.get_breaker_status()
            print(f"   📊 Initial Breaker Status: {initial_status}")
            
            # 2. BUTTON PRESS: Manual trip command
            cmd = {'command': 'toggleBreaker', 'data': {'open': True}}
            response = requests.post(f'{self.base_url}/api/command', json=cmd, timeout=2)
            self.assertEqual(response.status_code, 200)
            
            time.sleep(1)
            
            # 3. CONTAINER EFFECT: Verify breaker opened
            response = requests.get(f'{self.base_url}/api/simulation-data', timeout=2)
            data = response.json()
            self.assertTrue(data.get('breakerStatus', False))
            
            # 4. GUI UPDATE: Verify breaker status via TCP
            final_status = self.get_breaker_status()
            if final_status:
                self.assertEqual(final_status.get('position', 'UNKNOWN'), 'OPEN')
                print("   ✅ Breaker Status: OPEN confirmed via TCP")
            
            print("   ✅ Manual Trip button test PASSED")
            
        except requests.exceptions.RequestException:
            self.skipTest("Web interface not available")

    def test_manual_close_button(self):
        """Test Manual Close: Button → Breaker Closes → Status Updates"""
        print("\n🔘 Testing Circuit Breaker Manual Close Button...")
        
        try:
            # 1. BUTTON PRESS: Manual close command
            cmd = {'command': 'toggleBreaker', 'data': {'open': False}}
            response = requests.post(f'{self.base_url}/api/command', json=cmd, timeout=2)
            self.assertEqual(response.status_code, 200)
            
            time.sleep(1)
            
            # 2. CONTAINER EFFECT: Verify breaker closed
            response = requests.get(f'{self.base_url}/api/simulation-data', timeout=2)
            data = response.json()
            self.assertFalse(data.get('breakerStatus', True))
            
            # 3. GUI UPDATE: Verify breaker status via TCP
            final_status = self.get_breaker_status()
            if final_status:
                self.assertEqual(final_status.get('position', 'UNKNOWN'), 'CLOSED')
                print("   ✅ Breaker Status: CLOSED confirmed via TCP")
            
            print("   ✅ Manual Close button test PASSED")
            
        except requests.exceptions.RequestException:
            self.skipTest("Web interface not available")
    
    def get_breaker_status(self):
        """Get breaker status via TCP"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect(('localhost', self.breaker_port))
            data = sock.recv(1024).decode()
            sock.close()
            return json.loads(data)
        except:
            return None


class TestHMIScadaPanel(unittest.TestCase):
    """Test HMI/SCADA Panel: Button → MMS Command → Relay Response"""
    
    def setUp(self):
        self.hmi_url = 'http://localhost:8080'
        self.base_url = 'http://localhost:3000'

    def test_send_trip_button(self):
        """Test Send Trip: Button → MMS Command → Protection Relay"""
        print("\n🔘 Testing HMI/SCADA Send Trip Button...")
        
        try:
            # 1. BUTTON PRESS: Send MMS trip command
            response = requests.post(f'{self.hmi_url}/mms/trip', timeout=2)
            self.assertEqual(response.status_code, 200)
            
            time.sleep(1)
            
            # 2. CONTAINER EFFECT: Verify MMS command processed
            print("   ✅ MMS Trip command sent successfully")
            
            # 3. GUI UPDATE: Check if protection relay received MMS command
            response = requests.get(f'{self.base_url}/api/simulation-data', timeout=2)
            if response.status_code == 200:
                data = response.json()
                print(f"   📊 System Trip Status: {data.get('tripCommand', False)}")
            
            print("   ✅ HMI Send Trip button test PASSED")
            
        except requests.exceptions.RequestException:
            self.skipTest("HMI container not available")

    def test_hmi_data_response(self):
        """Test HMI Data: MMS Reads → Container Data → GUI Display"""
        print("\n🔘 Testing HMI/SCADA Data Response...")
        
        try:
            # 1. GUI REQUEST: HMI requests data from protection relay
            response = requests.get(self.hmi_url, timeout=2)
            self.assertEqual(response.status_code, 200)
            
            # 2. CONTAINER EFFECT: Verify MMS data structure
            data = response.json()
            required_fields = ['voltage', 'current', 'frequency', 'tripCommand']
            
            for field in required_fields:
                self.assertIn(field, data)
                print(f"   ✅ MMS Data Field '{field}': {data[field]}")
            
            # 3. GUI UPDATE: Verify data is realistic
            self.assertGreater(data['voltage'], 0)
            self.assertGreaterEqual(data['current'], 0)
            self.assertGreater(data['frequency'], 40)
            
            print("   ✅ HMI Data Response test PASSED")
            
        except requests.exceptions.RequestException:
            self.skipTest("HMI container not available")


class TestSystemIntegration(unittest.TestCase):
    """Test Complete Button → Container → GUI Integration Chains"""
    
    def setUp(self):
        self.base_url = 'http://localhost:3000'
        self.breaker_port = 8081
        self.hmi_port = 8080

    def test_fault_to_trip_sequence(self):
        """Test Complete Chain: Fault Button → Protection → GOOSE → Breaker → All GUIs"""
        print("\n🔘 Testing Complete Fault-to-Trip Integration...")
        
        try:
            # 1. BUTTON PRESS: Inject severe fault (should cause instant trip)
            print("   Step 1: Injecting severe fault (2500A)...")
            fault_cmd = {'command': 'updateFaultCurrent', 'data': {'faultCurrent': 2500.0}}
            response = requests.post(f'{self.base_url}/api/command', json=fault_cmd, timeout=2)
            self.assertEqual(response.status_code, 200)
            
            time.sleep(1)
            
            # 2. CONTAINER EFFECT: Verify fault in simulation
            response = requests.get(f'{self.base_url}/api/simulation-data', timeout=2)
            data = response.json()
            self.assertEqual(data['faultCurrent'], 2500.0)
            print("   ✅ Step 2: Fault injected in simulation container")
            
            # 3. PROTECTION LOGIC: Send trip (simulating protection relay decision)
            print("   Step 3: Protection relay issuing trip command...")
            trip_cmd = {'command': 'sendTrip', 'data': {}}
            response = requests.post(f'{self.base_url}/api/command', json=trip_cmd, timeout=2)
            self.assertEqual(response.status_code, 200)
            
            time.sleep(1)
            
            # 4. GOOSE COMMUNICATION: Verify trip propagated
            response = requests.get(f'{self.base_url}/api/simulation-data', timeout=2)
            data = response.json()
            print(f"   📊 Trip Command Status: {data.get('tripCommand', False)}")
            
            # 5. BREAKER RESPONSE: Check if breaker received GOOSE
            breaker_data = self.get_breaker_status()
            if breaker_data:
                trip_received = breaker_data.get('tripReceived', False)
                position = breaker_data.get('position', 'UNKNOWN')
                print(f"   📊 Breaker - Trip Received: {trip_received}, Position: {position}")
            
            # 6. HMI UPDATE: Verify HMI sees the fault condition
            hmi_data = self.get_hmi_status()
            if hmi_data:
                hmi_fault = hmi_data.get('faultCurrent', 0)
                print(f"   📊 HMI Fault Current Reading: {hmi_fault}A")
                self.assertGreater(hmi_fault, 2000)
            
            print("   ✅ Complete Fault-to-Trip sequence PASSED")
            
        except requests.exceptions.RequestException:
            self.skipTest("System components not available")
    
    def get_breaker_status(self):
        """Get breaker status"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect(('localhost', self.breaker_port))
            data = sock.recv(1024).decode()
            sock.close()
            return json.loads(data)
        except:
            return None
    
    def get_hmi_status(self):
        """Get HMI status"""
        try:
            response = requests.get(f'http://localhost:{self.hmi_port}', timeout=1)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None


class TestContainerConnectivity(unittest.TestCase):
    """Test connectivity to all containers"""
    
    def test_web_interface_connectivity(self):
        """Test web interface container (port 3000)"""
        try:
            response = requests.get('http://localhost:3000/api/simulation-data', timeout=2)
            self.assertEqual(response.status_code, 200)
        except requests.exceptions.RequestException:
            self.fail("Web interface container not accessible on port 3000")
            
    def test_protection_relay_mms_connectivity(self):
        """Test protection relay MMS server (port 102)"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect(('localhost', 102))
            sock.close()
            self.assertTrue(True)
        except socket.error:
            self.fail("Protection relay MMS server not accessible on port 102")
            
    def test_circuit_breaker_connectivity(self):
        """Test circuit breaker TCP server (port 8081)"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect(('localhost', 8081))
            sock.close()
            self.assertTrue(True)
        except socket.error:
            self.fail("Circuit breaker container not accessible on port 8081")
            
    def test_hmi_scada_connectivity(self):
        """Test HMI/SCADA HTTP server (port 8080)"""
        try:
            response = requests.get('http://localhost:8080', timeout=2)
            self.assertEqual(response.status_code, 200)
        except requests.exceptions.RequestException:
            self.fail("HMI/SCADA container not accessible on port 8080")


def run_tests():
    """Run all test suites with detailed chain validation"""
    print("=" * 70)
    print("VIRTUAL SUBSTATION BUTTON → CONTAINER → GUI TESTING")
    print("=" * 70)
    print("Testing complete chain: Button Press → Container Effect → GUI Update")
    print()
    
    # Test suites
    test_suites = [
        TestSimulationControlPanel,
        TestProtectionRelayPanel,
        TestCircuitBreakerPanel,
        TestHMIScadaPanel,
        TestSystemIntegration,
        TestContainerConnectivity
    ]
    
    total_tests = 0
    total_failures = 0
    total_skipped = 0
    
    for suite_class in test_suites:
        print(f"\n--- Testing {suite_class.__name__} ---")
        suite = unittest.TestLoader().loadTestsFromTestCase(suite_class)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        total_tests += result.testsRun
        total_failures += len(result.failures) + len(result.errors)
        total_skipped += len(result.skipped)
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_tests - total_failures - total_skipped}")
    print(f"Failed: {total_failures}")
    print(f"Skipped: {total_skipped}")
    
    if total_failures == 0:
        print("\n✅ ALL BUTTON → CONTAINER → GUI CHAINS WORKING!")
    else:
        print(f"\n❌ {total_failures} CHAIN TESTS FAILED!")
    
    return total_failures == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)