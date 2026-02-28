# Contributing

Thank you for your interest in contributing to this project! This guide will help you get started.

## How to Contribute

1. **Fork** the repository
2. **Create a branch** from `main`: `git checkout -b feature/your-feature main`
3. **Make your changes** and commit
4. **Push** to your fork: `git push -u origin feature/your-feature`
5. **Open a Pull Request** against `main`

## Branch Naming

Use the format `{type}/{short-description}`:

| Type | Use Case | Example |
|------|----------|---------|
| `feature/` | New functionality | `feature/add-healthcheck` |
| `fix/` | Bug fixes | `fix/redis-connection-timeout` |
| `docs/` | Documentation changes | `docs/update-scaling-guide` |
| `chore/` | Maintenance, dependencies | `chore/bump-n8n-version` |

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
{type}: {description}
```

**Types**: `feat`, `fix`, `docs`, `chore`, `refactor`, `style`, `test`

**Examples**:
```
feat: add health check endpoint to python-runner
fix: resolve redis connection timeout on worker restart
docs: update README with backup instructions
chore: bump postgres image to v16
```

**Rules**:
- Use English, lowercase, no period at the end
- Use present tense: "add" not "added"
- Keep the subject under 50 characters

## Pull Request Checklist

Before submitting a PR, please verify:

- [ ] `docker-compose up -d` starts all services without errors
- [ ] `docker-compose ps` shows all services as healthy/running
- [ ] Changes are documented (README, comments, etc.)
- [ ] No secrets or personal data are included in the commit

## Code Style

### Python (python-runner)
- Follow [PEP 8](https://pep8.org/)
- Use type hints where practical
- Add docstrings for public functions

### Docker / YAML
- Use 2-space indentation
- Add comments for non-obvious configurations

## Reporting Issues

When opening an issue, please include:

1. **Description**: What happened vs. what you expected
2. **Steps to reproduce**: How to trigger the issue
3. **Environment**: OS, Docker version, n8n version
4. **Logs**: Relevant output from `docker-compose logs`

## Questions?

Open an issue with the `question` label and we'll be happy to help.
