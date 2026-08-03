import pytest

from retrieval.hybrid import rrf_fuse


def test_fusion_math():
    fused = rrf_fuse({"dense": ["x", "y"], "bm25": ["y", "z"]}, k=60)
    scores = dict(fused)
    assert scores["y"] == pytest.approx(1 / 61 + 1 / 62)
    assert scores["x"] == pytest.approx(1 / 61)
    assert scores["z"] == pytest.approx(1 / 62)
    assert [cid for cid, _ in fused] == ["y", "x", "z"]


def test_item_in_both_lists_beats_single_list_winner():
    # rank 3 in both lists still outranks a lone rank 2
    fused = rrf_fuse({"a": ["p", "q", "both"], "b": ["r", "s", "both"]}, k=60)
    assert fused[0][0] == "both"


def test_tie_break_is_deterministic():
    fused = rrf_fuse({"a": ["zebra"], "b": ["apple"]}, k=60)
    assert fused[0][1] == pytest.approx(fused[1][1])
    assert [cid for cid, _ in fused] == ["apple", "zebra"]  # lexical on equal score


def test_empty_input():
    assert rrf_fuse({}, k=60) == []
    assert rrf_fuse({"a": []}, k=60) == []


def test_k_dampens_rank_gap():
    small_k = rrf_fuse({"a": ["first", "second"]}, k=1)
    big_k = rrf_fuse({"a": ["first", "second"]}, k=1000)
    gap_small = small_k[0][1] - small_k[1][1]
    gap_big = big_k[0][1] - big_k[1][1]
    assert gap_small > gap_big
