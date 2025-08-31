#!/bin/bash

# Setup custom bridge for GOOSE multicast support
echo "Setting up GOOSE-enabled bridge network..."

# Create custom bridge
docker network create \
  --driver=bridge \
  --subnet=192.168.100.0/24 \
  --opt com.docker.network.bridge.name=goose-br \
  --opt com.docker.network.bridge.enable_icc=true \
  --opt com.docker.network.bridge.enable_ip_masquerade=false \
  goose_network 2>/dev/null || echo "Network exists"

# Enable promiscuous mode on bridge
sudo ip link set goose-br promisc on 2>/dev/null || echo "Bridge not ready yet"

# Allow multicast traffic
sudo iptables -I FORWARD -i goose-br -o goose-br -j ACCEPT 2>/dev/null || echo "iptables rule exists"

# Enable multicast on bridge
echo 1 | sudo tee /sys/class/net/goose-br/bridge/multicast_querier 2>/dev/null || echo "Bridge not ready"
echo 0 | sudo tee /sys/class/net/goose-br/bridge/multicast_snooping 2>/dev/null || echo "Bridge not ready"

echo "GOOSE bridge setup complete"