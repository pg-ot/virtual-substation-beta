#!/bin/bash

echo "Enabling GOOSE multicast on Docker bridge networks..."

sleep 2

get_bridge_name() {
  local net_name="$1"
  # Try to get explicit bridge name option
  local br
  br=$(docker network inspect "$net_name" -f '{{ index .Options "com.docker.network.bridge.name"}}' 2>/dev/null)
  if [ -n "$br" ] && ip link show "$br" >/dev/null 2>&1; then
    echo "$br"; return 0;
  fi
  # Fallback to default br-<id[:12]>
  local id
  id=$(docker network inspect "$net_name" -f '{{.Id}}' 2>/dev/null | cut -c1-12)
  if [ -n "$id" ] && ip link show "br-$id" >/dev/null 2>&1; then
    echo "br-$id"; return 0;
  fi
  return 1
}

configure_bridge() {
  local br="$1"
  echo "Configuring $br for multicast..."
  sudo ip link set "$br" promisc on 2>/dev/null || true
  echo 0 | sudo tee "/sys/class/net/$br/bridge/multicast_snooping" >/dev/null 2>&1 || true
  echo 1 | sudo tee "/sys/class/net/$br/bridge/multicast_querier" >/dev/null 2>&1 || true
  sudo iptables -I FORWARD -i "$br" -o "$br" -j ACCEPT 2>/dev/null || true
  echo "✅ $br configured"
}

PROC_NET="$(docker network ls --format '{{.Name}}' | grep -m1 process_bus || true)"
STAT_NET="$(docker network ls --format '{{.Name}}' | grep -m1 station_bus || true)"

if [ -n "$PROC_NET" ]; then
  BR_PROC=$(get_bridge_name "$PROC_NET")
  if [ -n "$BR_PROC" ]; then configure_bridge "$BR_PROC"; else echo "❌ process_bus bridge not found"; fi
else
  echo "❌ process_bus network not found"
fi

if [ -n "$STAT_NET" ]; then
  BR_STAT=$(get_bridge_name "$STAT_NET")
  if [ -n "$BR_STAT" ]; then configure_bridge "$BR_STAT"; else echo "❌ station_bus bridge not found"; fi
else
  echo "❌ station_bus network not found"
fi

echo "GOOSE multicast configuration complete"
