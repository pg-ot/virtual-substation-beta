# IEC 61850 GOOSE Training Guide

## 🎯 Learning Objectives
- Understand IEC 61850 GOOSE protocol
- Experience substation automation
- Test protection relay functions

## 🚀 Quick Start
```bash
make start          # Start system
make demo           # Run automated demo
make test-goose     # Test GOOSE functions
```

## 📚 Training Modules

### Module 1: System Overview
- **Duration**: 15 minutes
- **Objective**: Understand architecture
- **Commands**: `make start`, browse http://localhost:3000

### Module 2: GOOSE Communication
- **Duration**: 20 minutes  
- **Objective**: Test GOOSE messages
- **Commands**: `make test-goose-complete`

### Module 3: Protection Functions
- **Duration**: 25 minutes
- **Objective**: Test protection logic
- **Commands**: Manual operations via APIs

## 🧪 Exercises

### Exercise 1: Manual Operations
```bash
# Close breaker
curl -X POST http://localhost:8081/close

# Trip relay  
curl -X POST http://localhost:8082/trip

# Check GOOSE communication
curl -s http://localhost:8082 | jq '{txCount,rxCount}'
```

### Exercise 2: Automated Testing
```bash
make test-goose-complete
```

## 📊 Assessment
- GOOSE message exchange: ✅/❌
- Protection functions: ✅/❌  
- System understanding: ✅/❌