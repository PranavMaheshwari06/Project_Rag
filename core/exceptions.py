"""App-level exceptions. The FastAPI layer maps these to HTTP responses in one
place instead of sprinkling status codes through business code."""


class AppError(Exception):
    status_code = 500

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class BadRequestError(AppError):
    status_code = 400


class CorpusNotIngestedError(AppError):
    status_code = 409

    def __init__(self, message: str = "Corpus not ingested yet. Run `make ingest` or POST /ingest first."):
        super().__init__(message)


class IndexNotBuiltError(AppError):
    status_code = 409

    def __init__(self, message: str = "Indexes not built yet. Run `make index` or POST /ingest with rebuild_indexes=true."):
        super().__init__(message)
