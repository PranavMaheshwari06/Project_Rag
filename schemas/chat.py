from typing import Literal

from pydantic import BaseModel, Field, model_validator

from eligibility.profile import Profile
from schemas.search import Filters


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    filters: Filters | None = None  # one-shot retrieval only; the agent chooses its own lookups
    mode: Literal["oneshot", "agent"] = "oneshot"
    # the student's own profile, for check_eligibility only: never sent to the model, logged or cached
    profile: Profile | None = None
    profile_confirmed: bool = False
    intake: Literal["winter", "summer"] | None = None
    starting_year: int | None = None

    @model_validator(mode="after")
    def _confirmed(self):
        if self.profile is not None and not self.profile_confirmed:
            raise ValueError("a profile is used only after the student confirms it (profile_confirmed: true)")
        return self
