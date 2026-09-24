"""
Tests for CaveCode approximate token estimator.
"""

from cavecode.tokenizer import TokenEstimator


def test_approximate_token_estimator():
    estimator = TokenEstimator()

    raw = "def calculate_large_dataset(records: list) -> int:\n    return sum(records)\n" * 10
    compressed = "def calculate(records: list) -> int: sum(records)" * 10

    estimate = estimator.estimate(raw, compressed)

    assert estimate.raw_approx_tokens > 0
    assert estimate.compressed_approx_tokens > 0
    assert estimate.raw_approx_tokens > estimate.compressed_approx_tokens
    assert estimate.saved_approx_tokens > 0
    assert estimate.percent_saved > 0.0

    assert "BPE Standard (Byte-Pair)" in estimate.model_estimates
    assert "BPE Code-Tuned" in estimate.model_estimates
    assert "SentencePiece / Unigram" in estimate.model_estimates
