# Virtual Substation Installation Guide
## Fresh Ubuntu System Setup

### Prerequisites
- Fresh Ubuntu 20.04+ system
- Internet connection
- User with sudo privileges

---

## Step 1: Update System
```bash
sudo apt update
sudo apt upgrade -y
```

## Step 2: Install Docker & Docker Compose
```bash
# Install Docker
sudo apt install -y docker.io docker-compose

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER

# Apply group changes (logout/login or run)
newgrp docker
```

## Step 3: Install Build Tools
```bash
sudo apt install -y build-essential cmake git gcc
```

## Step 4: Install Python Dependencies
```bash
sudo apt install -y python3 python3-pip python3-tk
pip3 install requests
```

## Step 5: Install Node.js (for Web Interface)
```bash
sudo apt install -y nodejs npm
```

## Step 6: Clone/Copy Project
```bash
# If using git
git clone <repository-url>
cd "Virtual Substation/Cirtual Substation"

# Or copy project files to desired directory
```

## Step 7: Set File Permissions
```bash
chmod +x build.sh start_all.sh stop_all.sh
mkdir -p logs
```

## Step 8: Install Web Interface Dependencies
```bash
cd web-interface
npm install
cd ..
```

## Step 9: Configure Network Interfaces (If Needed)
```bash
# Check your system's network interface
ip addr show

# If your system uses interface other than 'eth0' inside containers,
# update docker-compose.yml:
# Change GOOSE_INTERFACE=eth0 to your interface name

# Most systems work with default 'eth0' in containers
```

## Step 10: Build Docker Images
```bash
./build.sh
```

## Step 11: Start System
```bash
./start_all.sh
```

---

## Verification Commands

### Check Docker Status
```bash
docker --version
docker-compose --version
docker ps
```

### Check Python Dependencies
```bash
python3 -c "import tkinter, requests; print('Python OK')"
```

### Check Web Interface
```bash
curl http://localhost:3000/api/simulation-data
```

### Check Container Logs
```bash
docker logs protection_relay_ied --tail 10
docker logs circuit_breaker_ied --tail 10
```

---

## System Access

- **Web Interface**: http://localhost:3000
- **SCADA Interface**: http://localhost:3000/scada
- **MMS Server**: Port 102 (Protection Relay)
- **GUI Panels**: Auto-launched by start_all.sh

---

## Troubleshooting

### Docker Permission Issues
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Container Not Starting
```bash
docker-compose down
docker-compose up -d
```

### Web Interface Not Accessible
```bash
docker restart substation_web_ui
```

### GUI Panels Not Opening
```bash
# Install tkinter if missing
sudo apt install python3-tk

# Check display
echo $DISPLAY
```

### Interface Configuration Issues
```bash
# Check container interfaces
docker exec protection_relay_ied ls /sys/class/net/

# If containers don't have eth0, update docker-compose.yml:
# Change GOOSE_INTERFACE=eth0 to correct interface

# Common container interfaces: eth0, eth1
```

---

## Stop System
```bash
./stop_all.sh
```

## Complete Cleanup
```bash
docker-compose down
docker system prune -f
```

---

## System Requirements
- **CPU**: Multi-core recommended
- **RAM**: 4GB minimum, 8GB recommended  
- **Storage**: 2GB free space
- **Network**: Docker bridge networking
- **Display**: GUI environment for panels