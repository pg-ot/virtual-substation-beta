# System Architecture

## Overview
The Virtual Substation Training System implements IEC 61850 protocol communication using a containerized microservices architecture with dual network topology.

## Service Architecture

### Services
```
┌─────────────────┐    GOOSE     ┌──────────────────┐    GOOSE     ┌─────────────────┐
│ Web Interface   │◄────────────►│ Protection       │◄────────────►│ Circuit Breaker │
│ (Node.js)       │   HTTP       │ Relay LN (C)     │   AppId:1000 │ LN (C)          │
│ Port: 3000      │              │ MMS: 102         │              │ MMS: 103        │
└─────────────────┘              └──────────────────┘              └─────────────────┘
        │                                 │                                 │
        │                    MMS          │                                 │
        └─────────────────────────────────┼─────────────────────────────────┘
                                          │
                                 ┌─────────────────┐
                                 │ HMI/SCADA LN    │
                                 │ MMS Client      │
                                 │ Port: 8080      │
                                 └─────────────────┘
```

All services use IEC 61850 Logical Node (LN) based data models generated from ICD files.

## Network Topology

### Process Bus (192.168.10.0/24)
- **Purpose**: GOOSE communication between IEDs
- **Protocol**: IEC 61850-8-1 GOOSE
- **Participants**: Protection Relay ↔ Circuit Breaker

### Station Bus (192.168.20.0/24)  
- **Purpose**: MMS client/server communication
- **Protocol**: IEC 61850-8-1 MMS
- **Participants**: HMI/SCADA ↔ Protection Relay, Circuit Breaker

## Data Models

### Protection Relay (LN-based)
```
LD0/
├── LLN0/                    # Logical Node Zero
│   ├── Events (DataSet)     # GOOSE dataset
│   └── EventsRCB (RCB)      # Report Control Block
├── PTRC1/                   # Protection Trip Conditioning
│   └── Tr (SPS)             # Trip signal
├── PTOC1/                   # Time Overcurrent Protection  
│   ├── Op (SPS)             # Operation signal
│   └── Str (SPS)            # Start signal
├── XCBR1/                   # Circuit Breaker
│   └── Pos (DPC)            # Position
└── MMXU1/                   # Measurements
    ├── PhV (MV)             # Phase voltage
    ├── Amp (MV)             # Current
    └── Hz (MV)              # Frequency
```

### Circuit Breaker (LN-based)
```
LD0/
├── LLN0/                    # Logical Node Zero
│   ├── BrkStatus (DataSet)  # GOOSE dataset  
│   └── gcbStatus (GoCB)     # GOOSE Control Block
├── XCBR1/                   # Circuit Breaker
│   └── Pos (DPC)            # Position (Dbpos)
└── CSWI1/                   # Switch Controller
    └── Op (SPC)             # Operate
```

## Communication Protocols

### GOOSE Messages
- **Relay → Breaker**: Trip commands, protection status
  - GoCbRef: `"GenericIO/LLN0$GO$gcbEvents"`
  - AppId: 1000, MAC: 01:0c:cd:01:00:01
- **Breaker → Relay**: Position feedback
  - GoCbRef: `"LD0/LLN0$GO$gcbStatus"`  
  - AppId: 1001, MAC: 01:0c:cd:01:00:02

### MMS Services
- **Read**: Analog measurements, digital status
- **Write**: Control commands (trip/close)
- **Reports**: Real-time data updates via URCB

### HTTP APIs
- **Protection Relay**: Port 8082 (status, control)
- **Circuit Breaker**: Port 8081 (status, control)  
- **HMI/SCADA**: Port 8080 (aggregated data, control)
- **Web Interface**: Port 3000 (simulation, monitoring)

## File Structure
```
├── src/                     # C source files
│   ├── protection-relay.c   # Protection relay implementation
│   ├── circuit-breaker.c    # Circuit breaker implementation
│   └── hmi-scada.c         # HMI/SCADA client
├── config/                  # Configuration files
│   ├── models/             # ICD data models
│   └── Dockerfile.*        # Container definitions
├── gui/                    # Python GUI panels
├── web-interface/          # Node.js web server
├── scripts/               # Deployment scripts
└── libiec61850/           # IEC 61850 protocol library
```

## Security Considerations
- **Network Isolation**: Services run in isolated Docker networks
- **Privileged Containers**: Required for raw socket GOOSE access
- **No Authentication**: Educational system - not production-ready
- **Local Access Only**: Bound to localhost by default