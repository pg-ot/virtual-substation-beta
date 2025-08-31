# Virtual Substation Training System
# IEC 61850 Dual-Network Architecture Implementation

.PHONY: help build start stop clean install test

# Default target
help:
	@echo "Virtual Substation Training System"
	@echo "=================================="
	@echo ""
	@echo "Available targets:"
	@echo "  build    - Build all Docker containers"
	@echo "  start    - Start the complete system"
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