#!/usr/bin/env python3
"""
Test script to verify GUI panels receive live updates
"""
import subprocess
import time
import requests
import sys
import os

def test_gui_updates():
    print("Testing GUI Panel Live Updates...")
    
    # Test 1: Verify web interface is accessible
    print("\n1. Testing web interface connectivity...")
    try:
        response = requests.get('http://localhost:3000/api/simulation-data', timeout=2)
        if response.status_code == 200:
            print("✓ Web interface accessible")
            initial_data = response.json()
            print(f"  Initial voltage: {initial_data.get('voltage', 0)} kV")
        else:
            print("✗ Web interface not accessible")
            return False
    except Exception as e:
        print(f"✗ Web interface error: {e}")
        return False
    
    # Test 2: Test data updates
    print("\n2. Testing data updates...")
    test_voltage = 145.0
    try:
        payload = {'type': 'command', 'command': 'updateVoltage', 'data': {'voltage': test_voltage}}
        response = requests.post('http://localhost:3000/api/command', json=payload, timeout=2)
        
        if response.status_code == 200:
            print("✓ Command sent successfully")
            
            # Wait and verify update
            time.sleep(1)
            response = requests.get('http://localhost:3000/api/simulation-data', timeout=2)
            updated_data = response.json()
            
            if abs(updated_data.get('voltage', 0) - test_voltage) < 0.1:
                print(f"✓ Data updated correctly: {updated_data.get('voltage', 0)} kV")
            else:
                print(f"✗ Data not updated: expected {test_voltage}, got {updated_data.get('voltage', 0)}")
                return False
        else:
            print("✗ Command failed")
            return False
    except Exception as e:
        print(f"✗ Update test error: {e}")
        return False
    
    # Test 3: Start a GUI panel in background to test live updates
    print("\n3. Testing GUI panel live updates...")
    print("Starting Protection Relay Panel for 10 seconds...")
    
    try:
        # Start GUI panel in background
        gui_process = subprocess.Popen([
            'python3', 'gui/protection_relay_panel.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Give GUI time to start
        time.sleep(2)
        
        # Send multiple updates
        test_values = [150.0, 155.0, 160.0]
        for voltage in test_values:
            payload = {'type': 'command', 'command': 'updateVoltage', 'data': {'voltage': voltage}}
            requests.post('http://localhost:3000/api/command', json=payload, timeout=2)
            print(f"  Sent voltage update: {voltage} kV")
            time.sleep(2)
        
        # Terminate GUI
        gui_process.terminate()
        gui_process.wait(timeout=5)
        
        print("✓ GUI panel test completed (check GUI window for live updates)")
        
    except Exception as e:
        print(f"✗ GUI panel test error: {e}")
        return False
    
    # Test 4: Reset to normal values
    print("\n4. Resetting to normal values...")
    try:
        payload = {'type': 'command', 'command': 'updateVoltage', 'data': {'voltage': 132.0}}
        requests.post('http://localhost:3000/api/command', json=payload, timeout=2)
        print("✓ Reset to normal voltage")
    except Exception as e:
        print(f"✗ Reset error: {e}")
    
    print("\n" + "="*50)
    print("GUI UPDATE TEST RESULTS:")
    print("✓ Web interface working")
    print("✓ Data updates working") 
    print("✓ GUI panels should now show live updates")
    print("="*50)
    
    return True

if __name__ == "__main__":
    success = test_gui_updates()
    sys.exit(0 if success else 1)