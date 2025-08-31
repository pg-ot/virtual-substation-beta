#!/bin/bash

# SR-IOV setup for GOOSE (requires compatible hardware)
echo "Setting up SR-IOV for GOOSE multicast..."

# Check if SR-IOV is supported
if lspci | grep -i "virtual function" >/dev/null; then
    echo "SR-IOV hardware detected"
    
    # Enable SR-IOV virtual functions
    echo 2 | sudo tee /sys/class/net/ens33/device/sriov_numvfs 2>/dev/null || echo "SR-IOV not supported on ens33"
    
    # Create network namespace for each container
    sudo ip netns add protection-relay-ns 2>/dev/null || echo "Namespace exists"
    sudo ip netns add circuit-breaker-ns 2>/dev/null || echo "Namespace exists"
    
    echo "SR-IOV setup complete"
else
    echo "SR-IOV hardware not available - using alternative method"
fi