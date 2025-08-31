# Communication Flow Documentation
## Virtual Substation Training System - IEC 61850 Implementation

### 🎯 **Overview**
This document explains the complete communication architecture, data flows, and protocol interactions in the Virtual Substation Training System. The system implements authentic IEC 61850 protocols with dual-network architecture separating operational (Process Bus) and monitoring (Station Bus) communications.

---

## 🏗️ **System Architecture**

### **Physical Network Topology**
```
┌─────────────────────────────────────────────────────────────────┐
│                        HOST SYSTEM (Linux)                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Simulation GUI  │  │ Protection GUI  │  │ Circuit Br GUI  │ │
│  │ Port: 3000      │  │ Port: 102       │  │ Port: 8081      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│           │                     │                     │         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Web Interface   │  │                 │  │                 │ │
│  │ Container       │  │                 │  │                 │ │
│  │ Port: 3000      │  │                 │  │                 │ │
│  └─────────────────┘  │                 │  │                 │ │
│           │            │                 │  │                 │ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              DOCKER BRIDGE NETWORKS                        │ │
│  │                                                             │ │
│  │  Process Bus (192.168.10.0/24)    Station Bus (192.168.20.0/24) │
│  │  ┌─────────────────┐              ┌─────────────────┐      │ │
│  │  │ Protection      │◄─────────────┤ Protection      │      │ │
│  │  │ Relay           │              │ Relay           │      │ │
│  │  │ (GOOSE Pub)     │              │ (MMS Server)    │      │ │
│  │  └─────────┬───────┘              └─────────┬───────┘      │ │
│  │            │                                │              │ │
│  │            ▼                                ▼              │ │
│  │  ┌─────────────────┐              ┌─────────────────┐      │ │
│  │  │ Circuit Breaker │              │ HMI/SCADA       │      │ │
│  │  │ (GOOSE Sub)     │              │ (MMS Client)    │      │ │
│  │  │ TCP: 8081       │              │ HTTP: 8080      │      │ │
│  │  └─────────────────┘              └─────────────────┘      │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### **Container Network Configuration**
- **Process Bus**: 192.168.10.0/24 (High-speed operational communication)
- **Station Bus**: 192.168.20.0/24 (Configuration and monitoring)
- **Host Bridge**: Docker bridge for GUI panel access

---

## 📡 **Communication Protocols & Ports**

### **IEC 61850 Protocols**
| Protocol | Purpose | Network | Speed | Implementation |
|----------|---------|---------|-------|----------------|
| **GOOSE** | Trip signals, status | Process Bus | <4ms | libiec61850 |
| **MMS** | Configuration, monitoring | Station Bus | ~100ms | libiec61850 |
| **SV** | Sampled values | Process Bus | <1ms | Simulated |

### **Port Mapping**
| Component | Protocol | Port | Purpose |
|-----------|----------|------|---------|
| Protection Relay | MMS Server | 102 | IEC 61850 MMS communication |
| Circuit Breaker | TCP Server | 8081 | GUI panel communication |
| HMI/SCADA | HTTP API | 8080 | Web interface for monitoring |
| Web Interface | HTTP Server | 3000 | Simulation control |

---

## 🔄 **Data Flow Patterns**

### **1. Simulation Control Flow**
```
┌─────────────────┐    HTTP POST     ┌─────────────────┐    HTTP GET
│ Simulation      │ ──────────────► │ Web Interface   │ ◄──────────────
│ Control Panel   │   Commands       │ Container       │   Fetch Data
│ (Tkinter GUI)   │                 │ (Node.js)       │
└─────────────────┘                 └─────────┬───────┘
                                              │ HTTP GET
                                              ▼
                                    ┌─────────────────┐
                                    │ Protection      │
                                    │ Relay Container │
                                    │ (Fetches data)  │
                                    └─────────────────┘
```

**Data Elements:**
- Voltage L1 (kV)
- Current L1 (A) 
- Frequency (Hz)
- Fault Current (A)
- Manual trip commands
- Breaker position commands

### **2. Protection Logic Flow**
```
┌─────────────────┐    Analog       ┌─────────────────┐    GOOSE
│ Simulation      │    Values       │ Protection      │    Messages
│ Data Input      │ ──────────────► │ Logic Engine    │ ──────────────►
│                 │                 │ (50/51/50G/     │
└─────────────────┘                 │  51G/81U)       │
                                    └─────────┬───────┘
                                              │ MMS Updates
                                              ▼
                                    ┌─────────────────┐
                                    │ MMS Data Model  │
                                    │ (IEC 61850)     │
                                    └─────────────────┘
```

**Protection Elements:**
- **50**: Instantaneous Overcurrent (≥2500A → Trip)
- **51**: Time Overcurrent (≥1000A → 1.0s → Trip)
- **50G**: Instantaneous Ground Fault (≥800A → Trip)
- **51G**: Time Ground Fault (≥300A → 0.5s → Trip)
- **81U**: Underfrequency (<48.5Hz → Trip)

### **3. GOOSE Communication Flow**
```
┌─────────────────┐    GOOSE        ┌─────────────────┐    Position
│ Protection      │    Dataset      │ Circuit Breaker │    Update
│ Relay           │ ──────────────► │ IED             │ ──────────────►
│ (Publisher)     │   Multicast     │ (Subscriber)    │   Auto-Trip
└─────────────────┘   Ethernet      └─────────────────┘
```

**GOOSE Dataset (8 values):**
```
SPCSO1: Trip Command        (Boolean + Timestamp)
SPCSO2: Breaker Position    (Boolean + Timestamp)  
SPCSO3: Fault Detected      (Boolean + Timestamp)
SPCSO4: Overcurrent Pickup  (Boolean + Timestamp)
```

**GOOSE Parameters:**
- **AppId**: 4096
- **MAC Address**: 01:0c:cd:01:00:01 (Multicast)
- **VLAN**: Priority 4
- **TTL**: 3000ms
- **Interface**: eth0 (Process Bus)

### **4. MMS Communication Flow**
```
┌─────────────────┐    MMS          ┌─────────────────┐    Data
│ HMI/SCADA       │    Read/Write   │ Protection      │    Model
│ Container       │ ◄─────────────► │ Relay           │ ◄──────────
│ (MMS Client)    │   Port 102      │ (MMS Server)    │   Updates
└─────────────────┘                 └─────────────────┘
```

**MMS Objects:**
```
Analog Inputs (FC=MX):
- simpleIOGenericIO/GGIO1.AnIn1.mag.f  (Voltage)
- simpleIOGenericIO/GGIO1.AnIn2.mag.f  (Current)
- simpleIOGenericIO/GGIO1.AnIn3.mag.f  (Frequency)
- simpleIOGenericIO/GGIO1.AnIn4.mag.f  (Fault Current)

Digital Status (FC=ST):
- simpleIOGenericIO/GGIO1.SPCSO1.stVal (Trip Command)
- simpleIOGenericIO/GGIO1.SPCSO2.stVal (Breaker Position)
- simpleIOGenericIO/GGIO1.SPCSO3.stVal (Fault Detected)
- simpleIOGenericIO/GGIO1.SPCSO4.stVal (OC Pickup)
```

---

## 🖥️ **GUI Panel Communication**

### **Panel Architecture**
```
┌─────────────────┐    Direct       ┌─────────────────┐
│ Protection      │    MMS          │ Protection      │
│ Relay Panel     │ ◄─────────────► │ Relay Container │
│ (Tkinter)       │   Port 102      │ (MMS Server)    │
└─────────────────┘                 └─────────────────┘

┌─────────────────┐    Direct       ┌─────────────────┐
│ Circuit Breaker │    TCP          │ Circuit Breaker │
│ Panel           │ ◄─────────────► │ Container       │
│ (Tkinter)       │   Port 8081     │ (TCP Server)    │
└─────────────────┘                 └─────────────────┘

┌─────────────────┐    HTTP         ┌─────────────────┐
│ HMI/SCADA       │    API          │ HMI/SCADA       │
│ Panel           │ ◄─────────────► │ Container       │
│ (Tkinter)       │   Port 8080     │ (HTTP Server)   │
└─────────────────┘                 └─────────────────┘
```

### **Panel Communication Details**

#### **Simulation Control Panel**
- **Connection**: HTTP → Web Interface (Port 3000)
- **Function**: Master control for all simulation parameters
- **Update Rate**: Real-time (1Hz monitoring)
- **Commands**: Analog value updates, scenario buttons, manual controls

#### **Protection Relay Panel**  
- **Primary**: Direct MMS → Protection Relay (Port 102)
- **Fallback**: HTTP → Web Interface (Port 3000)
- **Function**: Real-time protection logic monitoring
- **Data**: Live measurements, protection element status, trip reasons
- **Update Rate**: 1Hz (MMS polling)

#### **Circuit Breaker Panel**
- **Connection**: Direct TCP → Circuit Breaker (Port 8081)
- **Function**: Breaker position and GOOSE message monitoring
- **Data**: Position status, trip reception, manual controls
- **Update Rate**: 1Hz (TCP polling)
- **Response Format**: JSON status messages

#### **HMI/SCADA Panel**
- **Connection**: HTTP → HMI/SCADA Container (Port 8080)
- **Function**: System-wide monitoring and alarm management
- **Data**: Aggregated measurements, alarms, remote control
- **Update Rate**: 1Hz (HTTP polling)

---

## ⚡ **Complete Operational Sequences**

### **Normal Operation Sequence**
```
1. Simulation Control → Sets normal values → Web Interface
2. Web Interface → Provides data → Protection Relay (HTTP fetch)
3. Protection Relay → Updates MMS model → Internal processing
4. Protection Relay → GOOSE heartbeat → Circuit Breaker (Process Bus)
5. Protection Relay → MMS data → HMI/SCADA (Station Bus)
6. All GUI Panels → Poll status → Display updates (1Hz)
```

### **Fault Detection & Trip Sequence**
```
1. Simulation Control → Injects fault (I≥2500A) → Protection Relay
2. Protection Relay → 50 Element triggers → Immediate trip decision
3. Protection Relay → GOOSE trip signal → Circuit Breaker (<4ms)
4. Circuit Breaker → Receives GOOSE → Auto-opens breaker
5. Circuit Breaker → Updates position → TCP server (Port 8081)
6. Protection Relay → MMS alarm → HMI/SCADA (Station Bus)
7. All Panels → Detect changes → Update displays
8. HMI/SCADA Panel → Shows alarm → Operator notification
```

### **Manual Trip Sequence**
```
1. Protection Relay Panel → Manual trip button → Web Interface
2. Web Interface → Trip command → Protection Relay
3. Protection Relay → Manual trip logic → GOOSE trip signal
4. Circuit Breaker → GOOSE reception → Auto-opens
5. All Panels → Status updates → Synchronized display
```

### **System Recovery Sequence**
```
1. Simulation Control → Reset to normal → All parameters
2. Protection Relay → Conditions normal → Reset protection elements
3. HMI/SCADA Panel → Manual close → Circuit Breaker
4. Circuit Breaker → Close command → Position update
5. Protection Relay → GOOSE update → Normal status
6. All Panels → Green status → System ready
```

---

## 🔧 **Technical Implementation Details**

### **libiec61850 Integration**
- **GOOSE Publisher**: `GoosePublisher_create()` with CommParameters
- **GOOSE Subscriber**: `GooseSubscriber_create()` with callback
- **MMS Server**: `IedServer_create()` with static model
- **MMS Client**: `IedConnection_create()` with read/write operations

### **Network Configuration**
```yaml
networks:
  process_bus:
    driver: bridge
    ipam:
      config:
        - subnet: 192.168.10.0/24
  station_bus:
    driver: bridge
    ipam:
      config:
        - subnet: 192.168.20.0/24
```

### **Container Networking**
- **Protection Relay**: Dual-homed (both networks)
- **Circuit Breaker**: Process Bus only
- **HMI/SCADA**: Station Bus only
- **Web Interface**: Host network access

### **Data Synchronization**
- **GOOSE**: Event-driven (state changes)
- **MMS**: Polling-based (1-2 second intervals)
- **GUI Panels**: 1Hz update rate
- **Protection Logic**: 500ms cycle time

This communication architecture ensures authentic IEC 61850 protocol implementation while providing responsive GUI interfaces for training and monitoring purposes.