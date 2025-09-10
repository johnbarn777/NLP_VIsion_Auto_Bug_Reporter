# fc25-bugbot

Automated Bug Reporter (Vision + NLP) proof of concept.

```
+-----------+    +-----------+    +-----------+
| capture   | -> | detectors | -> |  NLP      |
+-----------+    +-----------+    +-----------+
                                 |
                                 v
                           +-----------+
                           | reporter  |
                           +-----------+
```

## Setup

1. Install dependencies with [Poetry](https://python-poetry.org/):
   ```bash
   poetry install
   ```
2. Run the app:
   ```bash
   poetry run python -m app.main
   ```

## Testing

```bash
poetry run pytest
poetry run black --check .
```
