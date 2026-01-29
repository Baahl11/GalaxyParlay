# Contributing to ParlayGalaxy

Thank you for your interest in contributing! This document provides guidelines and instructions.

## 🚀 Getting Started

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/parlaygalaxy.git
   cd parlaygalaxy
   ```
3. **Install dependencies**
   ```bash
   pnpm install
   cd apps/worker && pip install -r requirements.txt
   ```
4. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 📝 Code Style

### TypeScript/JavaScript
- Use Prettier for formatting (configured)
- Follow ESLint rules
- Use TypeScript strict mode
- Prefer functional components with hooks

### Python
- Use Black for formatting (line length: 100)
- Follow Ruff linting rules
- Type hints required for all functions
- Use async/await for I/O operations

### Naming Conventions
- **Files:** `kebab-case.ts`, `snake_case.py`
- **Components:** `PascalCase.tsx`
- **Functions:** `camelCase()` (TS), `snake_case()` (Python)
- **Constants:** `UPPER_SNAKE_CASE`

## 🧪 Testing

### Before submitting PR
```bash
# Run all tests
pnpm test

# Run specific tests
pnpm --filter web test
cd apps/worker && pytest tests/

# E2E tests
pnpm --filter web test:e2e
```

### Test Requirements
- Unit tests for all business logic
- Integration tests for external APIs
- E2E tests for critical user flows
- Minimum coverage: 70% (worker), 60% (web)

## 📦 Commits

### Commit Message Format
```
type(scope): subject

body (optional)

footer (optional)
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples
```bash
feat(galaxy): add zoom controls to canvas
fix(worker): handle API-Football rate limit error
docs(readme): update installation instructions
test(predictions): add ensemble model unit tests
```

## 🔄 Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Run all tests** and ensure they pass
4. **Update CHANGELOG.md** with changes
5. **Create PR** with clear description
6. **Link related issues** using keywords (Fixes #123)
7. **Request review** from maintainers

### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed

## Checklist
- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

## 🐛 Reporting Bugs

### Before Reporting
- Check existing issues
- Verify bug in latest version
- Collect reproduction steps

### Bug Report Template
```markdown
**Describe the bug**
Clear description

**To Reproduce**
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What should happen

**Screenshots**
If applicable

**Environment:**
- OS: [e.g., Windows 11]
- Browser: [e.g., Chrome 120]
- Version: [e.g., v1.0.0]
```

## 💡 Feature Requests

Use GitHub Issues with `enhancement` label:
- Clear use case description
- Expected behavior
- Alternative solutions considered
- Additional context

## 📚 Documentation

- Update README.md for user-facing changes
- Add JSDoc/docstrings for functions
- Update API documentation
- Include examples where helpful

## 🔐 Security

**DO NOT** open public issues for security vulnerabilities.
Email: security@parlaygalaxy.com

## ⚖️ License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## 🤝 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## 📞 Questions?

- GitHub Discussions: Q&A and general discussion
- GitHub Issues: Bug reports and feature requests
- Email: dev@parlaygalaxy.com

---

Thank you for contributing to ParlayGalaxy! 🌌
