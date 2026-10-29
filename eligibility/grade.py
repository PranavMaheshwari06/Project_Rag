"""Modified Bavarian formula, the non-binding estimate of a German grade:

    german = 1 + 3 * (best - obtained) / (best - passing)

Works for scales running either way (100 best / 50 passing, or 1.0 best / 4.0
passing). Decimal throughout and no rounding, so a boundary is never decided by
a rounded estimate. An official conversion (e.g. a VPD) outranks this result."""

from decimal import Decimal

from pydantic import BaseModel

FORMULA = "1 + 3 * (best - obtained) / (best - passing)"


class GradeConversion(BaseModel):
    best: Decimal
    passing: Decimal
    obtained: Decimal
    german: Decimal
    formula: str = FORMULA
    estimate: bool = True  # never an official equivalence


def convert_grade(
    best: Decimal, passing: Decimal, obtained: Decimal
) -> GradeConversion:
    best, passing, obtained = Decimal(best), Decimal(passing), Decimal(obtained)
    if best == passing:
        raise ValueError("best and passing grade must differ")
    lo, hi = sorted((best, passing))
    if not lo <= obtained <= hi:
        raise ValueError("obtained grade lies outside the passing range of the scale")
    german = 1 + 3 * (best - obtained) / (best - passing)
    return GradeConversion(best=best, passing=passing, obtained=obtained, german=german)
