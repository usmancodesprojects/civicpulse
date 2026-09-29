import pytest
from pydantic import ValidationError

from app.domain import Category, ComplaintCreate, Priority, TriageResult
from app.providers.triage.rules import RuleBasedTriage


@pytest.mark.parametrize(
    ("text", "category"),
    [
        ("Water pipe leak flooding the road", Category.WATER),
        ("Electric transformer has exposed wire", Category.ELECTRICITY),
        ("Garbage waste has not been collected", Category.SANITATION),
        ("Deep pothole on the main road", Category.ROADS),
        ("Streetlight lamp is dark at night", Category.STREETLIGHTS),
        ("An abandoned cart blocks the park gate", Category.OTHER),
    ],
)
def test_rule_categories(text: str, category: Category) -> None:
    assert RuleBasedTriage().triage(text, "Central Plaza").category == category


def test_high_priority_keyword() -> None:
    assert (
        RuleBasedTriage().triage("Urgent live wire danger near school", "Street 1").priority
        == Priority.HIGH
    )


def test_low_priority_keyword() -> None:
    assert (
        RuleBasedTriage().triage("Minor cosmetic road marking issue", "Street 1").priority
        == Priority.LOW
    )


def test_summary_is_capped() -> None:
    assert len(RuleBasedTriage().triage("water " * 100, "Street 1").summary) <= 140


def test_complaint_validation_has_server_limits() -> None:
    with pytest.raises(ValidationError):
        ComplaintCreate(text="too short", location="x")


def test_triage_rejects_multiline_summary() -> None:
    with pytest.raises(ValidationError):
        TriageResult(category="other", priority="low", summary="line one\nline two", confidence=0.5)
