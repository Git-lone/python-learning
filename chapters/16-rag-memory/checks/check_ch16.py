"""CH16-EX01 自动验收。"""

import pytest

from exercise_support import load_target

target = load_target(__file__)


def test_documents_are_ranked_by_overlap_then_identifier() -> None:
    documents = [
        target.Document("b", "python file context"),
        target.Document("a", "python file pathlib"),
        target.Document("c", "java stream"),
    ]
    assert [item.document_id for item in target.rank_documents("python file", documents, 2)] == [
        "a",
        "b",
    ]


def test_documents_without_overlap_are_not_returned() -> None:
    documents = [target.Document("a", "python file")]
    assert target.rank_documents("database", documents, 3) == []


def test_limit_is_applied_after_ranking() -> None:
    documents = [
        target.Document("a", "python"),
        target.Document("b", "python"),
    ]
    assert [item.document_id for item in target.rank_documents("python", documents, 1)] == ["a"]


def test_non_positive_limit_is_rejected() -> None:
    with pytest.raises(ValueError):
        target.rank_documents("python", [], 0)
