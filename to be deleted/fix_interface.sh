#!/bin/bash

echo "🔧 Fixing network interface detection..."

# Stop containers
echo "password" | sudo -S docker-compose down

# Update docker-compose to use auto-detection
cat > docker-compose.yml << 'EOF'
services:
  protection-relay:
    build:
      context: .
      dockerfile: Dockerfile.protection-relay
    container_name: protection_relay_ied
    networks:
      - process_bus
      - station_bus
    cap_add:
      - NET_RAW
    environment:
      - MMS_PORT=102
    volumes:
      - ./logs:/app/logs

  circuit-breaker:
    build:
      context: .
      dockerfile: Dockerfile.circuit-breaker
    container_name: circuit_breaker_ied
    networks:
      - process_bus
    cap_add:
      - NET_RAW
    depends_on:
      - protection-relay
    volumes:
      - ./logs:/app/logs

  hmi-scada:
    build:
      context: .
      dockerfile: Dockerfile.hmi-scada
    container_name: hmi_scada
    networks:
      - station_bus
    environment:
      - RELAY_HOST=protection_relay_ied
      - MMS_PORT=102
    depends_on:
      - protection-relay
    volumes:
      - ./logs:/app/logs

  web-interface:
    build:
      context: ./web-interface
    container_name: substation_web_ui
    ports:
      - "3000:3000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    depends_on:
      - protection-relay
      - circuit-breaker

networks:
  process_bus:
    driver: bridge
    ipam:
      config:
        - subnet: 192.168.10.0/24
  station_bus:
    driver: bridge
    ipam:
      config:
        - subnet: 192.168.20.0/24
EOF

# Add interface detection to protection relay
cat > src/get_interface.c << 'EOF'
#include <stdio.h>
#include <string.h>
#include <ifaddrs.h>
#include <netinet/in.h>
#include <arpa/inet.h>

char* get_process_bus_interface() {
    struct ifaddrs *ifaddr, *ifa;
    static char interface_name[16] = "eth0";
    
    if (getifaddrs(&ifaddr) == -1) {
        return interface_name;
    }
    
    for (ifa = ifaddr; ifa != NULL; ifa = ifa->ifa_next) {
        if (ifa->ifa_addr == NULL) continue;
        
        if (ifa->ifa_addr->sa_family == AF_INET) {
            struct sockaddr_in* addr = (struct sockaddr_in*)ifa->ifa_addr;
            char ip_str[INET_ADDRSTRLEN];
            inet_ntop(AF_INET, &addr->sin_addr, ip_str, INET_ADDRSTRLEN);
            
            // Check if this is the process bus network (192.168.10.x)
            if (strncmp(ip_str, "192.168.10.", 11) == 0) {
                strncpy(interface_name, ifa->ifa_name, sizeof(interface_name)-1);
                interface_name[sizeof(interface_name)-1] = '\0';
                break;
            }
        }
    }
    
    freeifaddrs(ifaddr);
    return interface_name;
}
EOF

# Update protection relay to use auto-detection
sed -i 's/char\* interface = "eth0";/char* interface = get_process_bus_interface();/' src/protection-relay.c
sed -i '1i#include "get_interface.c"' src/protection-relay.c

# Update circuit breaker to use auto-detection  
sed -i 's/char\* interface = "eth0";/char* interface = get_process_bus_interface();/' src/circuit-breaker.c
sed -i '1i#include "get_interface.c"' src/circuit-breaker.c

# Rebuild containers
echo "🔨 Rebuilding containers with interface auto-detection..."
./build.sh

# Start system
echo "🚀 Starting fixed system..."
echo "password" | sudo -S docker-compose up -d

echo "✅ Interface detection fixed!"
echo "Containers should now auto-detect correct network interfaces"