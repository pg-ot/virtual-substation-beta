#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import requests
import json
import threading
import time

class SimulationControlPanel:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Simulation Control Panel")
        self.root.geometry("450x650")
        self.root.configure(bg='#1a1a1a')
        
        # Variables
        self.voltage = tk.DoubleVar(value=132.0)
        self.current = tk.DoubleVar(value=450.0)
        self.frequency = tk.DoubleVar(value=50.0)
        self.fault_current = tk.DoubleVar(value=0.0)
        self.fault_active = tk.BooleanVar(value=False)
        
        self.setup_ui()
        self.start_monitoring()
        
    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg='#0d47a1', height=60)
        header.pack(fill='x', padx=5, pady=5)
        
        tk.Label(header, text="⚡ SIMULATION CONTROL CENTER", 
                fg='white', bg='#0d47a1', font=('Arial', 16, 'bold')).pack(pady=15)
        
        # Connection Status
        status_frame = tk.Frame(self.root, bg='#1a1a1a')
        status_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(status_frame, text="Connection Status:", 
                fg='#ccc', bg='#1a1a1a', font=('Arial', 10)).pack(side='left')
        
        self.status_indicator = tk.Label(status_frame, text="● CONNECTED", 
                                       fg='#4caf50', bg='#1a1a1a', font=('Arial', 10, 'bold'))
        self.status_indicator.pack(side='left', padx=10)
        
        # Analog Controls
        analog_frame = tk.LabelFrame(self.root, text="Analog Measurements", 
                                   fg='#2196f3', bg='#1a1a1a', font=('Arial', 12, 'bold'))
        analog_frame.pack(fill='x', padx=10, pady=10)
        
        # Voltage Control
        voltage_frame = tk.Frame(analog_frame, bg='#1a1a1a')
        voltage_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(voltage_frame, text="Voltage L1 (kV):", 
                fg='white', bg='#1a1a1a', font=('Arial', 10)).pack(side='left')
        
        self.voltage_scale = tk.Scale(voltage_frame, from_=110, to=150, resolution=0.1, 
                                    orient='horizontal', variable=self.voltage,
                                    bg='#333', fg='#2196f3', highlightbackground='#1a1a1a',
                                    command=self.update_voltage, length=200)
        self.voltage_scale.pack(side='right', padx=10)
        
        self.voltage_entry = tk.Entry(voltage_frame, textvariable=self.voltage, 
                                    width=8, bg='#333', fg='white', insertbackground='white')
        self.voltage_entry.pack(side='right', padx=5)
        self.voltage_entry.bind('<Return>', lambda e: self.update_voltage(self.voltage.get()))
        
        # Current Control
        current_frame = tk.Frame(analog_frame, bg='#1a1a1a')
        current_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(current_frame, text="Current L1 (A):", 
                fg='white', bg='#1a1a1a', font=('Arial', 10)).pack(side='left')
        
        self.current_scale = tk.Scale(current_frame, from_=0, to=3000, resolution=10, 
                                    orient='horizontal', variable=self.current,
                                    bg='#333', fg='#ff9800', highlightbackground='#1a1a1a',
                                    command=self.update_current, length=200)
        self.current_scale.pack(side='right', padx=10)
        
        self.current_entry = tk.Entry(current_frame, textvariable=self.current, 
                                    width=8, bg='#333', fg='white', insertbackground='white')
        self.current_entry.pack(side='right', padx=5)
        self.current_entry.bind('<Return>', lambda e: self.update_current(self.current.get()))
        
        # Frequency Control
        freq_frame = tk.Frame(analog_frame, bg='#1a1a1a')
        freq_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(freq_frame, text="Frequency (Hz):", 
                fg='white', bg='#1a1a1a', font=('Arial', 10)).pack(side='left')
        
        self.freq_scale = tk.Scale(freq_frame, from_=47.0, to=52.0, resolution=0.01, 
                                 orient='horizontal', variable=self.frequency,
                                 bg='#333', fg='#4caf50', highlightbackground='#1a1a1a',
                                 command=self.update_frequency, length=200)
        self.freq_scale.pack(side='right', padx=10)
        
        self.freq_entry = tk.Entry(freq_frame, textvariable=self.frequency, 
                                 width=8, bg='#333', fg='white', insertbackground='white')
        self.freq_entry.pack(side='right', padx=5)
        self.freq_entry.bind('<Return>', lambda e: self.update_frequency(self.frequency.get()))
        
        # Fault Current Control
        fault_frame = tk.Frame(analog_frame, bg='#1a1a1a')
        fault_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(fault_frame, text="Fault Current (A):", 
                fg='white', bg='#1a1a1a', font=('Arial', 10)).pack(side='left')
        
        self.fault_scale = tk.Scale(fault_frame, from_=0, to=5000, resolution=100, 
                                  orient='horizontal', variable=self.fault_current,
                                  bg='#333', fg='#f44336', highlightbackground='#1a1a1a',
                                  command=self.update_fault_current, length=200)
        self.fault_scale.pack(side='right', padx=10)
        
        self.fault_entry = tk.Entry(fault_frame, textvariable=self.fault_current, 
                                  width=8, bg='#333', fg='white', insertbackground='white')
        self.fault_entry.pack(side='right', padx=5)
        self.fault_entry.bind('<Return>', lambda e: self.update_fault_current(self.fault_current.get()))
        
        # Digital Controls
        digital_frame = tk.LabelFrame(self.root, text="Digital Signals & Events", 
                                    fg='#ff9800', bg='#1a1a1a', font=('Arial', 12, 'bold'))
        digital_frame.pack(fill='x', padx=10, pady=10)
        
        # Fault Simulation
        fault_control = tk.Frame(digital_frame, bg='#1a1a1a')
        fault_control.pack(fill='x', padx=10, pady=5)
        
        tk.Checkbutton(fault_control, text="Fault Detected", variable=self.fault_active,
                      fg='#f44336', bg='#1a1a1a', selectcolor='#333', 
                      font=('Arial', 10, 'bold'), command=self.toggle_fault).pack(side='left')
        
        tk.Button(fault_control, text="INJECT FAULT", bg='#f44336', fg='white',
                 font=('Arial', 9, 'bold'), command=self.inject_fault).pack(side='right', padx=5)
        

        
        # Scenario Buttons
        scenario_frame = tk.LabelFrame(self.root, text="Simulation Scenarios", 
                                     fg='#9c27b0', bg='#1a1a1a', font=('Arial', 12, 'bold'))
        scenario_frame.pack(fill='x', padx=10, pady=10)
        
        scenario_grid = tk.Frame(scenario_frame, bg='#1a1a1a')
        scenario_grid.pack(pady=10)
        
        tk.Button(scenario_grid, text="Normal Operation", bg='#4caf50', fg='white',
                 font=('Arial', 10), width=15, command=self.scenario_normal).grid(row=0, column=0, padx=5, pady=2)
        
        tk.Button(scenario_grid, text="Overcurrent", bg='#ff9800', fg='white',
                 font=('Arial', 10), width=15, command=self.scenario_overcurrent).grid(row=0, column=1, padx=5, pady=2)
        
        tk.Button(scenario_grid, text="Ground Fault", bg='#f44336', fg='white',
                 font=('Arial', 10), width=15, command=self.scenario_ground_fault).grid(row=1, column=0, padx=5, pady=2)
        
        tk.Button(scenario_grid, text="Frequency Deviation", bg='#3f51b5', fg='white',
                 font=('Arial', 10), width=15, command=self.scenario_freq_dev).grid(row=1, column=1, padx=5, pady=2)
        
        # Live Data Display
        data_frame = tk.LabelFrame(self.root, text="Live IED Response", 
                                 fg='#4caf50', bg='#1a1a1a', font=('Arial', 12, 'bold'))
        data_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.data_text = tk.Text(data_frame, bg='#0d1117', fg='#4caf50', 
                               font=('Courier', 9), height=8)
        self.data_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Control Buttons
        control_frame = tk.Frame(self.root, bg='#1a1a1a')
        control_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Button(control_frame, text="RESET ALL", bg='#607d8b', fg='white',
                 font=('Arial', 10, 'bold'), command=self.reset_all).pack(side='left', padx=5)
        
        tk.Button(control_frame, text="EMERGENCY STOP", bg='#d32f2f', fg='white',
                 font=('Arial', 10, 'bold'), command=self.emergency_stop).pack(side='right', padx=5)
        
    def update_voltage(self, value):
        self.send_command('updateVoltage', {'voltage': float(value)})
        
    def update_current(self, value):
        self.send_command('updateCurrent', {'current': float(value)})
        
    def update_frequency(self, value):
        self.send_command('updateFrequency', {'frequency': float(value)})
        
    def update_fault_current(self, value):
        self.send_command('updateFaultCurrent', {'faultCurrent': float(value)})
        
    def toggle_fault(self):
        self.send_command('toggleFault', {'active': self.fault_active.get()})
        
    def inject_fault(self):
        self.fault_current.set(2500)
        self.current.set(2500)
        self.fault_active.set(True)
        self.send_command('toggleFault', {'active': True})
        self.send_command('updateFaultCurrent', {'faultCurrent': 2500})
        
    def scenario_normal(self):
        self.voltage.set(132.0)
        self.current.set(450)
        self.frequency.set(50.0)
        self.fault_current.set(0)
        self.fault_active.set(False)
        self.apply_all_settings()
        
    def scenario_overcurrent(self):
        self.current.set(1500)
        self.fault_current.set(1500)
        self.apply_all_settings()
        
    def scenario_ground_fault(self):
        self.fault_current.set(3000)
        self.current.set(3000)
        self.fault_active.set(True)
        self.apply_all_settings()
        
    def scenario_freq_dev(self):
        self.frequency.set(48.0)
        self.apply_all_settings()
        
    def apply_all_settings(self):
        self.send_command('updateVoltage', {'voltage': self.voltage.get()})
        self.send_command('updateCurrent', {'current': self.current.get()})
        self.send_command('updateFrequency', {'frequency': self.frequency.get()})
        self.send_command('updateFaultCurrent', {'faultCurrent': self.fault_current.get()})
        self.send_command('toggleFault', {'active': self.fault_active.get()})
        
    def reset_all(self):
        self.scenario_normal()
        
    def emergency_stop(self):
        self.fault_current.set(5000)
        self.current.set(5000)
        self.fault_active.set(True)
        self.send_command('updateFaultCurrent', {'faultCurrent': 5000})
        self.send_command('updateCurrent', {'current': 5000})
        self.send_command('toggleFault', {'active': True})
        
    def send_command(self, command, data):
        try:
            payload = {'type': 'command', 'command': command, 'data': data}
            response = requests.post('http://localhost:3000/api/command', 
                                   json=payload, timeout=2)
            if response.status_code == 200:
                self.status_indicator.config(text="● CONNECTED", fg='#4caf50')
                return True
        except Exception as e:
            self.status_indicator.config(text="● DISCONNECTED", fg='#f44336')
            return False
            
    def start_monitoring(self):
        def monitor():
            while True:
                try:
                    response = requests.get('http://localhost:3000/api/simulation-data', timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        self.update_display(data)
                        self.status_indicator.config(text="● CONNECTED", fg='#4caf50')
                except:
                    self.status_indicator.config(text="● DISCONNECTED", fg='#f44336')
                time.sleep(1)
                
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        
    def update_display(self, data):
        display_text = f"""Real-time IED Data:

Protection Relay (MMS Server):
  Voltage: {data.get('voltage', 0):.1f} kV
  Current: {data.get('current', 0):.0f} A
  Frequency: {data.get('frequency', 0):.3f} Hz
  Fault Current: {data.get('faultCurrent', 0):.0f} A
  
Digital Signals (GOOSE):
  Trip Command: {data.get('tripCommand', False)}
  Breaker Status: {'OPEN' if data.get('breakerStatus', False) else 'CLOSED'}
  Fault Detected: {data.get('faultDetected', False)}
  Overcurrent: {data.get('current', 0) > 1000}

System Status:
  MMS Port: 102 (Active)
  GOOSE AppId: 4096 (Publishing)
  Last Update: {time.strftime('%H:%M:%S')}
"""
        self.data_text.delete(1.0, tk.END)
        self.data_text.insert(1.0, display_text)
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SimulationControlPanel()
    app.run()