# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2024-01-15

### Added

#### 🚀 New Features
- **Terminal User Interface (TUI)**: Complete terminal interface with Rich-based UI components
  - Interactive chat sessions with local and remote LLMs
  - Session management and persistence
  - Configuration management with theming support
  - Keyboard shortcuts and intuitive navigation
- **OpenAI Agents SDK Integration**: Advanced agent capabilities with tool calling
  - Enhanced tool definitions for literacy coaching
  - Vector store integration for RAG
  - Retrieval-augmented generation
  - Safe key management with encryption
- **Vector Store**: Full-featured vector database for embeddings
  - Cosine similarity search
  - Metadata filtering
  - Persistent storage with backup/restore
  - Performance optimizations
- **Enhanced Security**: Comprehensive security framework
  - Encrypted API key storage
  - Environment-based configuration
  - Security scanning and validation
  - Secure defaults and best practices

#### 🧪 Testing & Quality
- **Comprehensive Test Suite**: Multi-layered testing strategy
  - Unit tests with high coverage (>85%)
  - Integration tests for service interaction
  - End-to-end tests for complete workflows
  - Property-based tests with Hypothesis
  - Performance and load testing
  - Security testing framework
- **Code Quality Tools**: Automated quality enforcement
  - Ruff linting with custom rules
  - Black code formatting
  - isort import organization
  - MyPy type checking
  - Bandit security scanning
  - Pre-commit hooks
- **CI/CD Pipeline**: Complete automation pipeline
  - GitHub Actions workflow
  - Multi-Python version testing
  - Quality gates and validation
  - Security vulnerability scanning
  - Docker image building and testing
  - SBOM generation

#### 🐳 Production Infrastructure
- **Multi-stage Docker Builds**: Optimized production images
  - Slim runtime images with security
  - Non-root container execution
  - Health checks and monitoring
  - Cache mounts for performance
- **Production Docker Compose**: Complete production stack
  - Nginx reverse proxy with SSL
  - Monitoring with Prometheus/Grafana
  - Centralized logging with Loki
  - Log shipping with Promtail
- **Observability**: Comprehensive monitoring
  - Service health endpoints
  - Metrics collection
  - Log aggregation
  - Alerting and dashboards

#### 📚 Documentation
- **API Reference**: Complete API documentation
  - All endpoints with examples
  - Request/response schemas
  - Authentication guide
  - SDK examples in Python and JavaScript
- **Operational Runbooks**: Production operations guide
  - Service management procedures
  - Troubleshooting guides
  - Backup and recovery
  - Security operations
  - Performance monitoring
- **Contributing Guide**: Developer onboarding
  - Development environment setup
  - Code standards and guidelines
  - Testing requirements
  - Pull request process

### Changed

#### 🔧 Architecture Improvements
- **Modular Design**: Enhanced service separation
  - Clear module boundaries
  - Dependency injection
  - Configuration management
  - Error handling improvements
- **Performance Optimizations**:
  - Caching for embeddings and TTS
  - Database query optimization
  - Memory usage improvements
  - Concurrent request handling
- **Security Hardening**:
  - Input validation and sanitization
  - SQL injection prevention
  - XSS protection
  - Secure file handling

#### 🛠️ Development Experience
- **Enhanced Tooling**: Modern development workflow
  - uv for fast package management
  - hatch for build management
  - tox for testing environments
  - Rich for beautiful CLI output
- **Environment Management**: Reproducible environments
  - Locked dependencies with uv.lock
  - Multiple Python version support
  - Virtual environment management
  - Development and production parity

### Fixed

#### 🐛 Bug Fixes
- **Service Communication**: Improved inter-service reliability
- **Database Handling**: Better error handling and recovery
- **File Operations**: Robust file I/O with proper encoding
- **Memory Management**: Fixed memory leaks in long-running services
- **Error Reporting**: Enhanced error messages and logging

#### 🔒 Security Fixes
- **Key Management**: Secure API key handling
- **Input Validation**: Comprehensive input sanitization
- **File Permissions**: Proper file access controls
- **Dependency Security**: Updated vulnerable dependencies

### Removed

#### 🗑️ Cleanup
- **Legacy Code**: Removed deprecated functionality

## [1.2.0] - 2025-09-30

### Added

- Mock mode for offline usage via `LITCOACH_MOCK`, with deterministic stubs for transcription, TTS, chat, and embeddings.
- Gateway mock short-circuits for agent and assessment endpoints.
- `.env.example` for safe configuration bootstrapping.
- CI (GitHub Actions) and release workflow (tests, PyPI, Docker) with secrets-driven publishing.
- Developer tooling: `Makefile`, `requirements-test.txt`, and `scripts/release.sh`.
- README logo display and mock-compose quickstart.

### Changed

- Bumped version to `1.2.0`.

### Fixed

- Improved local smoke-testability without requiring installed coverage plugins or external services.

- **Dead Code**: Eliminated unused code paths
- **Old Dependencies**: Updated outdated packages
- **Redundant Files**: Cleaned up temporary and build artifacts

### Deprecated

#### ⚠️ Deprecations
- **Old CLI Interface**: Legacy command-line interface (use new TUI)
- **Direct Database Access**: Direct SQLite access (use service APIs)
- **Plain Text Configuration**: Unencrypted configuration files

## [1.0.0] - 2023-12-01

### Added

- **Initial Release**: Core literacy coaching functionality
  - Voice-first AI tutoring with OpenAI Whisper and TTS
  - Reading fluency assessment (WCPM, accuracy)
  - Writing feedback with rubric scoring
  - Leveled text search and RAG
  - Teacher dashboard and analytics
  - Docker containerization
  - Basic testing framework

## Development Roadmap

### Upcoming Features (v1.2.0)

#### 🎯 Planned Enhancements
- **Multi-language Support**: Support for additional languages
- **Advanced Analytics**: Enhanced learning analytics and insights
- **Mobile Application**: Native mobile apps for iOS and Android
- **Offline Mode**: Local-only operation without internet
- **Custom Models**: Support for fine-tuned models
- **Real-time Collaboration**: Multi-user sessions

#### 🔧 Technical Improvements
- **Database Optimization**: Migration to PostgreSQL for production
- **Horizontal Scaling**: Kubernetes deployment support
- **Advanced Caching**: Redis integration for performance
- **Message Queue**: Async processing with RabbitMQ
- **API Rate Limiting**: Advanced rate limiting and quotas

### Long-term Vision (v2.0.0)

#### 🚀 Major Features
- **Adaptive Learning**: AI-powered personalized learning paths
- **Multi-modal Input**: Support for images, video, and other media
- **Peer Learning**: Student collaboration features
- **Parental Dashboard**: Comprehensive parent portal
- **Curriculum Integration**: LMS integration capabilities
- **Research Tools**: Built-in research and citation tools

#### 🏗️ Platform Evolution
- **Plugin Architecture**: Extensible plugin system
- **Custom AI Models**: Domain-specific model training
- **Federated Learning**: Privacy-preserving model improvements
- **Global Scale**: Multi-region deployment support
- **Compliance Features**: FERPA, COPPA, and GDPR compliance

---

*For more detailed information about changes, see the [commit history](https://github.com/opengov/literacy-coach/commits/main) on GitHub.*
