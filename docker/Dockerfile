FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONPATH=/app

WORKDIR /app

# Install build dependencies and project requirements
COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir poetry \
    && poetry install --without dev --no-root

# Copy application source
COPY app ./app
COPY README.md ./

CMD ["python", "-m", "app.main"]
