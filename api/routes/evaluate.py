from fastapi import APIRouter

from core.config import get_settings
from evaluation.runner import run_benchmark
from schemas.eval import BenchmarkResult

router = APIRouter()


@router.post("/evaluate", response_model=BenchmarkResult)
def evaluate() -> BenchmarkResult:
    # runs the full 4-way benchmark; slow-ish on CPU but bounded by the gold set size
    return run_benchmark(get_settings())
