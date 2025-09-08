#!/bin/bash

cd "$(dirname "$0")"/.. || exit 1

echo "🛑 Stopping Virtual Substation System..."

# Stop GUI panels
echo "🖥️ Stopping GUI panels..."
if [ -f /tmp/relay_pid ]; then
    kill $(cat /tmp/relay_pid) 2>/dev/null
    rm /tmp/relay_pid
    echo "   ✓ Protection Relay Panel stopped"
fi

if [ -f /tmp/breaker_pid ]; then
    kill $(cat /tmp/breaker_pid) 2>/dev/null
    rm /tmp/breaker_pid
    echo "   ✓ Circuit Breaker Panel stopped"
fi

if [ -f /tmp/hmi_pid ]; then
    kill $(cat /tmp/hmi_pid) 2>/dev/null
    rm /tmp/hmi_pid
    echo "   ✓ HMI/SCADA Panel stopped"
fi

if [ -f /tmp/sim_pid ]; then
    kill $(cat /tmp/sim_pid) 2>/dev/null
    rm /tmp/sim_pid
    echo "   ✓ Simulation Control Panel stopped"
fi

# Kill any remaining Python GUI processes
pkill -f "python3.*_panel.py" 2>/dev/null

# Stop Docker containers
echo "📦 Stopping Docker containers..."
docker compose down

echo ""
echo "✅ Virtual Substation System Stopped!"
echo ""
echo "📊 Final Status:"
docker ps --format "   {{.Names}}: {{.Status}}" | grep -E "(protection|circuit|substation)" || echo "   All containers stopped"