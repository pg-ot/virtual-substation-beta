# Virtual Substation Training System
# IEC 61850 Dual-Network Architecture Implementation

.PHONY: help build start start-nc stop clean install test gui

# Default target
help:
	@echo "Virtual Substation Training System"
	@echo "=================================="
	@echo ""
	@echo "Available targets:"
	@echo "  build    - Build all Docker containers"
	@echo "  start    - Start the complete system"
	@echo "  start-nc - Build (no-cache) and start all services"
	@echo "  stop     - Stop all services"
	@echo "  clean    - Clean Docker containers and images"
	@echo "  install  - Install system dependencies"
	@echo "  test     - Run system tests"
	@echo "  gui      - Launch GUI panels"
	@echo "  test-goose - Run GOOSE communication tests"
	@echo "  test-goose-full - Run comprehensive GOOSE tests"
	@echo "  test-goose-complete - Run complete manual test suite"
	@echo "  demo - Run automated GOOSE demonstration"
	@echo "  dev-setup - Setup development environment"
	@echo "  ci-test - Run CI test pipeline"
	@echo "  start-secure - Start with security hardening"
	@echo "  monitor - Real-time system monitoring"
	@echo ""

# Build all containers
build:
	@echo "Building Virtual Substation containers..."
	@./scripts/build.sh

# Start complete system
start:
	@echo "Starting Virtual Substation system..."
	@docker network prune -f
	@./scripts/start_all.sh

# Build without cache and start all services
start-nc:
	@echo "Rebuilding all services without cache..."
	COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose build --no-cache --pull
	@echo "Starting Virtual Substation system (fresh images)..."
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

# Test GOOSE communication
test-goose:
	@echo "🧪 Running GOOSE communication tests..."
	@bash scripts/test_goose_simple.sh

test-goose-full:
	@echo "🧪 Running comprehensive GOOSE tests..."
	@bash scripts/test_goose.sh

test-goose-complete:
	@echo "🧪 Running complete manual test suite..."
	@bash scripts/test_goose_complete.sh

demo:
	@echo "🎭 Running automated demo..."
	@bash scripts/demo-mode.sh

dev-setup:
	@echo "🔧 Setting up development environment..."
	@bash scripts/dev-setup.sh

ci-test:
	@echo "🧪 Running CI test suite..."
	@bash scripts/test-ci.sh

start-secure:
	@echo "🔒 Starting secure production mode..."
	@docker-compose -f docker-compose.secure.yml up -d

monitor:
	@echo "📊 Starting system monitoring..."
	@bash scripts/monitoring.sh
