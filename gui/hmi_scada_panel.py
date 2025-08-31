#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import requests
import threading
import time

class HMIScadaPanel:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HMI/SCADA - MMS Client")
        self.root.geometry("500x700")
        self.root.configure(bg='#2c2c2c')
        
        self.setup_ui()
        self.start_monitoring()
        
    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg='#1a1a1a', height=50)
        header.pack(fill='x', padx=5, pady=5)
        
        tk.Label(header, text="💻 HMI/SCADA SYSTEM", 
                fg='#00ff00', bg='#1a1a1a', font=('Courier', 14, 'bold')).pack(pady=10)
        
        # Connection Status
        conn_frame = tk.LabelFrame(self.root, text="MMS Connection", 
                                 fg='#00ff00', bg='#2c2c2c', font=('Courier', 10))
        conn_frame.pack(fill='x', padx=10, pady=5)
        
        self.conn_status_label = tk.Label(conn_frame, text="● CONNECTED", 
                                        fg='#00ff00', bg='#2c2c2c', font=('Courier', 10))
        self.conn_status_label.pack(pady=2)
        
        tk.Label(conn_frame, text="Server: protection_relay_ied:102", 
                fg='#ccc', bg='#2c2c2c', font=('Courier', 9)).pack(pady=1)
        
        tk.Label(conn_frame, text="Protocol: IEC 61850 MMS", 
                fg='#ccc', bg='#2c2c2c', font=('Courier', 9)).pack(pady=1)
        
        # Real-time Data
        data_frame = tk.LabelFrame(self.root, text="Real-time Measurements", 
                                 fg='#00ff00', bg='#2c2c2c', font=('Courier', 10))
        data_frame.pack(fill='x', padx=10, pady=5)
        
        # Create measurement displays
        meas_grid = tk.Frame(data_frame, bg='#2c2c2c')
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
        
        # Power
        tk.Label(meas_grid, text="Active Power:", fg='#ccc', bg='#2c2c2c', 
                font=('Courier', 9)).grid(row=3, column=0, sticky='w', padx=5)
        self.power_label = tk.Label(meas_grid, text="59.4 MW", fg='#00ff00', bg='#2c2c2c', 
                                  font=('Courier', 10, 'bold'))
        self.power_label.grid(row=3, column=1, sticky='w', padx=10)
        
        # Alarms Frame
        alarm_frame = tk.LabelFrame(self.root, text="System Alarms", 
                                  fg='#00ff00', bg='#2c2c2c', font=('Courier', 10))
        alarm_frame.pack(fill='x', padx=10, pady=5)
        
        self.alarm_listbox = tk.Listbox(alarm_frame, bg='#1a1a1a', fg='#ff0000', 
                                      font=('Courier', 9), height=4)
        self.alarm_listbox.pack(fill='x', padx=5, pady=5)
        
        # Control Commands
        control_frame = tk.LabelFrame(self.root, text="Remote Control", 
                                    fg='#00ff00', bg='#2c2c2c', font=('Courier', 10))
        control_frame.pack(fill='x', padx=10, pady=5)
        
        cmd_grid = tk.Frame(control_frame, bg='#2c2c2c')
        cmd_grid.pack(pady=5)
        
        tk.Button(cmd_grid, text="READ VALUES", bg='#404040', fg='#00ff00',
                 font=('Courier', 9), command=self.read_values).grid(row=0, column=0, padx=5, pady=2)
        
        tk.Button(cmd_grid, text="SEND TRIP", bg='#ff0000', fg='white',
                 font=('Courier', 9), command=self.send_trip).grid(row=0, column=1, padx=5, pady=2)
        
        tk.Button(cmd_grid, text="RESET RELAY", bg='#404040', fg='#00ff00',
                 font=('Courier', 9), command=self.reset_relay).grid(row=1, column=0, padx=5, pady=2)
        
        tk.Button(cmd_grid, text="ACK ALARMS", bg='#ff8800', fg='white',
                 font=('Courier', 9), command=self.ack_alarms).grid(row=1, column=1, padx=5, pady=2)
        
        tk.Button(cmd_grid, text="TEST TRIP", bg='#ffaa00', fg='white',
                 font=('Courier', 9, 'bold'), command=self.test_trip).grid(row=2, column=0, padx=5, pady=2)
        
        # MMS Data Log
        log_frame = tk.LabelFrame(self.root, text="MMS Communication Log", 
                                fg='#00ff00', bg='#2c2c2c', font=('Courier', 10))
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, bg='#1a1a1a', fg='#00ff00', 
                              font=('Courier', 8), height=12)
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Status Bar
        status_bar = tk.Frame(self.root, bg='#1a1a1a', height=25)
        status_bar.pack(fill='x', side='bottom')
        
        self.status_text = tk.Label(status_bar, text="MMS Client Ready", 
                                  fg='#00ff00', bg='#1a1a1a', font=('Courier', 9))
        self.status_text.pack(side='left', padx=10, pady=2)
        
        self.time_label = tk.Label(status_bar, text="", 
                                 fg='#ffff00', bg='#1a1a1a', font=('Courier', 9))
        self.time_label.pack(side='right', padx=10, pady=2)
        
    def read_values(self):
        self.log_message("MMS READ: GenericIO/GGIO1.AnIn1.mag.f")
        self.log_message("MMS READ: GenericIO/GGIO1.AnIn2.mag.f")
        self.log_message("MMS READ: GenericIO/GGIO1.AnIn3.mag.f")
        
    def send_trip(self):
        # Send MMS control command to protection relay
        try:
            response = requests.post('http://localhost:8080/trip', timeout=2)
            if response.status_code == 200:
                self.log_message("MMS CONTROL: GenericIO/GGIO1.SPCSO1.Oper.ctlVal = TRUE")
                self.log_message("MMS TRIP: Command sent via IEC 61850 MMS")
            else:
                self.log_message("MMS CONTROL FAILED: Trip command")
        except:
            self.log_message("MMS CONNECTION ERROR: HMI/SCADA server unavailable")
        
    def reset_relay(self):
        # Send reset commands via web interface
        try:
            payload1 = {'type': 'command', 'command': 'toggleFault', 'data': {'active': False}}
            payload2 = {'type': 'command', 'command': 'toggleManualTrip', 'data': {'active': False}}
            requests.post('http://localhost:3000/api/command', json=payload1, timeout=2)
            requests.post('http://localhost:3000/api/command', json=payload2, timeout=2)
            self.log_message("MMS WRITE: Reset command sent")
        except:
            self.log_message("MMS CONNECTION ERROR: Cannot send reset")
        
    def ack_alarms(self):
        self.alarm_listbox.delete(0, tk.END)
        self.log_message("All alarms acknowledged")
        
    def send_command(self, command, data):
        # Legacy fallback for non-MMS commands
        try:
            payload = {'type': 'command', 'command': command, 'data': data}
            requests.post('http://localhost:3000/api/command', 
                         json=payload, timeout=1)
        except:
            pass
            
    def log_message(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def test_trip(self):
        try:
            # Test MMS connection via HMI server
            response = requests.get('http://localhost:8080', timeout=2)
            if response.status_code == 200:
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(tk.END, f"MMS TEST: HMI/SCADA MMS Client\n\nHTTP Status: {response.status_code}\nMMS Server: protection_relay_ied:102\nTest: SUCCESS\n\nMMS control ready.\n")
            else:
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(tk.END, f"MMS TEST: Connection Failed\n\nHTTP Status: {response.status_code}\nTest: FAILED\n")
        except Exception as e:
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, f"MMS TEST: Connection Failed\n\nError: {str(e)}\nMMS Server: protection_relay_ied:102\nTest: FAILED\n")
        
    def start_monitoring(self):
        def monitor():
            while True:
                try:
                    response = requests.get('http://localhost:8080', timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        self.update_display(data)
                        self.conn_status_label.config(text="● CONNECTED", fg='#00ff00')
                        self.status_text.config(text="MMS Client Active")
                except:
                    self.conn_status_label.config(text="● DISCONNECTED", fg='#ff0000')
                    self.status_text.config(text="MMS Connection Lost")
                    
                # Update time
                self.time_label.config(text=time.strftime("%Y-%m-%d %H:%M:%S"))
                time.sleep(2)
                
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        
    def update_display(self, data):
        # Update measurements
        voltage = data.get('voltage', 0)
        current = data.get('current', 0)
        frequency = data.get('frequency', 0)
        
        self.voltage_label.config(text=f"{voltage:.1f} kV")
        self.current_label.config(text=f"{current:.0f} A")
        self.frequency_label.config(text=f"{frequency:.3f} Hz")
        
        # Calculate power
        power = voltage * current * 1.732 / 1000  # 3-phase power in MW
        self.power_label.config(text=f"{power:.1f} MW")
        
        # Check for alarms
        fault_detected = data.get('faultDetected', False)
        trip_command = data.get('tripCommand', False)
        
        if fault_detected and not hasattr(self, 'fault_alarm_added'):
            self.alarm_listbox.insert(tk.END, f"{time.strftime('%H:%M:%S')} - FAULT DETECTED")
            self.fault_alarm_added = True
            self.log_message("ALARM: Fault detected in protection zone")
        elif not fault_detected:
            self.fault_alarm_added = False
            
        if trip_command and not hasattr(self, 'trip_alarm_added'):
            self.alarm_listbox.insert(tk.END, f"{time.strftime('%H:%M:%S')} - TRIP COMMAND ISSUED")
            self.trip_alarm_added = True
            self.log_message("EVENT: Trip command issued by protection relay")
        elif not trip_command:
            self.trip_alarm_added = False
            
        # Color coding for measurements
        if fault_detected:
            self.current_label.config(fg='#ff0000')
        elif current > 1000:
            self.current_label.config(fg='#ffff00')
        else:
            self.current_label.config(fg='#00ff00')
            
        if frequency < 49.8 or frequency > 50.2:
            self.frequency_label.config(fg='#ffff00')
        else:
            self.frequency_label.config(fg='#00ff00')
            
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = HMIScadaPanel()
    app.run()