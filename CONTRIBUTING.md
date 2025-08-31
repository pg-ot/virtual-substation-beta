# Contributing to Virtual Substation Training System

## Development Setup

### Prerequisites
- Docker & Docker Compose
- Python 3.8+
- Node.js 14+
- Git

### Quick Start
```bash
git clone <repository-url>
cd virtual-substation
make install
make build
make start
```

## Project Structure

```
virtual-substation/
├── src/                    # Core IED implementations
├── gui/                    # Training interface panels
├── web-interface/          # REST API server
├── config/                 # Docker configurations
├── scripts/                # Build and deployment scripts
├── docs/                   # Documentation
├── libiec61850/           # IEC 61850 protocol library
├── docker-compose.yml     # Container orchestration
└── Makefile              # Build automation
```

## Development Workflow

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/your-feature`
3. **Make changes** following coding standards
4. **Test locally**: `make test`
5. **Commit changes**: `git commit -m "feat: description"`
6. **Push branch**: `git push origin feature/your-feature`
7. **Create Pull Request**

## Coding Standards

### C Code (IED Implementation)
- Follow IEC 61850 naming conventions
- Use descriptive variable names
- Add comments for complex logic
- Test GOOSE/MMS communication

### Python Code (GUI Panels)
- Follow PEP 8 style guide
- Use type hints where appropriate
- Add docstrings for functions
- Handle exceptions gracefully

### Docker
- Use multi-stage builds
- Minimize image size
- Document exposed ports
- Use health checks

## Testing

### Manual Testing
```bash
make start
make gui
# Test scenarios using GUI panels
```

### Integration Testing
- Test GOOSE communication between IEDs
- Verify MMS server functionality
- Check GUI panel updates
- Validate protection logic

## Commit Message Format

Use conventional commits:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Test additions/changes

## Pull Request Guidelines

- Provide clear description of changes
- Include testing instructions
- Update documentation if needed
- Ensure all containers build successfully
- Test GUI functionality

## Issues and Bug Reports

When reporting issues:
1. Describe the problem clearly
2. Include steps to reproduce
3. Provide system information
4. Include relevant logs
5. Suggest potential solutions

## License

This project is licensed under the terms specified in the main repository.