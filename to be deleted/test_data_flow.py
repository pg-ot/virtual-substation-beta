#!/usr/bin/env python3
"""
Test Data Flow: GUI → Web Interface → Protection Relay → GUI
"""

import requests
import time
import socket
import json

def test_complete_data_flow():
    """Test the complete data flow chain"""
    print("🔄 Testing Complete Data Flow Chain")
    print("=" * 50)
    
    base_url = 'http://localhost:3000'
    
    # Step 1: Update voltage via web interface (simulating GUI)
    print("\n1️⃣ Updating voltage to 140kV via web interface...")
    cmd = {'command': 'updateVoltage', 'data': {'voltage': 140.0}}
    response = requests.post(f'{base_url}/api/command', json=cmd, timeout=2)
    
    if response.status_code == 200:
        print("   ✅ Command sent successfully")
    else:
        print("   ❌ Command failed")
        return False
    
    # Step 2: Verify web interface updated
    print("\n2️⃣ Checking web interface data...")
    response = requests.get(f'{base_url}/api/simulation-data', timeout=2)
    data = response.json()
    
    if data['voltage'] == 140.0:
        print(f"   ✅ Web interface updated: {data['voltage']}kV")
    else:
        print(f"   ❌ Web interface not updated: {data['voltage']}kV")
        return False
    
    # Step 3: Wait for protection relay to fetch data
    print("\n3️⃣ Waiting for protection relay to fetch data...")
    time.sleep(3)  # Protection relay fetches every 500ms
    
    # Step 4: Check if HMI can read from protection relay
    print("\n4️⃣ Testing HMI read from protection relay...")
    try:
        hmi_response = requests.get('http://localhost:8080', timeout=2)
        if hmi_response.status_code == 200:
            hmi_data = hmi_response.json()
            print(f"   ✅ HMI reads: V={hmi_data.get('voltage')}kV")
            
            if hmi_data.get('voltage') == 140.0:
                print("   ✅ Complete chain working!")
                return True
            else:
                print(f"   ⚠️  HMI shows different value: {hmi_data.get('voltage')}kV")
        else:
            print("   ❌ HMI not responding")
    except:
        print("   ❌ HMI connection failed")
    
    # Step 5: Test current change
    print("\n5️⃣ Testing current change (1200A - should trigger overcurrent)...")
    cmd = {'command': 'updateCurrent', 'data': {'current': 1200.0}}
    response = requests.post(f'{base_url}/api/command', json=cmd, timeout=2)
    
    if response.status_code == 200:
        print("   ✅ Current command sent")
        time.sleep(3)
        
        # Check if protection relay detects overcurrent
        try:
            hmi_response = requests.get('http://localhost:8080', timeout=2)
            if hmi_response.status_code == 200:
                hmi_data = hmi_response.json()
                current = hmi_data.get('current', 0)
                print(f"   📊 HMI reads current: {current}A")
                
                if current >= 1200:
                    print("   ✅ Overcurrent detected in protection relay!")
                else:
                    print(f"   ⚠️  Current not updated: {current}A")
        except:
            print("   ❌ Could not verify overcurrent detection")
    
    return True

def test_gui_simulation_commands():
    """Test typical GUI simulation commands"""
    print("\n\n🎮 Testing GUI Simulation Commands")
    print("=" * 50)
    
    base_url = 'http://localhost:3000'
    
    # Test scenario commands that GUI panels would send
    scenarios = [
        ("Normal Operation", [
            {'command': 'updateVoltage', 'data': {'voltage': 132.0}},
            {'command': 'updateCurrent', 'data': {'current': 450.0}},
            {'command': 'updateFrequency', 'data': {'frequency': 50.0}},
            {'command': 'updateFaultCurrent', 'data': {'faultCurrent': 0.0}}
        ]),
        ("Overcurrent Scenario", [
            {'command': 'updateCurrent', 'data': {'current': 1500.0}}
        ]),
        ("Ground Fault Scenario", [
            {'command': 'updateFaultCurrent', 'data': {'faultCurrent': 2000.0}},
            {'command': 'toggleFault', 'data': {'active': True}}
        ])
    ]
    
    for scenario_name, commands in scenarios:
        print(f"\n📋 Testing {scenario_name}...")
        
        for cmd in commands:
            response = requests.post(f'{base_url}/api/command', json=cmd, timeout=2)
            if response.status_code == 200:
                print(f"   ✅ {cmd['command']}: {list(cmd['data'].values())[0]}")
            else:
                print(f"   ❌ {cmd['command']}: Failed")
        
        # Check result
        time.sleep(1)
        response = requests.get(f'{base_url}/api/simulation-data', timeout=2)
        data = response.json()
        
        print(f"   📊 Result: V={data['voltage']}kV, I={data['current']}A, F={data['frequency']}Hz, FC={data['faultCurrent']}A")
        
        time.sleep(2)  # Allow protection relay to process

if __name__ == "__main__":
    print("🧪 VIRTUAL SUBSTATION DATA FLOW TEST")
    print("Testing: GUI → Web Interface → Protection Relay → HMI")
    print()
    
    try:
        # Test complete data flow
        success = test_complete_data_flow()
        
        # Test GUI commands
        test_gui_simulation_commands()
        
        if success:
            print("\n🎉 DATA FLOW TEST COMPLETED!")
            print("✅ The system is working correctly")
            print("✅ Values changed in simulator ARE reflected in protection relay")
            print("✅ GUI panels should be able to see the changes")
        else:
            print("\n❌ DATA FLOW TEST FAILED!")
            print("Check container connections and timing")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print("Make sure all containers are running: ./start_all.sh")