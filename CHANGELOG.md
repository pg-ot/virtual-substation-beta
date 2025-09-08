# Changelog

## [2.0.0] - 2025-01-XX

### Major Changes
- **BREAKING**: Migrated to ICD-based Logical Node (LN) architecture
- **BREAKING**: Removed legacy GGIO-based services completely
- **BREAKING**: All services now use LN-based IEC 61850 data models

### Added
- ICD-based data models (ln_ied.icd, ln_breaker.icd)
- Proper IEC 61850 Logical Node structure (PTRC1, PTOC1, XCBR1, MMXU1)
- GOOSE communication with correct GoCbRef mapping
- Automatic model generation from ICD files
- Network aliases for seamless service replacement

### Fixed
- GOOSE communication between protection relay and circuit breaker
- Port conflicts between LN and non-LN services
- HMI/SCADA offline status issues
- MMS data model consistency

### Technical Details
- Protection Relay: Uses LD0 logical device with proper LN structure
- Circuit Breaker: Subscribes to "GenericIO/LLN0$GO$gcbEvents" GOOSE messages
- HMI/SCADA: Connects to LN-based services via network aliases
- Web Interface: Compatible with both architectures

## [1.0.0] - 2024-XX-XX

### Initial Release
- Basic IEC 61850 protocol demonstration
- GGIO-based data model implementation
- Docker containerization
- Python GUI panels
- Web-based monitoring interface