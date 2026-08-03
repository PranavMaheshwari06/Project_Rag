from pydantic import BaseModel


class IngestRequest(BaseModel):
    # index rebuild embeds the whole corpus, so it's opt-in
    rebuild_indexes: bool = False


class IngestResponse(BaseModel):
    request_id: str
    docs: int
    chunks: int
    indexes_rebuilt: bool
    latency_ms: dict[str, float]
