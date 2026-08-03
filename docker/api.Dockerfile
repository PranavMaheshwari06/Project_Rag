# Containerization phase — NOT used in the local no-Docker run.
# Build context is the repo root: docker build -f docker/api.Dockerfile .

FROM python:3.12-slim

WORKDIR /app

# torch CPU wheels are large; keep them cached in their own layer
COPY pyproject.toml ./
RUN pip install --no-cache-dir . && pip uninstall -y engineerdoc-ai

COPY api ./api
COPY core ./core
COPY schemas ./schemas
COPY ingestion ./ingestion
COPY retrieval ./retrieval
COPY generation ./generation
COPY evaluation ./evaluation
COPY scripts ./scripts
COPY config ./config
COPY data/samples ./data/samples
RUN pip install --no-cache-dir --no-deps .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
