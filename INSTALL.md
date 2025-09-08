# Installation Guide

## System Requirements

### Operating System
- **Linux**: Ubuntu 20.04+ (recommended)
- **macOS**: 10.15+ with Docker Desktop
- **Windows**: WSL2 with Docker Desktop

### Hardware Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Network**: Raw socket access for GOOSE (Linux containers need privileged mode)

## Step-by-Step Installation

### 1. Install Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y docker.io docker-compose python3-tk nodejs npm git wget

# Enable Docker service
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
newgrp docker
```

**macOS (with Homebrew):**
```bash
brew install docker docker-compose node python-tk git wget
```

**Windows:**
- Install Docker Desktop
- Install WSL2 with Ubuntu
- Run commands in WSL2 terminal

### 2. Download Project

**Option A: Git Clone (Recommended)**
```bash
git clone https://github.com/YOUR_USERNAME/virtual-substation.git
cd virtual-substation
```

**Option B: Download ZIP**
```bash
wget https://github.com/YOUR_USERNAME/virtual-substation/archive/refs/heads/main.zip
unzip main.zip
cd virtual-substation-main
```

**Option C: Direct Download**
```bash
# Download and extract in one command
wget -O - https://github.com/YOUR_USERNAME/virtual-substation/archive/refs/heads/main.tar.gz | tar -xz
cd virtual-substation-main
```

### 3. Setup Project
```bash
# Install web interface dependencies
cd web-interface
npm install
cd ..

# Make scripts executable
chmod +x scripts/*.sh
```

### 4. Build and Start
```bash
# Build all containers (takes 5-10 minutes)
make build

# Start the system
make start

# Wait 30 seconds for containers to initialize
sleep 30
```

### 5. Launch Interface
```bash
# Launch GUI panels (optional)
make gui
```

### 6. Verify Installation
Open these URLs in your browser:
- **Main Interface**: http://localhost:3000
- **HMI/SCADA**: http://localhost:8080
- **Protection Relay**: http://localhost:8082
- **Circuit Breaker**: http://localhost:8081

**Success indicators:**
- All 4 URLs respond
- Web interface shows system diagram
- GUI panels open (if launched)
- No error messages in terminal

## Quick Test

```bash
# Run automated test
make test-goose

# Expected output:
# ✅ GOOSE communication working
# ✅ Protection relay responding
# ✅ Circuit breaker responding
# ✅ All tests passed
```

## Troubleshooting

### Common Issues

**1. Docker Permission Denied**
```bash
sudo usermod -aG docker $USER
newgrp docker
# Then restart terminal
```

**2. Containers Won't Start**
```bash
# Check Docker status
sudo systemctl status docker

# Restart Docker
sudo systemctl restart docker

# Clean and rebuild
make clean
make build
```

**3. Port Already in Use**
```bash
# Find what's using the ports
sudo netstat -tulpn | grep -E ':(3000|8080|8081|8082)'

# Stop the system
make stop

# Kill processes if needed
sudo pkill -f "node.*3000"
```

**4. GUI Panels Won't Open**
```bash
# Install Tkinter
sudo apt install python3-tk

# Check display
echo $DISPLAY

# For SSH connections
ssh -X username@hostname
```

**5. Web Interface Not Loading**
```bash
# Check container logs
docker logs substation_web_ui

# Restart web interface
docker restart substation_web_ui

# Wait and try again
sleep 10
curl http://localhost:3000
```

### Getting Help

**Check System Status:**
```bash
# View all containers
docker ps -a

# Check logs
docker logs protection_relay_ied
docker logs circuit_breaker_ied
```

**Reset Everything:**
```bash
make stop
make clean
make build
make start
```

## Next Steps

### 1. Run Demo
```bash
# Automated demonstration
make demo
```

### 2. Manual Testing
```bash
# Launch GUI panels
make gui

# Test protection functions:
# - Open Simulation Control Panel
# - Set Current > 1000A
# - Watch circuit breaker trip
```

### 3. Learn More
- Read `ARCHITECTURE.md` for technical details
- Check `README.md` for usage examples
- See `docs/TRAINING.md` for learning exercises

## Advanced Configuration

### Production Deployment
```bash
# Secure production mode
make start-secure

# System monitoring
make monitor
```

### Development Mode
```bash
# Development setup
make dev-setup

# Run tests
make ci-test
```

### Network Configuration
The system uses two Docker networks:
- **Process Bus** (192.168.10.0/24): GOOSE communication
- **Station Bus** (192.168.20.0/24): MMS communication

### Environment Variables
- `SIMULATOR_HOST`: Web interface hostname
- `RELAY_HOST`: Protection relay hostname  
- `BREAKER_HOST`: Circuit breaker hostname
- `TEST_MODE`: Enable test quality flags

---

**Installation Complete!** 🎉

Your Virtual Substation Training System is ready to use.

**Quick Links:**
- Main Interface: http://localhost:3000
- Documentation: `README.md`
- Architecture: `ARCHITECTURE.md`
- Training Guide: `docs/TRAINING.md`