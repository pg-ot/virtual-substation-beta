# Virtual Substation Training System
## IEC 61850 Protocol Demonstration

[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://docker.com)
[![IEC 61850](https://img.shields.io/badge/IEC%2061850-Basic-green)](https://en.wikipedia.org/wiki/IEC_61850)
[![License](https://img.shields.io/badge/License-Educational-orange)](LICENSE)

A containerized IEC 61850 protocol demonstration system implementing basic substation automation concepts for educational purposes.

## 🚀 Quick Start

```bash
# Build containers
make build

# Start system
make start

# Launch GUI panels
make gui
```

**Access Points:**
- **Web Interface**: http://localhost:3000
- **Protection Relay API**: http://localhost:8082
- **Circuit Breaker API**: http://localhost:8081
- **HMI/SCADA API**: http://localhost:8080

## 🎯 What This System Actually Does

### **IEC 61850 Protocol Implementation**
- ✅ **GOOSE** messaging between protection relay and circuit breaker
- ✅ **MMS** client/server communication for HMI/SCADA
- ✅ **Basic data modeling** using Generic I/O (GGIO1)
- ✅ **Containerized deployment** with dual networks

### **Protection Functions**
- **Instantaneous Overcurrent (50)**: I≥2500A → immediate trip
- **Time Overcurrent (51)**: I≥1000A → 1.0s delay → trip
- **Instantaneous Ground Fault (50G)**: FC≥800A → immediate trip
- **Time Ground Fault (51G)**: FC≥300A → 0.5s delay → trip
- **Underfrequency (81U)**: F<48.5Hz → immediate trip

### **Training Interface**
- 🎮 **4 Python GUI panels** for hands-on interaction
- 📊 **Web-based monitoring** with SVG single-line diagram
- ⚡ **Manual fault injection** and parameter control
- 🔄 **Real-time status updates** via HTTP APIs

## 🏗️ System Architecture

```
┌─────────────────┐    GOOSE     ┌──────────────────┐    GOOSE     ┌─────────────────┐
│ Web Interface   │◄────────────►│ Protection       │◄────────────►│ Circuit Breaker │
│ (Node.js)       │   HTTP       │ Relay (C)        │   AppId:4096 │ (C)             │
│ Port: 3000      │              │ MMS: 102         │              │ MMS: 103        │
└─────────────────┘              └──────────────────┘              └─────────────────┘
        │                                 │                                 │
        │                    MMS          │                                 │
        └─────────────────────────────────┼─────────────────────────────────┘
                                          │
                                 ┌─────────────────┐
                                 │ HMI/SCADA (C)   │
                                 │ MMS Client      │
                                 │ Port: 8080      │
                                 └─────────────────┘
```

### **Network Design**
- **Process Bus** (192.168.10.0/24): GOOSE communication
- **Station Bus** (192.168.20.0/24): MMS communication

## 📋 Requirements

### **System Requirements**
- **OS**: Linux (Ubuntu 20.04+ recommended)
- **Docker**: With privileged container support
- **Python**: 3.8+ with Tkinter
- **Node.js**: 14+ for web interface
- **Memory**: 4GB RAM minimum
- **Network**: Raw socket access for GOOSE

### **Dependencies**
```bash
# Ubuntu/Debian
sudo apt install docker.io docker-compose python3-tk nodejs npm
```

## 🛠️ Installation

### **1. Clone Repository**
```bash
git clone <repository-url>
cd "Virtual Substation/Cirtual Substation (30082025)"
```

### **2. Build System**
```bash
# Install web interface dependencies
cd web-interface && npm install && cd ..

# Build Docker containers
make build
```

### **3. Start System**
```bash
make start
```

### **4. Launch GUI Panels**
```bash
make gui
```

## 🎮 Usage

### **Protection Testing**
1. **Normal Operation**: Monitor baseline system (V=132kV, I=450A, F=50Hz)
2. **Overcurrent Test**: Set current >1000A via simulation panel
3. **Ground Fault Test**: Set fault current >300A
4. **Frequency Test**: Set frequency <48.5Hz
5. **Manual Trip**: Use protection relay panel

### **Communication Monitoring**
- **GOOSE Messages**: Monitor via circuit breaker panel logs
- **MMS Data**: View real-time updates in HMI/SCADA panel
- **System Status**: Check web interface dashboard

### **Manual Controls**
- **Trip Breaker**: Protection relay panel → "MANUAL TRIP"
- **Close Breaker**: Circuit breaker panel → "CLOSE"
- **Inject Fault**: Simulation panel → adjust parameters
- **Reset System**: Simulation panel → "RESET ALL"

## 🔧 Technical Details

### **IEC 61850 Data Model**
```
GenericIO/GGIO1/
├── AnIn1.mag.f    # Voltage (kV)
├── AnIn2.mag.f    # Current (A)
├── AnIn3.mag.f    # Frequency (Hz)
├── AnIn4.mag.f    # Fault Current (A)
├── SPCSO1.stVal   # Trip Command
├── SPCSO2.stVal   # Breaker Position
├── SPCSO3.stVal   # Fault Detected
└── SPCSO4.stVal   # Overcurrent Pickup
```

### **GOOSE Configuration**
- **Publisher**: Protection relay (AppId: 4096)
- **Subscriber**: Circuit breaker
- **Dataset**: Events3 (8 values with quality flags)
- **MAC Address**: 01:0c:cd:01:00:01

### **Container Ports**
- **3000**: Web interface
- **102**: Protection relay MMS server
- **103**: Circuit breaker MMS server
- **8080**: HMI/SCADA HTTP API
- **8081**: Circuit breaker HTTP API
- **8082**: Protection relay HTTP API

## 📊 Monitoring

### **Container Status**
```bash
docker ps
docker logs protection_relay_ied
docker logs circuit_breaker_ied
```

### **Network Traffic**
```bash
# Monitor GOOSE traffic
sudo tcpdump -i docker0 ether proto 0x88b8
```

## ⚠️ Limitations

### **What This System Is**
- Basic IEC 61850 protocol demonstration
- Educational training tool
- Containerized development environment
- Proof-of-concept implementation

### **What This System Is NOT**
- Production substation automation system
- Real-time electrical simulation
- Advanced protection relay modeling
- Performance testing platform
- Security-hardened implementation

### **Technical Constraints**
- **Simulation**: Parameter storage only (no physics)
- **Protection**: Hardcoded thresholds
- **Communication**: HTTP APIs for GUI (not pure IEC 61850)
- **Data**: No persistence or historical storage
- **Timing**: No precise time synchronization

## 🛑 Troubleshooting

### **Common Issues**

**Containers Won't Start**
```bash
# Check Docker permissions
sudo usermod -aG docker $USER
newgrp docker

# Check privileged mode
docker-compose down
docker-compose up -d
```

**GOOSE Not Working**
```bash
# Verify raw socket access
docker exec protection_relay_ied ls /sys/class/net/
# Should show eth0

# Check container capabilities
docker inspect protection_relay_ied | grep -i cap
```

**GUI Panels Not Opening**
```bash
# Install Tkinter
sudo apt install python3-tk

# Check display
echo $DISPLAY
```

**Web Interface Not Accessible**
```bash
# Check container status
docker logs substation_web_ui

# Restart web interface
docker restart substation_web_ui
```

## 🔄 Development

### **Build Commands**
```bash
make build          # Build all containers
make start          # Start system
make stop           # Stop system
make clean          # Clean Docker environment
make gui            # Launch GUI panels
```

### **File Structure**
```
├── src/                    # C source files (IEC 61850)
├── gui/                    # Python GUI panels
├── web-interface/          # Node.js server
├── config/                 # Docker configurations
├── libiec61850/           # IEC 61850 protocol library
├── scripts/               # Deployment scripts
└── docker-compose.yml     # Container orchestration
```

## 🎓 Educational Value

### **Learning Outcomes**
- IEC 61850 GOOSE and MMS protocols
- Basic protection system concepts
- Substation communication architecture
- Docker containerization
- Network protocol analysis

### **Suitable For**
- University courses on power systems
- IEC 61850 protocol training
- Substation automation basics
- Software development learning

## 📄 License

Educational use only. See LICENSE file for details.

---

**Note**: This is a simplified demonstration system for educational purposes. It implements basic IEC 61850 concepts but lacks the complexity, performance, and security features required for production substation automation systems.