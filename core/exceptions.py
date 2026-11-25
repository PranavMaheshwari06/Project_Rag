"""App-level exceptions. The FastAPI layer maps these to HTTP responses in one
place instead of sprinkling status codes through business code."""


class AppError(Exception):
    status_code = 500
    headers: dict[str, str] | None = None  # sent with the error response (e.g. Retry-After)

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class BadRequestError(AppError):
    status_code = 400


class ServiceUnavailableError(AppError):
    status_code = 503


class UpstreamError(AppError):
    status_code = 502


class DeadlineError(AppError):
    status_code = 504


class TooManyRequestsError(AppError):
    status_code = 429

    def __init__(self, message: str, retry_after: float):
        super().__init__(message)
        self.headers = {"Retry-After": str(max(1, round(retry_after)))}


class CorpusNotIngestedError(AppError):
    status_code = 409

    def __init__(self, message: str = "Corpus not ingested yet. Run `make ingest` or POST /ingest first."):
        super().__init__(message)


class IndexNotBuiltError(AppError):
    status_code = 409

    def __init__(self, message: str = "Indexes not built yet. Run `make index` or POST /ingest with rebuild_indexes=true."):
        super().__init__(message)
