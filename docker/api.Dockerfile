# Containerization phase — NOT used in the local no-Docker run.
# Build context is the repo root: docker build -f docker/api.Dockerfile .

FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv==0.9.21

# torch CPU wheels are large; keep them cached in their own layer
COPY requirements.lock ./
RUN uv pip install --system --no-cache --torch-backend cpu -r requirements.lock

COPY api ./api
COPY core ./core
COPY schemas ./schemas
COPY ingestion ./ingestion
COPY retrieval ./retrieval
COPY generation ./generation
COPY evaluation ./evaluation
COPY extraction ./extraction
COPY eligibility ./eligibility
COPY scripts ./scripts
COPY config ./config
COPY sources ./sources
COPY pyproject.toml ./
RUN uv pip install --system --no-cache --no-deps .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
