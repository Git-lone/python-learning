import pytest

from agent_lab.evaluate import evaluate
from agent_lab.retrieval import recall_at_k, reciprocal_rank, retrieve


def test_retrieval_filters_tenant_and_returns_no_unknown_evidence():
    hits = retrieve("password reset", "alpha")
    assert hits[0].document.id == "kb-reset"
    assert all(hit.document.tenant == "alpha" for hit in hits)
    assert retrieve("password reset", "unknown") == []
    assert retrieve("volcano", "alpha") == []
    assert retrieve("   ", "alpha") == []


def test_metrics_count_unique_relevant_documents():
    assert recall_at_k(["a", "a", "b"], {"a", "b"}, 2) == 0.5
    assert reciprocal_rank(["x", "a"], {"a"}) == 0.5
    assert reciprocal_rank(["x"], {"a"}) == 0
    with pytest.raises(ValueError):
        recall_at_k([], set(), 3)
    with pytest.raises(ValueError):
        retrieve("q", "alpha", 0)


def test_synthetic_baseline():
    result = evaluate()
    assert result["recall@3"] == 1
    assert result["mrr@3"] == 1
    assert result["correct_abstentions"] == result["negative_cases"]
