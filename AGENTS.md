# Contributor Guidelines

This repository implements an automated bug reporter for EA Sports FC25. It captures gameplay anomalies, summarizes them with NLP, and can export reports to external systems.

## Development Workflow

- Use Python 3.11 and manage dependencies with [Poetry](https://python-poetry.org/).
- Install all dependencies (including dev tools) with:
  ```bash
  poetry install --with dev --no-root
  ```
- **Formatting**: Run Black over the whole tree before committing:
  ```bash
  poetry run black .
  ```
- **Testing**: Execute the test suite and make a best effort to ensure it passes:
  ```bash
  poetry run pytest
  ```
- Only commit when the formatter and tests finish successfully.
