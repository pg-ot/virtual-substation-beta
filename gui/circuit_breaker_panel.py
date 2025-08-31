#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import requests
import threading
import time
import queue

class CircuitBreakerPanel:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Circuit Breaker IED - CB_LINE_01_001")
        self.root.geometry("350x500")
        self.root.configure(bg='#2c2c2c')
        self.data_queue = queue.Queue()
        
        self.setup_ui()
        self.start_monitoring()
        
    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg='#1a1a1a', height=50)
        header.pack(fill='x', padx=5, pady=5)
        
        tk.Label(header, text="🔌 CIRCUIT BREAKER IED", 
                fg='#00ff00', bg='#1a1a1a', font=('Courier', 14, 'bold')).pack(pady=10)
        
        # Status Frame
        status_frame = tk.LabelFrame(self.root, text="Breaker Status", 
                                   fg='#00ff00', bg='#2c2c2c', font=('Courier', 10))
        status_frame.pack(fill='x', padx=10, pady=5)
        
        self.position_label = tk.Label(status_frame, text="POSITION: CLOSED", 
                                     fg='#00ff00', bg='#2c2c2c', font=('Courier', 12, 'bold'))
        self.position_label.pack(pady=5)
        
        self.status_label = tk.Label(status_frame, text="STATUS: NORMAL", 
                                   fg='#00ff00', bg='#2c2c2c', font=('Courier', 10))
        self.status_label.pack(pady=2)
        
        # GOOSE Frame
        goose_frame = tk.LabelFrame(self.root, text="GOOSE Communication", 
                                  fg='#00ff00', bg='#2c2c2c', font=('Courier', 10))
        goose_frame.pack(fill='x', padx=10, pady=5)
        
        self.trip_received_label = tk.Label(goose_frame, text="TRIP RECEIVED: NO", 
                                          fg='#ccc', bg='#2c2c2c', font=('Courier', 10))
        self.trip_received_label.pack(pady=2)
        
        self.stnum_label = tk.Label(goose_frame, text="State Number: 0", 
                                  fg='#ccc', bg='#2c2c2c', font=('Courier', 9))
        self.stnum_label.pack(pady=1)
        
        self.sqnum_label = tk.Label(goose_frame, text="Sequence Number: 0", 
                                  fg='#ccc', bg='#2c2c2c', font=('Courier', 9))
        self.sqnum_label.pack(pady=1)
        
        # Control Frame
        control_frame = tk.LabelFrame(self.root, text="Manual Control", 
                                    fg='#00ff00', bg='#2c2c2c', font=('Courier', 10))
        control_frame.pack(fill='x', padx=10, pady=5)
        
        button_frame = tk.Frame(control_frame, bg='#2c2c2c')
        button_frame.pack(pady=10)
        
        self.trip_button = tk.Button(button_frame, text="TRIP", bg='#ff0000', fg='white',
                                   font=('Courier', 12, 'bold'), width=8,
                                   command=self.manual_trip)
        self.trip_button.pack(side='left', padx=5)
        
        self.close_button = tk.Button(button_frame, text="CLOSE", bg='#00aa00', fg='white',
                                    font=('Courier', 12, 'bold'), width=8,
                                    command=self.manual_close)
        self.close_button.pack(side='left', padx=5)
        
        self.debug_button = tk.Button(button_frame, text="DEBUG", bg='#ffaa00', fg='white',
                                    font=('Courier', 10, 'bold'), width=8,
                                    command=self.debug_test)
        self.debug_button.pack(side='left', padx=5)
        
        # Diagnostics Frame
        diag_frame = tk.LabelFrame(self.root, text="Diagnostics", 
                                 fg='#00ff00', bg='#2c2c2c', font=('Courier', 10))
        diag_frame.pack(fill='x', padx=10, pady=5)
        
        self.sf6_label = tk.Label(diag_frame, text="SF6 Pressure: 6.2 bar", 
                                fg='#00ff00', bg='#2c2c2c', font=('Courier', 9))
        self.sf6_label.pack(pady=2)
        
        self.operations_label = tk.Label(diag_frame, text="Operations: 1,247", 
                                       fg='#ccc', bg='#2c2c2c', font=('Courier', 9))
        self.operations_label.pack(pady=2)
        
        self.last_operation_label = tk.Label(diag_frame, text="Last Op: --:--:--", 
                                           fg='#ccc', bg='#2c2c2c', font=('Courier', 9))
        self.last_operation_label.pack(pady=2)
        
        # GOOSE Message Log
        log_frame = tk.LabelFrame(self.root, text="GOOSE Message Log", 
                                fg='#00ff00', bg='#2c2c2c', font=('Courier', 10))
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, bg='#1a1a1a', fg='#00ff00', 
                              font=('Courier', 8), height=8)
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=scrollbar.set)
        
    def manual_trip(self):
        # Send direct command to breaker container
        try:
            response = requests.post('http://localhost:8081/trip', timeout=1)
            if response.status_code == 200:
                self.log_message("MANUAL TRIP COMMAND ISSUED")
            else:
                self.log_message(f"TRIP FAILED: HTTP {response.status_code}")
        except Exception as e:
            self.log_message(f"TRIP FAILED: {str(e)[:30]}")
        
    def manual_close(self):
        # Send direct command to breaker container  
        try:
            response = requests.post('http://localhost:8081/close', timeout=1)
            if response.status_code == 200:
                self.log_message("MANUAL CLOSE COMMAND ISSUED")
            else:
                self.log_message(f"CLOSE FAILED: HTTP {response.status_code}")
        except Exception as e:
            self.log_message(f"CLOSE FAILED: {str(e)[:30]}")
        
    def send_command(self, command, data):
        # Remove simulator communication - breaker only responds to GOOSE
        pass
            
    def log_message(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def debug_test(self):
        try:
            response = requests.get('http://localhost:8081', timeout=2)
            if response.status_code == 200:
                data = response.json()
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(tk.END, f"DEBUG: Circuit Breaker Communication Test\n\nHTTP Status: {response.status_code}\nResponse: {data}\n\nTest: SUCCESS\n")
            else:
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(tk.END, f"DEBUG: Communication Test\n\nHTTP Status: {response.status_code}\nTest: FAILED\n")
        except Exception as e:
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, f"DEBUG: Communication Test\n\nError: {str(e)}\nTest: FAILED\n")
        
    def process_queue(self):
        try:
            while True:
                msg_type, data = self.data_queue.get_nowait()
                if msg_type == 'data':
                    self.update_display_direct(data)
                    self.status_label.config(text="STATUS: NORMAL", fg='#00ff00')
                elif msg_type == 'error':
                    if data == 'NO CONNECTION':
                        self.status_label.config(text="STATUS: NO CONNECTION", fg='#ff0000')
                    elif data == 'TIMEOUT':
                        self.status_label.config(text="STATUS: TIMEOUT", fg='#ff0000')
                    elif data == 'PARSING ERROR':
                        self.status_label.config(text="STATUS: PARSING ERROR", fg='#ffff00')
                    else:
                        self.status_label.config(text=f"STATUS: {data}", fg='#ff8800')
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)
        
    def start_monitoring(self):
        def monitor():
            while True:
                try:
                    # Get actual breaker container status
                    response = requests.get('http://localhost:8081', timeout=2)
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            self.data_queue.put(('data', data))
                        except ValueError:
                            self.data_queue.put(('error', 'PARSING ERROR'))
                    else:
                        self.data_queue.put(('error', f'HTTP {response.status_code}'))
                except requests.exceptions.ConnectionError:
                    self.data_queue.put(('error', 'NO CONNECTION'))
                except requests.exceptions.Timeout:
                    self.data_queue.put(('error', 'TIMEOUT'))
                except Exception as e:
                    self.data_queue.put(('error', str(e)[:15]))
                time.sleep(1)
                
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        self.root.after(100, self.process_queue)
        
    def update_display(self, data):
        # This method kept for compatibility but not used
        pass
        
    def update_display_direct(self, data):
        # Update breaker position from direct container communication
        position = data.get('position', 'CLOSED')
        if position == 'OPEN':
            self.position_label.config(text="POSITION: OPEN", fg='#ff0000')
            self.status_label.config(text="STATUS: OPEN", fg='#ff8800')
        else:
            self.position_label.config(text="POSITION: CLOSED", fg='#00ff00')
            self.status_label.config(text="STATUS: NORMAL", fg='#00ff00')
            
        # Update trip received from direct container
        trip_received = data.get('tripReceived', False)
        if trip_received:
            self.trip_received_label.config(text="TRIP RECEIVED: YES", fg='#ff0000')
            if not hasattr(self, 'last_trip_state_direct') or not self.last_trip_state_direct:
                self.log_message("⚡ GOOSE TRIP SIGNAL RECEIVED")
                self.last_operation_label.config(text=f"Last Op: {time.strftime('%H:%M:%S')}")
        else:
            self.trip_received_label.config(text="TRIP RECEIVED: NO", fg='#ccc')
            
        # Update GOOSE message details
        stnum = data.get('gooseStNum', 0)
        sqnum = data.get('gooseSqNum', 0)
        msg_count = data.get('gooseMsgCount', 0)
        last_time = data.get('lastGooseTime', '--:--:--')
        
        self.stnum_label.config(text=f"State Number: {stnum}")
        self.sqnum_label.config(text=f"Sequence Number: {sqnum}")
        
        # Log GOOSE message activity
        if hasattr(self, 'last_msg_count') and msg_count > self.last_msg_count:
            self.log_message(f"GOOSE MSG: StNum={stnum} SqNum={sqnum} Time={last_time}")
        
        self.last_msg_count = msg_count
        self.last_trip_state_direct = trip_received
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = CircuitBreakerPanel()
    app.run()