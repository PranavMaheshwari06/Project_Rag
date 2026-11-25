# The API image: code, verified records, rules, the chunked corpus, both indexes and the two retrieval models.
# Build from the repo root after `make ingest index` (data/processed and data/index are not in git):
#   docker build -f docker/api.Dockerfile -t germany-masters-api .
# Without GEMINI_API_KEY at run time, answers are extractive. Behind a trusted proxy set CLIENT_IP_HEADER, or every
# visitor shares one rate limit. One worker on purpose: the limits and the answer cache live in process memory.

FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HOME=/opt/models

RUN pip install --no-cache-dir uv==0.9.21

# torch CPU wheels are large; keep them cached in their own layer. Test and lint tools stay out of the image.
COPY requirements.lock ./
RUN grep -vE '^(pytest|ruff)==' requirements.lock > runtime.lock \
 && uv pip install --system --no-cache --torch-backend cpu -r runtime.lock

# an unprivileged user that can write only the model cache and the feedback notes
RUN useradd --create-home --uid 10001 app \
 && mkdir -p /opt/models data/feedback && chown app /opt/models data/feedback
USER app

# the two models named in settings.yaml, downloaded at build time so that a start needs no network
COPY config/settings.yaml ./config/settings.yaml
RUN python -c "import yaml; from huggingface_hub import snapshot_download; \
m = yaml.safe_load(open('config/settings.yaml'))['models']; \
[snapshot_download(m[k], allow_patterns=['*.json', '*.txt', '*.model', '*.safetensors']) \
 for k in ('embed_model', 'rerank_model')]"
ENV HF_HUB_OFFLINE=1

COPY api ./api
COPY agent ./agent
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

COPY data/eligibility ./data/eligibility
COPY data/verified ./data/verified
# named one by one: a missing corpus or index fails the build here
COPY data/processed/chunks.jsonl ./data/processed/
COPY data/index/bm25.pkl data/index/dense.npz ./data/index/

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready')"]

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--http", "httptools"]
