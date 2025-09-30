# Contributing to Literacy Coach

We welcome contributions from the community! This document outlines the process for contributing to the Literacy Coach project.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Git](https://git-scm.com/)
- OpenAI API key (for full functionality)

### Development Environment Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/opengov/literacy-coach.git
   cd literacy-coach
   ```

2. **Install dependencies:**
   ```bash
   uv sync --dev
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

4. **Run tests:**
   ```bash
   uv run pytest -q
   ```

5. **Start development services:**
   ```bash
   docker compose up --build
   ```

## Development Workflow

### Branch Strategy

- `main`: Production-ready code
- `develop`: Integration branch for new features
- `feature/*`: New features or enhancements
- `bugfix/*`: Bug fixes
- `hotfix/*`: Critical production fixes

### Making Changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests:**
   ```bash
   uv run pytest -q
   ```

4. **Check code quality:**
   ```bash
   uv run hatch run lint
   uv run hatch run type-check
   ```

5. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Add your descriptive commit message"
   ```

6. **Push and create a pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Standards

### Style Guidelines

- **Line length:** 100 characters maximum
- **Formatting:** Use Black for Python code formatting
- **Imports:** Use isort for import organization
- **Type hints:** All functions should have type annotations
- **Documentation:** Use Google-style docstrings

### Code Quality Tools

```bash
# Format code
uv run hatch run format

# Lint code
uv run hatch run lint

# Type checking
uv run hatch run type-check

# Security scanning
uv run hatch run security-scan
```

### Testing Requirements

- **Test coverage:** Minimum 85% for new code
- **Test types:** Include unit, integration, and end-to-end tests
- **Test markers:** Use appropriate pytest markers (`@pytest.mark.unit`, `@pytest.mark.integration`, etc.)

## Documentation

### Documentation Requirements

- Update README.md for user-facing changes
- Update API documentation for API changes
- Add inline documentation for complex functions
- Update runbooks for operational changes

### Documentation Tools

- **API docs:** Auto-generated from FastAPI applications
- **Runbooks:** Manual maintenance in `docs/runbooks.md`
- **Architecture:** Update `docs/architecture.md` for significant changes

## Pull Request Process

### PR Requirements

1. **Description:** Clear description of changes and motivation
2. **Tests:** All tests pass
3. **Documentation:** Updated as needed
4. **Code review:** Approved by at least one maintainer
5. **CI/CD:** All pipeline checks pass

### PR Template

```markdown
## Description

Brief description of the changes.

## Motivation

Why this change is needed.

## Changes

- Change 1
- Change 2
- Change 3

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] End-to-end tests added/updated
- [ ] Manual testing completed

## Documentation

- [ ] README updated
- [ ] API documentation updated
- [ ] Runbooks updated

## Checklist

- [ ] Code follows project style guidelines
- [ ] Tests pass
- [ ] Documentation is updated
- [ ] No breaking changes
```

## Commit Message Guidelines

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

**Examples:**
```
feat(tui): add new terminal interface

fix(agent): resolve tool calling timeout

docs(api): update endpoint documentation

test(security): add encryption tests
```

## Issue Reporting

### Bug Reports

When reporting bugs, please include:

- **Description:** Clear description of the issue
- **Steps to reproduce:** Detailed steps to reproduce the problem
- **Expected behavior:** What should happen
- **Actual behavior:** What actually happens
- **Environment:** Python version, OS, relevant dependencies
- **Logs:** Relevant error logs or stack traces

### Feature Requests

When requesting features, please include:

- **Problem statement:** What problem does this solve?
- **Proposed solution:** How should it work?
- **Alternatives considered:** Other approaches considered
- **Additional context:** Screenshots, examples, etc.

## Community Guidelines

### Code of Conduct

This project follows the Contributor Covenant Code of Conduct. By participating, you agree to:

- Be respectful and inclusive
- Use welcoming and inclusive language
- Be collaborative
- Focus on what is best for the community
- Show empathy towards other community members

### Communication

- **GitHub Issues:** For bug reports and feature requests
- **Discussions:** For questions and general discussion
- **Email:** For private communications with maintainers
- **Meetings:** Regular community meetings (schedule posted in Discussions)

## Development Tools

### Required Tools

- **uv:** Fast Python package manager
- **Docker:** Containerization
- **Git:** Version control
- **Visual Studio Code:** Recommended IDE (with Python extensions)

### Optional Tools

- **Postman:** API testing
- **ngrok:** Local development tunneling
- **SQLite Browser:** Database inspection
- **Wireshark:** Network debugging

## Performance Guidelines

### Performance Requirements

- **Response time:** < 2 seconds for API calls
- **Memory usage:** < 512MB per service container
- **CPU usage:** < 50% per service container
- **Database queries:** < 100ms for simple queries

### Performance Testing

```bash
# Run performance tests
uv run pytest tests/test_performance.py -v

# Load testing
uv run locust -f tests/load_test.py

# Memory profiling
uv run python -m memory_profiler script.py
```

## Security Guidelines

### Security Requirements

- All API keys must be encrypted at rest
- No hardcoded secrets in code
- Input validation on all endpoints
- SQL injection prevention
- XSS protection
- CSRF protection for web interfaces

### Security Testing

```bash
# Run security tests
uv run pytest tests/test_security.py -v

# Security scanning
uv run bandit -r src/
uv run detect-secrets scan

# Dependency vulnerability check
uv run safety check
```

## Release Process

### Version Management

- Follow [Semantic Versioning](https://semver.org/)
- Update version in `pyproject.toml`
- Create release notes in CHANGELOG.md
- Tag releases in Git

### Release Checklist

- [ ] All tests pass
- [ ] Code quality checks pass
- [ ] Security scan passes
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped
- [ ] Release tag created
- [ ] Docker images built and tested
- [ ] Deployment verified

## Getting Help

### Resources

- **Documentation:** [README.md](README.md)
- **API Reference:** [docs/api-reference.md](docs/api-reference.md)
- **Runbooks:** [docs/runbooks.md](docs/runbooks.md)
- **Architecture:** [docs/architecture.md](docs/architecture.md)

### Support Channels

1. **GitHub Issues:** Bug reports and feature requests
2. **GitHub Discussions:** Questions and general discussion
3. **Email:** maintainers@opengov.org for private inquiries
4. **Office Hours:** Weekly community calls (schedule in Discussions)

### Common Questions

**Q: How do I add a new service?**
A: Follow the existing microservice pattern. Create a new service in `src/litcoach/services/`, add to `pyproject.toml`, and update Docker configuration.

**Q: How do I modify the database schema?**
A: Update the SQLAlchemy models, create a migration script, and update the initialization code.

**Q: How do I add a new LLM provider?**
A: Implement the provider interface in `litcoach/services/llm_client.py` and add configuration options.

## Acknowledgments

Thank you for contributing to Literacy Coach! Your contributions help improve educational outcomes for learners worldwide.

---

*This contributing guide is adapted from the Open Source Guides for Kubernetes.*