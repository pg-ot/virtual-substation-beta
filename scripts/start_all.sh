#!/bin/bash

cd "$(dirname "$0")"/.. || exit 1

echo "🚀 Starting Virtual Substation System..."

# Start Docker containers
echo "📦 Starting Docker containers..."
docker-compose up -d

# Configure GOOSE multicast on bridge networks
echo "🔧 Configuring GOOSE multicast..."
chmod +x scripts/enable-goose-multicast.sh
./scripts/enable-goose-multicast.sh

# Wait for containers to be ready
echo "⏳ Waiting for containers to initialize..."
sleep 5

# Check if containers are running
echo "🔍 Checking container status..."
docker ps --format "table {{.Names}}\t{{.Status}}"

# Launch Tkinter GUI panels
echo "🖥️ Launching IED GUI panels..."

# Launch panels in background
python3 gui/protection_relay_panel.py &
RELAY_PID=$!

python3 gui/circuit_breaker_panel.py &
BREAKER_PID=$!

python3 gui/hmi_scada_panel.py &
HMI_PID=$!

python3 gui/simulation_control_panel.py &
SIM_PID=$!

# Store PIDs for cleanup
echo $RELAY_PID > /tmp/relay_pid
echo $BREAKER_PID > /tmp/breaker_pid  
echo $HMI_PID > /tmp/hmi_pid
echo $SIM_PID > /tmp/sim_pid

echo ""
echo "✅ Virtual Substation System Started!"
echo ""
echo "🌐 Web Interfaces:"
echo "   Single Line Diagram: http://localhost:3000"
echo "   SCADA Interface:      http://localhost:3000/scada"
echo ""
echo "🖥️ GUI Panels:"
echo "   - Protection Relay Panel"
echo "   - Circuit Breaker Panel" 
echo "   - HMI/SCADA Panel"
echo "   - Simulation Control Center"
echo ""
echo "📊 System Status:"
docker ps --format "   {{.Names}}: {{.Status}}"
echo ""
echo "To stop everything: ./stop_all.sh"