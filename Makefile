# Virtual Substation Training System
# IEC 61850 Dual-Network Architecture Implementation

.PHONY: help build start start-nc start-ln start-ln-nc stop clean install test gui

# Default target
help:
	@echo "Virtual Substation Training System"
	@echo "=================================="
	@echo ""
	@echo "Available targets:"
	@echo "  build    - Build all Docker containers"
	@echo "  start    - Start the complete system"
	@echo "  start-nc - Build (no-cache) and start all services"
	@echo "  start-ln - Start LN-only IEDs + HMI + web UI (no rebuild)"
	@echo "  start-ln-nc - Build (no-cache) and start LN-only IEDs"
	@echo "  stop     - Stop all services"
	@echo "  clean    - Clean Docker containers and images"
	@echo "  install  - Install system dependencies"
	@echo "  test     - Run system tests"
	@echo "  gui      - Launch GUI panels"
	@echo ""

# Build all containers
build:
	@echo "Building Virtual Substation containers..."
	@./scripts/build.sh

# Start complete system
start:
	@echo "Starting Virtual Substation system..."
	@./scripts/start_all.sh

# Build without cache and start all services
start-nc:
	@echo "Rebuilding all services without cache..."
	COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose build --no-cache --pull
	@echo "Starting Virtual Substation system (fresh images)..."
	@./scripts/start_all.sh

# Start LN-only services without rebuild (IEDs + HMI + web UI)
start-ln:
	@echo "Starting LN-only IEDs and HMI..."
	docker-compose up -d protection-relay-ln circuit-breaker-ln hmi-scada-ln
	@echo "Starting web interface without default IED dependencies..."
	docker-compose up -d --no-deps web-interface
	@echo "All LN services started."

# Build without cache and start only LN-only IED variants
start-ln-nc:
	@echo "Rebuilding LN-only IED services without cache..."
	COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose build --no-cache --pull protection-relay-ln circuit-breaker-ln hmi-scada-ln
	@echo "Starting LN-only services (IEDs + HMI)..."
	docker-compose up -d protection-relay-ln circuit-breaker-ln hmi-scada-ln

# Stop all services
stop:
	@echo "Stopping Virtual Substation system..."
	@./scripts/stop_all.sh

# Clean Docker environment
clean:
	@echo "Cleaning Docker environment..."
	docker-compose down --rmi all --volumes --remove-orphans
	docker system prune -f

# Install dependencies
install:
	@echo "Installing system dependencies..."
	@echo "See docs/INSTALL.md for detailed instructions"

# Run tests
test:
	@echo "Running system tests..."
	@echo "Manual testing: Use GUI panels to test functionality"

# Launch GUI panels
gui:
	@echo "Launching GUI panels..."
	cd gui && python3 simulation_control_panel.py &
	cd gui && python3 protection_relay_panel.py &
	cd gui && python3 circuit_breaker_panel.py &
	cd gui && python3 hmi_scada_panel.py &
