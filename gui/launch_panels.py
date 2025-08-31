#!/usr/bin/env python3
import subprocess
import sys
import os

def launch_panel(script_name):
    """Launch a panel script in a new process"""
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    subprocess.Popen([sys.executable, script_path])

def main():
    print("Launching IED Panels...")
    
    # Launch all three panels
    launch_panel("protection_relay_panel.py")
    launch_panel("circuit_breaker_panel.py") 
    launch_panel("hmi_scada_panel.py")
    
    print("All panels launched!")
    print("Close this window to keep panels running.")
    
    # Keep the launcher running
    try:
        input("Press Enter to exit...")
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()