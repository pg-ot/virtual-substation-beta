#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import requests
import json
import threading
import time

class ProtectionRelayPanel:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Protection Relay IED - PROT_REL_001")
        self.root.geometry("400x600")
        self.root.configure(bg='#2c2c2c')
        
        # No control variables - read-only display
        
        self.setup_ui()
        self.start_monitoring()
        
    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg='#1a1a1a', height=50)
        header.pack(fill='x', padx=5, pady=5)
        
        tk.Label(header, text="🛡️ PROTECTION RELAY IED", 
                fg='#00ff00', bg='#1a1a1a', font=('Courier', 14, 'bold')).pack(pady=10)
        
        # Status Frame
        status_frame = tk.LabelFrame(self.root, text="System Status", 
                                   fg='#00ff00', bg='#2c2c2c', font=('Courier', 10))
        status_frame.pack(fill='x', padx=10, pady=5)

        self.status_label = tk.Label(status_frame, text="● ONLINE", 
                                   fg='#00ff00', bg='#2c2c2c', font=('Courier', 10))
        self.status_label.pack(pady=5)

        # Comms LEDs and controls
        comms_frame = tk.Frame(status_frame, bg='#2c2c2c')
        comms_frame.pack(fill='x', padx=5, pady=5)

        tk.Label(comms_frame, text="GOOSE TX:", fg='#ccc', bg='#2c2c2c',
                 font=('Courier', 9)).grid(row=0, column=0, sticky='w')
        self.goose_tx_led = tk.Label(comms_frame, text="--", fg='#ff0000', bg='#2c2c2c',
                                     font=('Courier', 10, 'bold'))
        self.goose_tx_led.grid(row=0, column=1, sticky='w', padx=6)

        tk.Label(comms_frame, text="RX:", fg='#ccc', bg='#2c2c2c',
                 font=('Courier', 9)).grid(row=0, column=2, sticky='w')
        self.goose_rx_led = tk.Label(comms_frame, text="--", fg='#ff0000', bg='#2c2c2c',
                                     font=('Courier', 10, 'bold'))
        self.goose_rx_led.grid(row=0, column=3, sticky='w', padx=6)

        self.reset_btn = tk.Button(comms_frame, text="RESET LATCH", bg='#444', fg='white',
                                   font=('Courier', 9, 'bold'), command=self.reset_latch)
        self.reset_btn.grid(row=0, column=4, padx=10)
        
        # Measurements Frame
        meas_frame = tk.LabelFrame(self.root, text="Sampled Values (SV)", 
                                 fg='#00ff00', bg='#2c2c2c', font=('Courier', 10))
        meas_frame.pack(fill='x', padx=10, pady=5)
        
        # Create measurement displays
        meas_grid = tk.Frame(meas_frame, bg='#2c2c2c')
        meas_grid.pack(pady=5)
        
        # Voltage
        tk.Label(meas_grid, text="Voltage L1:", fg='#ccc', bg='#2c2c2c', 
                font=('Courier', 9)).grid(row=0, column=0, sticky='w', padx=5)
        self.voltage_label = tk.Label(meas_grid, text="132.0 kV", fg='#00ff00', bg='#2c2c2c', 
                                    font=('Courier', 10, 'bold'))
        self.voltage_label.grid(row=0, column=1, sticky='w', padx=10)
        
        # Current
        tk.Label(meas_grid, text="Current L1:", fg='#ccc', bg='#2c2c2c', 
                font=('Courier', 9)).grid(row=1, column=0, sticky='w', padx=5)
        self.current_label = tk.Label(meas_grid, text="450 A", fg='#00ff00', bg='#2c2c2c', 
                                    font=('Courier', 10, 'bold'))
        self.current_label.grid(row=1, column=1, sticky='w', padx=10)
        
        # Frequency
        tk.Label(meas_grid, text="Frequency:", fg='#ccc', bg='#2c2c2c', 
                font=('Courier', 9)).grid(row=2, column=0, sticky='w', padx=5)
        self.frequency_label = tk.Label(meas_grid, text="50.00 Hz", fg='#00ff00', bg='#2c2c2c', 
                                      font=('Courier', 10, 'bold'))
        self.frequency_label.grid(row=2, column=1, sticky='w', padx=10)
        
        # Fault Current
        tk.Label(meas_grid, text="Fault Current:", fg='#ccc', bg='#2c2c2c', 
                font=('Courier', 9)).grid(row=3, column=0, sticky='w', padx=5)
        self.fault_current_label = tk.Label(meas_grid, text="0 A", fg='#00ff00', bg='#2c2c2c', 
                                          font=('Courier', 10, 'bold'))
        self.fault_current_label.grid(row=3, column=1, sticky='w', padx=10)
        
        # Protection Elements Frame
        prot_frame = tk.LabelFrame(self.root, text="Protection Elements", 
                                 fg='#00ff00', bg='#2c2c2c', font=('Courier', 10))
        prot_frame.pack(fill='x', padx=10, pady=5)
        
        prot_grid = tk.Frame(prot_frame, bg='#2c2c2c')
        prot_grid.pack(pady=5)
        
        # Overcurrent Element (50/51)
        tk.Label(prot_grid, text="Overcurrent (50/51):", fg='#ccc', bg='#2c2c2c', 
                font=('Courier', 9)).grid(row=0, column=0, sticky='w', padx=5)
        self.oc_status_label = tk.Label(prot_grid, text="NORMAL", fg='#00ff00', bg='#2c2c2c', 
                                      font=('Courier', 9, 'bold'))
        self.oc_status_label.grid(row=0, column=1, sticky='w', padx=10)
        
        # Ground Fault Element (50G/51G)
        tk.Label(prot_grid, text="Ground Fault (50G/51G):", fg='#ccc', bg='#2c2c2c', 
                font=('Courier', 9)).grid(row=1, column=0, sticky='w', padx=5)
        self.gf_status_label = tk.Label(prot_grid, text="NORMAL", fg='#00ff00', bg='#2c2c2c', 
                                      font=('Courier', 9, 'bold'))
        self.gf_status_label.grid(row=1, column=1, sticky='w', padx=10)
        
        # Frequency Element (81U)
        tk.Label(prot_grid, text="Frequency (81U):", fg='#ccc', bg='#2c2c2c', 
                font=('Courier', 9)).grid(row=2, column=0, sticky='w', padx=5)
        self.freq_status_label = tk.Label(prot_grid, text="NORMAL", fg='#00ff00', bg='#2c2c2c', 
                                        font=('Courier', 9, 'bold'))
        self.freq_status_label.grid(row=2, column=1, sticky='w', padx=10)
        
        # Trip Command
        tk.Label(prot_grid, text="Trip Command:", fg='#ccc', bg='#2c2c2c', 
                font=('Courier', 9)).grid(row=3, column=0, sticky='w', padx=5)
        self.trip_status_label = tk.Label(prot_grid, text="NO", fg='#00ff00', bg='#2c2c2c', 
                                        font=('Courier', 9, 'bold'))
        self.trip_status_label.grid(row=3, column=1, sticky='w', padx=10)
        
        # Breaker Position
        tk.Label(prot_grid, text="Breaker Position:", fg='#ccc', bg='#2c2c2c', 
                font=('Courier', 9)).grid(row=4, column=0, sticky='w', padx=5)
        self.breaker_status_label = tk.Label(prot_grid, text="CLOSED", fg='#00ff00', bg='#2c2c2c', 
                                           font=('Courier', 9, 'bold'))
        self.breaker_status_label.grid(row=4, column=1, sticky='w', padx=10)
        
        # Control Buttons
        control_frame = tk.Frame(self.root, bg='#2c2c2c')
        control_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Button(control_frame, text="MANUAL TRIP", bg='#ff0000', fg='white',
                 font=('Courier', 10, 'bold'), command=self.send_trip).pack(side='left', padx=5)
        
        tk.Button(control_frame, text="RESET TRIP", bg='#0066cc', fg='white',
                 font=('Courier', 10, 'bold'), command=self.reset_trip).pack(side='left', padx=5)
        
        tk.Button(control_frame, text="RESET ALARMS", bg='#404040', fg='#00ff00',
                 font=('Courier', 10), command=self.reset_relay).pack(side='left', padx=5)
        
        tk.Button(control_frame, text="DEBUG", bg='#ffaa00', fg='white',
                 font=('Courier', 10, 'bold'), command=self.debug_test).pack(side='left', padx=5)
        
        # Live Data Display
        data_frame = tk.LabelFrame(self.root, text="Live IEC 61850 Data", 
                                 fg='#00ff00', bg='#2c2c2c', font=('Courier', 10))
        data_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.data_text = tk.Text(data_frame, bg='#1a1a1a', fg='#00ff00', 
                               font=('Courier', 9), height=8)
        self.data_text.pack(fill='both', expand=True, padx=5, pady=5)
        
    def send_trip(self):
        """Sends a direct HTTP POST request to the Protection Relay to trip."""
        try:
            requests.post('http://localhost:8082/trip', timeout=2)
            print("GUI: Manual Trip command sent to Protection Relay.")
        except Exception as e:
            print(f"GUI: Failed to send trip command: {e}")

    def reset_trip(self):
        try:
            r = requests.post('http://localhost:8082/reset', timeout=2)
            if r.status_code == 200:
                self.log_text.insert(1.0, "RESET: Trip reset command sent to relay\n")
            else:
                self.log_text.insert(1.0, f"RESET FAILED: HTTP {r.status_code}\n")
        except Exception as e:
            self.log_text.insert(1.0, f"RESET ERROR: {str(e)}\n")

    def reset_relay(self):
        # Alias to same /reset for now
        try:
            r = requests.post('http://localhost:8082/reset', timeout=2)
            if r.status_code == 200:
                self.log_text.insert(1.0, "ALARM RESET: Command sent to relay\n")
            else:
                self.log_text.insert(1.0, f"ALARM RESET FAILED: HTTP {r.status_code}\n")
        except Exception as e:
            self.log_text.insert(1.0, f"ALARM RESET ERROR: {str(e)}\n")
    
    def debug_test(self):
        try:
            response = requests.get('http://localhost:8082', timeout=2)
            if response.status_code == 200:
                data = response.json()
                self.data_text.delete(1.0, tk.END)
                self.data_text.insert(1.0, f"DEBUG: Protection Relay Communication Test\n\nHTTP Status: {response.status_code}\nResponse: {json.dumps(data, indent=2)}\n\nTest: SUCCESS")
            else:
                self.data_text.delete(1.0, tk.END)
                self.data_text.insert(1.0, f"DEBUG: Communication Test\n\nHTTP Status: {response.status_code}\nTest: FAILED")
        except Exception as e:
            self.data_text.delete(1.0, tk.END)
            self.data_text.insert(1.0, f"DEBUG: Communication Test\n\nError: {str(e)}\nTest: FAILED")
            
    def start_monitoring(self):
        def monitor():
            while True:
                try:
                    response = requests.get('http://localhost:8082', timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        self.update_display(data)
                        self.status_label.config(text="● RELAY ONLINE", fg='#00ff00')
                except:
                    self.status_label.config(text="● OFFLINE", fg='#ff0000')
                # Update TX (breaker sees relay GOOSE) from HMI diagnostics
                try:
                    s = requests.get('http://localhost:8082', timeout=2)
                    if s.status_code == 200:
                        st = s.json()
                        # TX/RX purely from local relay endpoint (front-panel behavior)
                        tx_ok = bool(st.get('txOk', False))
                        rx_ok = bool(st.get('rxOk', False))
                        self.goose_tx_led.config(text=("OK" if tx_ok else "TIMEOUT"),
                                                 fg=('#00ff00' if tx_ok else '#ff0000'))
                        self.goose_rx_led.config(text=("OK" if rx_ok else "TIMEOUT"),
                                                 fg=('#00ff00' if rx_ok else '#ff0000'))
                except:
                    self.goose_tx_led.config(text="TIMEOUT", fg='#ff0000')
                    self.goose_rx_led.config(text="TIMEOUT", fg='#ff0000')

                time.sleep(1)
                
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        
    def update_display(self, data):
        # Update measurement displays
        voltage = data.get('voltage', 0)
        current = data.get('current', 0)
        frequency = data.get('frequency', 0)
        fault_current = data.get('faultCurrent', 0)
        
        self.voltage_label.config(text=f"{voltage:.1f} kV")
        self.current_label.config(text=f"{current:.0f} A")
        self.frequency_label.config(text=f"{frequency:.3f} Hz")
        self.fault_current_label.config(text=f"{fault_current:.0f} A")
        
        # Color fault current based on level
        if fault_current >= 800:
            self.fault_current_label.config(fg='#ff0000')
        elif fault_current >= 300:
            self.fault_current_label.config(fg='#ffff00')
        else:
            self.fault_current_label.config(fg='#00ff00')
        
        # Update protection element status
        overcurrent = current > 1000
        fault_detected = data.get('faultDetected', False)
        trip_command = data.get('tripCommand', False)
        breaker_open = data.get('breakerStatus', False)
        
        # Overcurrent Protection (50/51)
        if current >= 2500:
            self.oc_status_label.config(text="50-INST TRIP", fg='#ff0000')
            self.current_label.config(fg='#ff0000')
        elif current >= 1000:
            self.oc_status_label.config(text="51-PICKUP", fg='#ffff00')
            self.current_label.config(fg='#ffff00')
        else:
            self.oc_status_label.config(text="NORMAL", fg='#00ff00')
            self.current_label.config(fg='#00ff00')
            
        # Ground Fault Protection (50G/51G)
        if fault_current >= 800:
            self.gf_status_label.config(text="50G-INST TRIP", fg='#ff0000')
        elif fault_current >= 300:
            self.gf_status_label.config(text="51G-PICKUP", fg='#ffff00')
        else:
            self.gf_status_label.config(text="NORMAL", fg='#00ff00')
            
        # Frequency Protection (81U)
        if frequency < 48.5:
            self.freq_status_label.config(text="81U-TRIP", fg='#ff0000')
            self.frequency_label.config(fg='#ff0000')
        elif frequency < 49.0:
            self.freq_status_label.config(text="81U-ALARM", fg='#ffff00')
            self.frequency_label.config(fg='#ffff00')
        else:
            self.freq_status_label.config(text="NORMAL", fg='#00ff00')
            self.frequency_label.config(fg='#00ff00')
            
        # Trip command
        if trip_command:
            self.trip_status_label.config(text="ACTIVE", fg='#ff0000')
        else:
            self.trip_status_label.config(text="NO", fg='#00ff00')
            
        # Breaker position
        if breaker_open:
            self.breaker_status_label.config(text="OPEN", fg='#ff8800')
        else:
            self.breaker_status_label.config(text="CLOSED", fg='#00ff00')
            
        # Determine trip reason based on conditions
        trip_reason = "Normal"
        if trip_command:
            if fault_current >= 800:
                trip_reason = "50G-Instantaneous GF"
            elif fault_current >= 300:
                trip_reason = "51G-Time GF"
            elif current >= 2500:
                trip_reason = "50-Instantaneous O/C"
            elif current >= 1000:
                trip_reason = "51-Time O/C"
            elif frequency < 48.5:
                trip_reason = "81U-Underfrequency"
            else:
                trip_reason = "Manual Trip"
                
        # Update IEC 61850 data display
        display_text = f"""IEC 61850 Data Points:
        
AnIn1 (Voltage): {voltage:.1f} kV
AnIn2 (Current): {current:.0f} A  
AnIn3 (Frequency): {frequency:.3f} Hz
AnIn4 (Fault I): {fault_current:.0f} A

SPCSO1 (Trip): {trip_command}
SPCSO2 (CB Pos): {breaker_open}
SPCSO3 (Fault): {fault_detected}
SPCSO4 (Overcur): {overcurrent}

Trip Reason: {trip_reason}
MMS Server: Port 102
GOOSE Publisher: Active
Dataset: Events (8 values)
"""
        self.data_text.delete(1.0, tk.END)
        self.data_text.insert(1.0, display_text)

    def reset_latch(self):
        # Hit HMI reset to clear latches and demonstrate reset path
        try:
            r = requests.post('http://localhost:8080/reset', timeout=2)
            if r.status_code == 200:
                self.status_label.config(text="● RESET SENT", fg='#00ff00')
            else:
                self.status_label.config(text="● RESET FAILED", fg='#ff0000')
        except Exception:
            self.status_label.config(text="● RESET ERROR", fg='#ff0000')
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ProtectionRelayPanel()
    app.run()
