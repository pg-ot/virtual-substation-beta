#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import requests
import threading
import time

class HMIScadaPanel:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SUBSTATION SCADA - BAY 01 LINE PROTECTION")
        self.root.geometry("800x900")
        self.root.configure(bg='#1e1e1e')  # Dark SCADA background
        self.root.resizable(True, True)
        
        self.setup_ui()
        self.start_monitoring()
        
    def setup_ui(self):
        # SCADA Header with Status Bar
        header = tk.Frame(self.root, bg='#0d47a1', height=60, relief='raised', bd=2)
        header.pack(fill='x', padx=2, pady=2)
        
        # Title and Status
        title_frame = tk.Frame(header, bg='#0d47a1')
        title_frame.pack(fill='x', pady=5)
        
        tk.Label(title_frame, text="⚡ SUBSTATION AUTOMATION SYSTEM", 
                fg='white', bg='#0d47a1', font=('Arial', 16, 'bold')).pack(side='left', padx=10)
        
        # System Status Indicators
        status_frame = tk.Frame(title_frame, bg='#0d47a1')
        status_frame.pack(side='right', padx=10)
        
        self.system_status = tk.Label(status_frame, text="● SYSTEM NORMAL", 
                                    fg='#4caf50', bg='#0d47a1', font=('Arial', 10, 'bold'))
        self.system_status.pack(side='right', padx=5)
        
        # Main SCADA Panel
        main_panel = tk.Frame(self.root, bg='#1e1e1e')
        main_panel.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Left Panel - Measurements and Status
        left_panel = tk.Frame(main_panel, bg='#1e1e1e')
        left_panel.pack(side='left', fill='both', expand=True, padx=5)
        
        # Right Panel - Controls and Status
        right_panel = tk.Frame(main_panel, bg='#1e1e1e', width=300)
        right_panel.pack(side='right', fill='y', padx=5)
        right_panel.pack_propagate(False)
        
        # Communication Status Panel
        conn_frame = tk.LabelFrame(left_panel, text="🔗 COMMUNICATION STATUS", 
                                 fg='#81c784', bg='#263238', font=('Arial', 11, 'bold'),
                                 relief='groove', bd=2)
        conn_frame.pack(fill='x', pady=5)
        
        # Communication Grid
        comm_grid = tk.Frame(conn_frame, bg='#263238')
        comm_grid.pack(fill='x', padx=10, pady=5)
        
        tk.Label(comm_grid, text="MMS:", fg='#b0bec5', bg='#263238', 
                font=('Arial', 10)).grid(row=0, column=0, sticky='w', padx=5)
        self.conn_status_label = tk.Label(comm_grid, text="🟢 ONLINE", 
                                        fg='#4caf50', bg='#263238', font=('Arial', 10, 'bold'))
        self.conn_status_label.grid(row=0, column=1, sticky='w', padx=10)
        
        tk.Label(comm_grid, text="GOOSE:", fg='#b0bec5', bg='#263238', 
                font=('Arial', 10)).grid(row=1, column=0, sticky='w', padx=5)
        self.goose_status_label = tk.Label(comm_grid, text="🟡 CHECKING", 
                                         fg='#ff9800', bg='#263238', font=('Arial', 10, 'bold'))
        self.goose_status_label.grid(row=1, column=1, sticky='w', padx=10)
        
        tk.Label(comm_grid, text="Server:", fg='#b0bec5', bg='#263238', 
                font=('Arial', 10)).grid(row=2, column=0, sticky='w', padx=5)
        tk.Label(comm_grid, text="protection_relay_ied:102", 
                fg='#90caf9', bg='#263238', font=('Arial', 10)).grid(row=2, column=1, sticky='w', padx=10)
        
        # Real-time Measurements Panel
        data_frame = tk.LabelFrame(left_panel, text="📊 REAL-TIME MEASUREMENTS", 
                                 fg='#81c784', bg='#263238', font=('Arial', 11, 'bold'),
                                 relief='groove', bd=2)
        data_frame.pack(fill='x', pady=5)
        
        # Measurement Grid with SCADA styling
        meas_grid = tk.Frame(data_frame, bg='#263238')
        meas_grid.pack(fill='x', padx=10, pady=10)
        
        # Voltage with SCADA colors
        tk.Label(meas_grid, text="⚡ Voltage L1:", fg='#ffeb3b', bg='#263238', 
                font=('Arial', 11, 'bold')).grid(row=0, column=0, sticky='w', padx=5, pady=3)
        self.voltage_label = tk.Label(meas_grid, text="132.0 kV", fg='#4caf50', bg='#1a1a1a', 
                                    font=('Arial', 14, 'bold'), relief='sunken', bd=1, width=12)
        self.voltage_label.grid(row=0, column=1, sticky='w', padx=15, pady=3)
        
        # Current with SCADA colors
        tk.Label(meas_grid, text="🔌 Current L1:", fg='#ffeb3b', bg='#263238', 
                font=('Arial', 11, 'bold')).grid(row=1, column=0, sticky='w', padx=5, pady=3)
        self.current_label = tk.Label(meas_grid, text="450 A", fg='#4caf50', bg='#1a1a1a', 
                                    font=('Arial', 14, 'bold'), relief='sunken', bd=1, width=12)
        self.current_label.grid(row=1, column=1, sticky='w', padx=15, pady=3)
        
        # Frequency with SCADA colors
        tk.Label(meas_grid, text="📡 Frequency:", fg='#ffeb3b', bg='#263238', 
                font=('Arial', 11, 'bold')).grid(row=2, column=0, sticky='w', padx=5, pady=3)
        self.frequency_label = tk.Label(meas_grid, text="50.00 Hz", fg='#4caf50', bg='#1a1a1a', 
                                      font=('Arial', 14, 'bold'), relief='sunken', bd=1, width=12)
        self.frequency_label.grid(row=2, column=1, sticky='w', padx=15, pady=3)
        
        # Fault Current with SCADA colors
        tk.Label(meas_grid, text="⚠️ Fault Current:", fg='#ff5722', bg='#263238', 
                font=('Arial', 11, 'bold')).grid(row=3, column=0, sticky='w', padx=5, pady=3)
        self.fault_current_label = tk.Label(meas_grid, text="0 A", fg='#4caf50', bg='#1a1a1a', 
                                          font=('Arial', 14, 'bold'), relief='sunken', bd=1, width=12)
        self.fault_current_label.grid(row=3, column=1, sticky='w', padx=15, pady=3)
        
        # Active Power with SCADA colors
        tk.Label(meas_grid, text="⚡ Active Power:", fg='#2196f3', bg='#263238', 
                font=('Arial', 11, 'bold')).grid(row=4, column=0, sticky='w', padx=5, pady=3)
        self.power_label = tk.Label(meas_grid, text="59.4 MW", fg='#4caf50', bg='#1a1a1a', 
                                  font=('Arial', 14, 'bold'), relief='sunken', bd=1, width=12)
        self.power_label.grid(row=4, column=1, sticky='w', padx=15, pady=3)
        
        # Reactive Power with SCADA colors
        tk.Label(meas_grid, text="🔄 Reactive Power:", fg='#9c27b0', bg='#263238', 
                font=('Arial', 11, 'bold')).grid(row=5, column=0, sticky='w', padx=5, pady=3)
        self.reactive_power_label = tk.Label(meas_grid, text="18.5 MVAr", fg='#4caf50', bg='#1a1a1a', 
                                           font=('Arial', 14, 'bold'), relief='sunken', bd=1, width=12)
        self.reactive_power_label.grid(row=5, column=1, sticky='w', padx=15, pady=3)
        
        # Power Factor with SCADA colors
        tk.Label(meas_grid, text="📈 Power Factor:", fg='#ff9800', bg='#263238', 
                font=('Arial', 11, 'bold')).grid(row=6, column=0, sticky='w', padx=5, pady=3)
        self.power_factor_label = tk.Label(meas_grid, text="0.95", fg='#4caf50', bg='#1a1a1a', 
                                         font=('Arial', 14, 'bold'), relief='sunken', bd=1, width=12)
        self.power_factor_label.grid(row=6, column=1, sticky='w', padx=15, pady=3)
        
        # System Alarms Panel
        alarm_frame = tk.LabelFrame(right_panel, text="🚨 SYSTEM ALARMS", 
                                  fg='#f44336', bg='#263238', font=('Arial', 11, 'bold'),
                                  relief='groove', bd=2)
        alarm_frame.pack(fill='x', pady=5)
        
        self.alarm_listbox = tk.Listbox(alarm_frame, bg='#1a1a1a', fg='#f44336', 
                                      font=('Arial', 10), height=4, 
                                      selectbackground='#424242', selectforeground='white')
        self.alarm_listbox.pack(fill='x', padx=10, pady=10)
        
        # Control Commands Panel
        control_frame = tk.LabelFrame(right_panel, text="🎛️ REMOTE CONTROL", 
                                    fg='#2196f3', bg='#263238', font=('Arial', 11, 'bold'),
                                    relief='groove', bd=2)
        control_frame.pack(fill='x', pady=5)
        
        cmd_grid = tk.Frame(control_frame, bg='#263238')
        cmd_grid.pack(fill='x', padx=10, pady=10)
        
        tk.Button(cmd_grid, text="📖 READ VALUES", bg='#37474f', fg='white', 
                 font=('Arial', 10, 'bold'), command=self.read_values, 
                 relief='raised', bd=2, width=15).grid(row=0, column=0, padx=3, pady=3)
        
        tk.Button(cmd_grid, text="🚨 SEND TRIP", bg='#d32f2f', fg='white', 
                 font=('Arial', 10, 'bold'), command=self.send_trip, 
                 relief='raised', bd=2, width=15).grid(row=0, column=1, padx=3, pady=3)
        
        tk.Button(cmd_grid, text="🔒 CLOSE BREAKER", bg='#388e3c', fg='white', 
                 font=('Arial', 10, 'bold'), command=self.close_breaker, 
                 relief='raised', bd=2, width=15).grid(row=1, column=0, padx=3, pady=3)
        
        tk.Button(cmd_grid, text="✅ ACK ALARMS", bg='#f57c00', fg='white', 
                 font=('Arial', 10, 'bold'), command=self.ack_alarms, 
                 relief='raised', bd=2, width=15).grid(row=1, column=1, padx=3, pady=3)
        
        tk.Button(cmd_grid, text="🔄 RESET PROTECTION", bg='#1976d2', fg='white', 
                 font=('Arial', 10, 'bold'), command=self.reset_relay, 
                 relief='raised', bd=2, width=15).grid(row=2, column=1, padx=3, pady=3)
        
        tk.Button(cmd_grid, text="🔓 OPEN BREAKER", bg='#e64a19', fg='white', 
                 font=('Arial', 10, 'bold'), command=self.open_breaker, 
                 relief='raised', bd=2, width=15).grid(row=2, column=0, padx=3, pady=3)
        
        tk.Button(cmd_grid, text="🔧 DIAGNOSTICS", bg='#7b1fa2', fg='white', 
                 font=('Arial', 10, 'bold'), command=self.show_diagnostics, 
                 relief='raised', bd=2, width=15).grid(row=3, column=0, padx=3, pady=3)
        
        tk.Button(cmd_grid, text="🧪 TEST TRIP", bg='#ffa000', fg='white', 
                 font=('Arial', 10, 'bold'), command=self.test_trip, 
                 relief='raised', bd=2, width=15).grid(row=3, column=1, padx=3, pady=3)
        
        # Communication Log Panel
        log_frame = tk.LabelFrame(right_panel, text="📋 COMMUNICATION LOG", 
                                fg='#607d8b', bg='#263238', font=('Arial', 11, 'bold'),
                                relief='groove', bd=2)
        log_frame.pack(fill='both', expand=True, pady=5)
        
        self.log_text = tk.Text(log_frame, bg='#0d1117', fg='#58a6ff', 
                              font=('Consolas', 9), height=8, 
                              insertbackground='white', selectbackground='#264f78')
        self.log_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview, bg='#37474f')
        scrollbar.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Protection Status Panel
        trip_frame = tk.LabelFrame(left_panel, text="🛡️ PROTECTION STATUS", 
                                 fg='#f44336', bg='#263238', font=('Arial', 11, 'bold'),
                                 relief='groove', bd=2)
        trip_frame.pack(fill='x', pady=5)
        
        self.trip_reason_label = tk.Label(trip_frame, text="⚡ NORMAL OPERATION", 
                                        fg='#4caf50', bg='#1a1a1a', font=('Arial', 12, 'bold'),
                                        relief='sunken', bd=2, pady=10)
        self.trip_reason_label.pack(fill='x', padx=10, pady=10)
        
        # Breaker Status Panel
        breaker_frame = tk.LabelFrame(left_panel, text="🔌 CIRCUIT BREAKER STATUS", 
                                    fg='#2196f3', bg='#263238', font=('Arial', 11, 'bold'),
                                    relief='groove', bd=2)
        breaker_frame.pack(fill='x', pady=5)
        
        # Breaker status grid
        breaker_grid = tk.Frame(breaker_frame, bg='#263238')
        breaker_grid.pack(fill='x', padx=10, pady=10)
        
        tk.Label(breaker_grid, text="Position:", fg='#b0bec5', bg='#263238', 
                font=('Arial', 11)).grid(row=0, column=0, sticky='w', padx=5, pady=3)
        self.breaker_position_label = tk.Label(breaker_grid, text="🔒 CLOSED", 
                                             fg='#4caf50', bg='#1a1a1a', font=('Arial', 12, 'bold'),
                                             relief='sunken', bd=1, width=15)
        self.breaker_position_label.grid(row=0, column=1, sticky='w', padx=15, pady=3)
        
        tk.Label(breaker_grid, text="GOOSE Count:", fg='#b0bec5', bg='#263238', 
                font=('Arial', 11)).grid(row=1, column=0, sticky='w', padx=5, pady=3)
        self.goose_count_label = tk.Label(breaker_grid, text="0", 
                                        fg='#90caf9', bg='#1a1a1a', font=('Arial', 12, 'bold'),
                                        relief='sunken', bd=1, width=15)
        self.goose_count_label.grid(row=1, column=1, sticky='w', padx=15, pady=3)
        
        # SCADA Status Bar
        status_bar = tk.Frame(self.root, bg='#0d47a1', height=30, relief='sunken', bd=1)
        status_bar.pack(fill='x', side='bottom')
        
        self.status_text = tk.Label(status_bar, text="🟢 SCADA SYSTEM READY", 
                                  fg='white', bg='#0d47a1', font=('Arial', 10, 'bold'))
        self.status_text.pack(side='left', padx=15, pady=5)
        
        self.time_label = tk.Label(status_bar, text="", 
                                 fg='#e1f5fe', bg='#0d47a1', font=('Arial', 10))
        self.time_label.pack(side='right', padx=15, pady=5)
        
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
    
    def close_breaker(self):
        # Send MMS close command via HMI server
        try:
            response = requests.post('http://localhost:8080/close', timeout=2)
            if response.status_code == 200:
                self.log_message("MMS CONTROL: GenericIO/GGIO1.SPCSO2.Oper.ctlVal = FALSE")
                self.log_message("MMS BREAKER: Close command via IEC 61850 MMS")
            else:
                self.log_message("MMS CONTROL FAILED: Close command")
        except:
            self.log_message("MMS CONNECTION ERROR: HMI/SCADA server unavailable")
        
    def reset_relay(self):
        # Send MMS reset command via HMI server
        try:
            response = requests.post('http://localhost:8080/reset', timeout=2)
            if response.status_code == 200:
                self.log_message("MMS CONTROL: Protection reset via IEC 61850 MMS")
                self.log_message("MMS RESET: All fault conditions cleared")
            else:
                self.log_message("MMS CONTROL FAILED: Reset command")
        except:
            self.log_message("MMS CONNECTION ERROR: HMI/SCADA server unavailable")
    
    def open_breaker(self):
        # Send MMS open command via HMI server
        try:
            response = requests.post('http://localhost:8080/open', timeout=2)
            if response.status_code == 200:
                self.log_message("MMS CONTROL: GenericIO/GGIO1.SPCSO2.Oper.ctlVal = TRUE")
                self.log_message("MMS BREAKER: Open command via IEC 61850 MMS")
            else:
                self.log_message("MMS CONTROL FAILED: Open command")
        except:
            self.log_message("MMS CONNECTION ERROR: HMI/SCADA server unavailable")
        
    def ack_alarms(self):
        self.alarm_listbox.delete(0, tk.END)
        self.log_message("All alarms acknowledged")
        
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
    
    def show_diagnostics(self):
        # Display comprehensive communication diagnostics
        diag_text = "=== COMMUNICATION DIAGNOSTICS ===\n\n"
        
        # Test MMS Connection
        try:
            response = requests.get('http://localhost:8080', timeout=2)
            if response.status_code == 200:
                diag_text += "MMS Connection: ✅ ACTIVE\n"
                diag_text += "HMI Server: localhost:8080 - OK\n"
                diag_text += "Protection Relay: protection_relay_ied:102 - OK\n"
            else:
                diag_text += "MMS Connection: ❌ FAILED\n"
        except:
            diag_text += "MMS Connection: ❌ OFFLINE\n"
            
        # Test MMS Communication to all devices
        try:
            response = requests.get('http://localhost:8080/diagnostics', timeout=2)
            if response.status_code == 200:
                data = response.json()
                diag_text += f"\nMMS Diagnostics: ✅ ACTIVE\n"
                diag_text += f"Protection Relay MMS: {data.get('protectionRelay', 'Unknown')}\n"
                diag_text += f"Circuit Breaker MMS: {data.get('circuitBreaker', 'Unknown')}\n"
                diag_text += f"GOOSE Messages: {data.get('gooseCount', 0)}\n"
            else:
                diag_text += "\nMMS Diagnostics: ❌ FAILED\n"
        except:
            diag_text += "\nMMS Diagnostics: ❌ OFFLINE\n"
            

            
        diag_text += "\n=== END DIAGNOSTICS ===\n"
        
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, diag_text)
        
    def start_monitoring(self):
        def monitor():
            while True:
                try:
                    response = requests.get('http://localhost:8080', timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        self.update_display(data)
                        self.conn_status_label.config(text="🟢 ONLINE", fg='#4caf50')
                        self.status_text.config(text="🟢 SCADA SYSTEM ACTIVE")
                        self.system_status.config(text="● SYSTEM NORMAL", fg='#4caf50')
                except:
                    self.conn_status_label.config(text="🔴 OFFLINE", fg='#f44336')
                    self.status_text.config(text="🔴 MMS CONNECTION LOST")
                    self.system_status.config(text="● SYSTEM FAULT", fg='#f44336')
                    
                # Get GOOSE status via MMS from HMI server
                try:
                    if 'response' in locals() and response.status_code == 200:
                        goose_data = data.get('gooseData', {})
                        msg_count = goose_data.get('messageCount', 0)
                        
                        # Update GOOSE status
                        if msg_count > 0:
                            self.goose_status_label.config(text=f"🟢 ACTIVE ({msg_count})", fg='#4caf50')
                        else:
                            self.goose_status_label.config(text="🟡 NO DATA", fg='#ff9800')
                            
                        # Update GOOSE count display
                        self.goose_count_label.config(text=str(msg_count))
                    else:
                        self.goose_status_label.config(text="🔴 OFFLINE", fg='#f44336')
                        self.goose_count_label.config(text="--")
                except:
                    self.goose_status_label.config(text="🔴 ERROR", fg='#f44336')
                    self.goose_count_label.config(text="--")
                    
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
        fault_current = data.get('faultCurrent', 0)
        
        self.voltage_label.config(text=f"{voltage:.1f} kV")
        self.current_label.config(text=f"{current:.0f} A")
        self.frequency_label.config(text=f"{frequency:.3f} Hz")
        self.fault_current_label.config(text=f"{fault_current:.0f} A")
        
        # Calculate power factor based on load conditions
        if current > 0:
            # Dynamic power factor: higher current = lower PF
            base_pf = 0.95
            pf_variation = min(0.1, (current - 400) / 2000)  # Varies with load
            power_factor = max(0.85, base_pf - pf_variation)
        else:
            power_factor = 1.0
            
        # Calculate active power
        power = voltage * current * 1.732 * power_factor / 1000  # 3-phase power in MW
        self.power_label.config(text=f"{power:.1f} MW")
        
        # Calculate reactive power (Q = P * tan(arccos(PF)))
        if power_factor < 1.0:
            reactive_power = power * (((1 - power_factor**2)**0.5) / power_factor)
        else:
            reactive_power = 0.0
        self.reactive_power_label.config(text=f"{reactive_power:.1f} MVAr")
        
        # Update power factor display with SCADA color coding
        self.power_factor_label.config(text=f"{power_factor:.3f}")
        if power_factor >= 0.95:
            self.power_factor_label.config(fg='#4caf50', bg='#e8f5e8')  # Good
        elif power_factor >= 0.90:
            self.power_factor_label.config(fg='#ff9800', bg='#fff3e0')  # Warning
        else:
            self.power_factor_label.config(fg='#f44336', bg='#ffebee')  # Poor
        
        # Update trip reason display
        last_alarm = data.get('lastAlarm', 'Normal Operation')
        trip_command = data.get('tripCommand', False)
        
        if trip_command:
            self.trip_reason_label.config(text=f"🚨 {last_alarm.upper()}", fg='#f44336', bg='#ffebee')
            self.system_status.config(text="● PROTECTION TRIP", fg='#f44336')
        else:
            self.trip_reason_label.config(text=f"⚡ {last_alarm.upper()}", fg='#4caf50', bg='#e8f5e8')
            if not hasattr(self, '_system_fault'):
                self.system_status.config(text="● SYSTEM NORMAL", fg='#4caf50')
        
        # Update breaker status display
        breaker_status = data.get('breakerStatus', False)
        if breaker_status:
            self.breaker_position_label.config(text="🔓 OPEN", fg='#f44336', bg='#ffebee')
        else:
            self.breaker_position_label.config(text="🔒 CLOSED", fg='#4caf50', bg='#e8f5e8')
        
        # Check for alarms
        fault_detected = data.get('faultDetected', False)
        
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
            
        # SCADA color coding for measurements
        if fault_detected:
            self.current_label.config(fg='#f44336', bg='#ffebee')
        elif current > 1000:
            self.current_label.config(fg='#ff9800', bg='#fff3e0')
        else:
            self.current_label.config(fg='#4caf50', bg='#e8f5e8')
            
        # SCADA color coding for fault current
        if fault_current > 300:
            self.fault_current_label.config(fg='#f44336', bg='#ffebee')
        elif fault_current > 100:
            self.fault_current_label.config(fg='#ff9800', bg='#fff3e0')
        else:
            self.fault_current_label.config(fg='#4caf50', bg='#e8f5e8')
            
        if frequency < 49.8 or frequency > 50.2:
            self.frequency_label.config(fg='#ff9800', bg='#fff3e0')
        else:
            self.frequency_label.config(fg='#4caf50', bg='#e8f5e8')
            
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = HMIScadaPanel()
    app.run()