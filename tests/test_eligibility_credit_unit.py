"""The credit unit is a closed choice,
"ECTS" or "other". Free text such as "LP" can no longer send a rule to
"the university decides" by accident; the form offers the two values."""

import pytest
from pydantic import ValidationError

from eligibility.profile import SCHEMA_VERSION, Profile


def test_credit_unit_is_a_closed_choice():
    assert SCHEMA_VERSION == "profile-v4"
    assert Profile(credit_unit="ECTS").credit_unit == "ECTS"
    assert Profile(credit_unit="other").credit_unit == "other"
    for free_text in ("LP", "CP", "ECTS credits", "ects", "US credits", ""):
        with pytest.raises(ValidationError):
            Profile(credit_unit=free_text)


def test_older_profiles_with_a_closed_unit_still_load():
    assert Profile.model_validate({"schema_version": "profile-v3", "credit_unit": "ECTS"}).credit_unit == "ECTS"
    assert Profile.model_validate({"schema_version": "profile-v3", "funds": []}).funds == []
