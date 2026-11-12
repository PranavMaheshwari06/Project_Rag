"""Deadline rules drafted 2026-11-12 from the verified records (pending review):
each encoding pattern on the real rule files, on the closing day and the day after."""

from datetime import date

import pytest

from core.config import load_settings
from eligibility.engine import check_eligibility
from eligibility.profile import Profile
from eligibility.rules import load_ruleset


def verdict(slug, rule_id, as_of, intake, citizenships=("India",), starting_year=2027, **facts):
    rules, stale = load_ruleset(load_settings(), slug)
    rep = check_eligibility(Profile(citizenships=list(citizenships), **facts), rules, stale,
                            as_of=as_of, intake=intake, starting_year=starting_year)
    c = {c.rule_id: c for c in rep.criteria}[rule_id]
    return c.verdict, c.reason


@pytest.mark.parametrize("slug", ["tum-m-sc-informatics", "tum-m-sc-data-engineering-and-analytics"])
def test_tum_summer_closes_in_november_of_the_previous_year(slug):
    assert verdict(slug, "deadline_summer", date(2026, 11, 30), "summer")[0] == "meets"
    assert verdict(slug, "deadline_summer", date(2026, 12, 1), "summer") == ("does_not_meet", "window_closed")
    assert verdict(slug, "deadline_winter", date(2027, 5, 31), "winter")[0] == "meets"
    assert verdict(slug, "deadline_winter", date(2027, 6, 1), "winter") == ("does_not_meet", "window_closed")


def test_stuttgart_winter_closes_in_january_and_summer_the_july_before():
    slug = "university-of-stuttgart-m-sc-computer-science"
    assert verdict(slug, "deadline_winter", date(2027, 1, 15), "winter")[0] == "meets"
    assert verdict(slug, "deadline_winter", date(2027, 1, 16), "winter")[1] == "window_closed"
    assert verdict(slug, "deadline_summer", date(2026, 7, 15), "summer")[0] == "meets"
    assert verdict(slug, "deadline_summer", date(2026, 7, 16), "summer")[1] == "window_closed"


def test_rwth_data_science_dates_depend_on_citizenship():
    slug = "rwth-aachen-m-sc-data-science"
    assert verdict(slug, "deadline_winter", date(2027, 3, 2), "winter")[1] == "window_closed"
    assert verdict(slug, "deadline_winter", date(2027, 7, 15), "winter", ["France"])[0] == "meets"
    assert verdict(slug, "deadline_summer", date(2026, 9, 1), "summer")[0] == "meets"
    assert verdict(slug, "deadline_summer", date(2026, 9, 2), "summer")[1] == "window_closed"


def test_dresden_dates_apply_to_a_foreign_degree_only():
    slug = "tu-dresden-m-sc-computer-science"
    assert verdict(slug, "deadline_winter", date(2027, 5, 31), "winter", degree_country="India")[0] == "meets"
    assert verdict(slug, "deadline_winter", date(2027, 6, 1), "winter", degree_country="India")[1] == "window_closed"
    assert verdict(slug, "deadline_winter", date(2027, 7, 15), "winter", ["Italy"], degree_country="India")[0] == "meets"
    assert verdict(slug, "deadline_winter", date(2027, 6, 1), "winter", degree_country="Germany")[0] == "not_applicable"


@pytest.mark.parametrize("slug", ["saarland-university-m-sc-computer-science",
                                  "saarland-university-m-sc-data-science-and-artificial-intelligence"])
def test_saarland_early_date_is_soft_and_cannot_fail_readiness(slug):
    rules, stale = load_ruleset(load_settings(), slug)
    rep = check_eligibility(Profile(citizenships=["India"]), rules, stale,
                            as_of=date(2027, 1, 10), intake="winter", starting_year=2027)
    c = {c.rule_id: c for c in rep.criteria}
    assert (c["deadline_winter_early"].verdict, c["deadline_winter_early"].severity) == ("does_not_meet", "soft")
    assert c["deadline_winter"].verdict == "meets"
    assert rep.readiness.headline != "items_still_needed"  # only a missed hard date fails readiness
