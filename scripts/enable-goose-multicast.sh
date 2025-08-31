#!/bin/bash

echo "Enabling GOOSE multicast on Docker bridge networks..."

# Wait for bridges to be created
sleep 2

# Configure process bus bridge for GOOSE
if ip link show goose-process >/dev/null 2>&1; then
    echo "Configuring goose-process bridge..."
    sudo ip link set goose-process promisc on
    echo 0 | sudo tee /sys/class/net/goose-process/bridge/multicast_snooping >/dev/null 2>&1
    echo 1 | sudo tee /sys/class/net/goose-process/bridge/multicast_querier >/dev/null 2>&1
    sudo iptables -I FORWARD -i goose-process -o goose-process -j ACCEPT 2>/dev/null
    echo "✅ goose-process bridge configured"
else
    echo "❌ goose-process bridge not found"
fi

# Configure station bus bridge for GOOSE
if ip link show goose-station >/dev/null 2>&1; then
    echo "Configuring goose-station bridge..."
    sudo ip link set goose-station promisc on
    echo 0 | sudo tee /sys/class/net/goose-station/bridge/multicast_snooping >/dev/null 2>&1
    echo 1 | sudo tee /sys/class/net/goose-station/bridge/multicast_querier >/dev/null 2>&1
    sudo iptables -I FORWARD -i goose-station -o goose-station -j ACCEPT 2>/dev/null
    echo "✅ goose-station bridge configured"
else
    echo "❌ goose-station bridge not found"
fi

echo "GOOSE multicast configuration complete"