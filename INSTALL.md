# Installation Guide

## System Requirements

### Operating System
- **Linux**: Ubuntu 20.04+ (recommended)
- **macOS**: 10.15+ with Docker Desktop
- **Windows**: WSL2 with Docker Desktop

### Software Dependencies
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y docker.io docker-compose python3-tk nodejs npm git

# macOS (with Homebrew)
brew install docker docker-compose node python-tk

# Enable Docker service (Linux)
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
newgrp docker
```

### Hardware Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Network**: Raw socket access for GOOSE (Linux containers need privileged mode)

## Quick Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd "Virtual Substation/Cirtual Substation (30082025)"
```

### 2. Install Web Dependencies
```bash
cd web-interface
npm install
cd ..
```

### 3. Build and Start System
```bash
# Build all containers
make build

# Start the system
make start

# Launch GUI panels
make gui
```

### 4. Verify Installation
- **Web Interface**: http://localhost:3000
- **HMI/SCADA**: http://localhost:8080
- **Protection Relay API**: http://localhost:8082
- **Circuit Breaker API**: http://localhost:8081

## Troubleshooting

### Docker Permission Issues
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### GOOSE Communication Issues
```bash
# Verify privileged containers are running
docker ps --format "table {{.Names}}\t{{.Status}}"

# Check container capabilities
docker inspect protection_relay_ied_ln | grep -i cap
```

### GUI Panel Issues
```bash
# Install Tkinter (Ubuntu/Debian)
sudo apt install python3-tk

# Check display variable
echo $DISPLAY
```

### Port Conflicts
```bash
# Check if ports are in use
netstat -tulpn | grep -E ':(3000|8080|8081|8082|102|103)'

# Stop conflicting services
make stop
```

## Advanced Configuration

### Environment Variables
- `SIMULATOR_HOST`: Web interface hostname (default: substation_web_ui)
- `RELAY_HOST`: Protection relay hostname (default: protection_relay_ied_ln)
- `BREAKER_HOST`: Circuit breaker hostname (default: circuit_breaker_ied_ln)
- `TEST_MODE`: Enable test quality flags (default: false)

### Network Configuration
The system uses two Docker networks:
- **Process Bus** (192.168.10.0/24): GOOSE communication
- **Station Bus** (192.168.20.0/24): MMS communication

### ICD Models
The system uses IEC 61850 ICD files for data model generation:
- `config/models/ln_ied.icd` - Protection relay model
- `config/models/ln_breaker.icd` - Circuit breaker model