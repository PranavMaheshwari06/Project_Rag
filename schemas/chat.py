from typing import Literal

from pydantic import BaseModel, Field, model_validator

from eligibility.profile import Profile
from schemas.search import Filters


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    filters: Filters | None = None  # one-shot retrieval only; the agent chooses its own lookups
    mode: Literal["oneshot", "agent", "auto"] = "auto"  # auto: one-shot, then the agent if it refuses
    # the student's own profile, for check_eligibility only: never sent to the model, logged or cached
    profile: Profile | None = None
    profile_confirmed: bool = False
    intake: Literal["winter", "summer"] | None = None
    starting_year: int | None = None
    # text the student pasted (a programme page, say): one unverified passage for one-shot, never cached, logged or
    # escalated to the agent. Its length limit (generation.user_source_max_chars) is checked by the route
    user_source: str | None = None

    @model_validator(mode="after")
    def _confirmed(self):
        if self.profile is not None and not self.profile_confirmed:
            raise ValueError("a profile is used only after the student confirms it (profile_confirmed: true)")
        return self

    @model_validator(mode="after")
    def _pasted_text_is_one_shot(self):
        if self.user_source is not None:
            if not self.user_source.strip():
                raise ValueError("user_source is empty")
            if self.mode == "agent" or self.profile is not None:
                raise ValueError("pasted text is answered by one-shot only: send it without a profile, "
                                 "and not in agent mode")
        return self
