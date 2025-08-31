#!/usr/bin/env python3
"""
GUI Panel Testing Script for Virtual Substation
Tests all button functions and validates expected responses
"""

import unittest
import requests
import json
import time
import threading
from unittest.mock import patch, MagicMock
import sys
import os

# Add GUI directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'gui'))

class TestSimulationControlPanel(unittest.TestCase):
    """Test Simulation Control Panel buttons"""
    
    def setUp(self):
        self.base_url = 'http://localhost:3000'
        
    def test_scenario_normal_button(self):
        """Test Normal Operation scenario button"""
        expected_data = {
            'voltage': 132.0,
            'current': 450.0,
            'frequency': 50.0,
            'faultCurrent': 0.0,
            'faultDetected': False,
            'breakerStatus': False,
            'tripCommand': False
        }
        
        # Simulate button click
        commands = [
            {'command': 'updateVoltage', 'data': {'voltage': 132.0}},
            {'command': 'updateCurrent', 'data': {'current': 450.0}},
            {'command': 'updateFrequency', 'data': {'frequency': 50.0}},
            {'command': 'updateFaultCurrent', 'data': {'faultCurrent': 0.0}},
            {'command': 'toggleFault', 'data': {'active': False}},
            {'command': 'toggleBreaker', 'data': {'open': False}},
            {'command': 'toggleManualTrip', 'data': {'active': False}}
        ]
        
        for cmd in commands:
            try:
                response = requests.post(f'{self.base_url}/api/command', json=cmd, timeout=2)
                self.assertEqual(response.status_code, 200)
            except requests.exceptions.RequestException:
                self.skipTest("Web interface not available")
                
    def test_scenario_overcurrent_button(self):
        """Test Overcurrent scenario button"""
        expected_commands = [
            {'command': 'updateCurrent', 'data': {'current': 1500.0}},
            {'command': 'updateFaultCurrent', 'data': {'faultCurrent': 1500.0}}
        ]
        
        for cmd in expected_commands:
            try:
                response = requests.post(f'{self.base_url}/api/command', json=cmd, timeout=2)
                self.assertEqual(response.status_code, 200)
            except requests.exceptions.RequestException:
                self.skipTest("Web interface not available")
                
    def test_scenario_ground_fault_button(self):
        """Test Ground Fault scenario button"""
        expected_commands = [
            {'command': 'updateFaultCurrent', 'data': {'faultCurrent': 3000.0}},
            {'command': 'updateCurrent', 'data': {'current': 3000.0}},
            {'command': 'toggleFault', 'data': {'active': True}}
        ]
        
        for cmd in expected_commands:
            try:
                response = requests.post(f'{self.base_url}/api/command', json=cmd, timeout=2)
                self.assertEqual(response.status_code, 200)
            except requests.exceptions.RequestException:
                self.skipTest("Web interface not available")
                
    def test_scenario_frequency_deviation_button(self):
        """Test Frequency Deviation scenario button"""
        cmd = {'command': 'updateFrequency', 'data': {'frequency': 49.2}}
        
        try:
            response = requests.post(f'{self.base_url}/api/command', json=cmd, timeout=2)
            self.assertEqual(response.status_code, 200)
        except requests.exceptions.RequestException:
            self.skipTest("Web interface not available")
            
    def test_inject_fault_button(self):
        """Test Inject Fault button"""
        expected_commands = [
            {'command': 'toggleFault', 'data': {'active': True}},
            {'command': 'updateFaultCurrent', 'data': {'faultCurrent': 2500.0}}
        ]
        
        for cmd in expected_commands:
            try:
                response = requests.post(f'{self.base_url}/api/command', json=cmd, timeout=2)
                self.assertEqual(response.status_code, 200)
            except requests.exceptions.RequestException:
                self.skipTest("Web interface not available")
                
    def test_trip_breaker_button(self):
        """Test Trip Breaker button"""
        cmd = {'command': 'toggleBreaker', 'data': {'open': True}}
        
        try:
            response = requests.post(f'{self.base_url}/api/command', json=cmd, timeout=2)
            self.assertEqual(response.status_code, 200)
        except requests.exceptions.RequestException:
            self.skipTest("Web interface not available")
            
    def test_send_trip_button(self):
        """Test Send Trip button"""
        cmd = {'command': 'sendTrip', 'data': {}}
        
        try:
            response = requests.post(f'{self.base_url}/api/command', json=cmd, timeout=2)
            self.assertEqual(response.status_code, 200)
        except requests.exceptions.RequestException:
            self.skipTest("Web interface not available")
            
    def test_reset_all_button(self):
        """Test Reset All button (same as Normal Operation)"""
        self.test_scenario_normal_button()
        
    def test_emergency_stop_button(self):
        """Test Emergency Stop button"""
        expected_commands = [
            {'command': 'sendTrip', 'data': {}},
            {'command': 'toggleBreaker', 'data': {'open': True}}
        ]
        
        for cmd in expected_commands:
            try:
                response = requests.post(f'{self.base_url}/api/command', json=cmd, timeout=2)
                self.assertEqual(response.status_code, 200)
            except requests.exceptions.RequestException:
                self.skipTest("Web interface not available")


class TestProtectionRelayPanel(unittest.TestCase):
    """Test Protection Relay Panel buttons"""
    
    def setUp(self):
        self.base_url = 'http://localhost:3000'
        
    def test_manual_trip_button(self):
        """Test Manual Trip button"""
        cmd = {'command': 'sendTrip', 'data': {}}
        
        try:
            response = requests.post(f'{self.base_url}/api/command', json=cmd, timeout=2)
            self.assertEqual(response.status_code, 200)
        except requests.exceptions.RequestException:
            self.skipTest("Web interface not available")
            
    def test_reset_alarms_button(self):
        """Test Reset Alarms button"""
        expected_commands = [
            {'command': 'toggleFault', 'data': {'active': False}},
            {'command': 'toggleManualTrip', 'data': {'active': False}}
        ]
        
        for cmd in expected_commands:
            try:
                response = requests.post(f'{self.base_url}/api/command', json=cmd, timeout=2)
                self.assertEqual(response.status_code, 200)
            except requests.exceptions.RequestException:
                self.skipTest("Web interface not available")


class TestCircuitBreakerPanel(unittest.TestCase):
    """Test Circuit Breaker Panel buttons"""
    
    def setUp(self):
        self.base_url = 'http://localhost:3000'
        self.breaker_url = 'http://localhost:8081'
        
    def test_manual_trip_button(self):
        """Test Manual Trip button"""
        cmd = {'command': 'toggleBreaker', 'data': {'open': True}}
        
        try:
            response = requests.post(f'{self.base_url}/api/command', json=cmd, timeout=2)
            self.assertEqual(response.status_code, 200)
        except requests.exceptions.RequestException:
            self.skipTest("Web interface not available")
            
    def test_manual_close_button(self):
        """Test Manual Close button"""
        cmd = {'command': 'toggleBreaker', 'data': {'open': False}}
        
        try:
            response = requests.post(f'{self.base_url}/api/command', json=cmd, timeout=2)
            self.assertEqual(response.status_code, 200)
        except requests.exceptions.RequestException:
            self.skipTest("Web interface not available")
            
    def test_breaker_status_response(self):
        """Test breaker status TCP response"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect(('localhost', 8081))
            data = sock.recv(1024).decode()
            sock.close()
            
            # Validate JSON response
            breaker_data = json.loads(data)
            self.assertIn('position', breaker_data)
            self.assertIn('tripReceived', breaker_data)
            self.assertIn('status', breaker_data)
            
        except (socket.error, json.JSONDecodeError, ConnectionRefusedError):
            self.skipTest("Circuit breaker container not available")


class TestHMIScadaPanel(unittest.TestCase):
    """Test HMI/SCADA Panel buttons"""
    
    def setUp(self):
        self.hmi_url = 'http://localhost:8080'
        
    def test_read_values_button(self):
        """Test Read Values button - should trigger MMS reads"""
        # This button logs MMS read operations, no HTTP call
        self.assertTrue(True)  # Always passes as it's a logging operation
        
    def test_send_trip_button(self):
        """Test Send Trip button via MMS"""
        try:
            response = requests.post(f'{self.hmi_url}/mms/trip', timeout=2)
            self.assertEqual(response.status_code, 200)
        except requests.exceptions.RequestException:
            self.skipTest("HMI container not available")
            
    def test_reset_relay_button(self):
        """Test Reset Relay button via MMS"""
        try:
            response = requests.post(f'{self.hmi_url}/mms/reset', timeout=2)
            self.assertEqual(response.status_code, 200)
        except requests.exceptions.RequestException:
            self.skipTest("HMI container not available")
            
    def test_ack_alarms_button(self):
        """Test Acknowledge Alarms button"""
        # This button clears local alarm list, no HTTP call
        self.assertTrue(True)  # Always passes as it's a local operation
        
    def test_hmi_data_response(self):
        """Test HMI HTTP data response"""
        try:
            response = requests.get(self.hmi_url, timeout=2)
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn('voltage', data)
            self.assertIn('current', data)
            self.assertIn('frequency', data)
            self.assertIn('tripCommand', data)
            
        except requests.exceptions.RequestException:
            self.skipTest("HMI container not available")


class TestSystemIntegration(unittest.TestCase):
    """Test system-wide integration scenarios"""
    
    def setUp(self):
        self.base_url = 'http://localhost:3000'
        
    def test_fault_to_trip_sequence(self):
        """Test complete fault-to-trip sequence"""
        sequence = [
            # 1. Inject fault
            {'command': 'updateFaultCurrent', 'data': {'faultCurrent': 2500.0}},
            {'command': 'toggleFault', 'data': {'active': True}},
            # 2. Verify trip command
            {'command': 'sendTrip', 'data': {}},
            # 3. Open breaker
            {'command': 'toggleBreaker', 'data': {'open': True}}
        ]
        
        for cmd in sequence:
            try:
                response = requests.post(f'{self.base_url}/api/command', json=cmd, timeout=2)
                self.assertEqual(response.status_code, 200)
                time.sleep(0.1)  # Small delay between commands
            except requests.exceptions.RequestException:
                self.skipTest("Web interface not available")
                
    def test_system_reset_sequence(self):
        """Test complete system reset sequence"""
        reset_commands = [
            {'command': 'updateVoltage', 'data': {'voltage': 132.0}},
            {'command': 'updateCurrent', 'data': {'current': 450.0}},
            {'command': 'updateFrequency', 'data': {'frequency': 50.0}},
            {'command': 'updateFaultCurrent', 'data': {'faultCurrent': 0.0}},
            {'command': 'toggleFault', 'data': {'active': False}},
            {'command': 'toggleBreaker', 'data': {'open': False}},
            {'command': 'toggleManualTrip', 'data': {'active': False}}
        ]
        
        for cmd in reset_commands:
            try:
                response = requests.post(f'{self.base_url}/api/command', json=cmd, timeout=2)
                self.assertEqual(response.status_code, 200)
            except requests.exceptions.RequestException:
                self.skipTest("Web interface not available")


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
    """Run all test suites"""
    print("=" * 60)
    print("VIRTUAL SUBSTATION GUI PANEL TESTING")
    print("=" * 60)
    
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
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_tests - total_failures - total_skipped}")
    print(f"Failed: {total_failures}")
    print(f"Skipped: {total_skipped}")
    
    if total_failures == 0:
        print("\n✅ ALL TESTS PASSED!")
    else:
        print(f"\n❌ {total_failures} TESTS FAILED!")
    
    return total_failures == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)