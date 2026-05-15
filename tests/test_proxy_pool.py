"""
Tests for ProxyPool.
"""
import pytest
from kryptic.proxy_pool import ProxyPool

PROXIES = [
    "http://proxy1.example.com:8080",
    "http://proxy2.example.com:8080",
    "http://proxy3.example.com:8080",
]


def test_init_round_robin():
    pool = ProxyPool(PROXIES, strategy="round_robin")
    assert pool.total == 3
    assert pool.available_count == 3
    assert pool.failed_count == 0


def test_init_random():
    pool = ProxyPool(PROXIES, strategy="random")
    assert pool.total == 3


def test_invalid_strategy():
    with pytest.raises(ValueError, match="strategy"):
        ProxyPool(PROXIES, strategy="unknown")


def test_empty_proxies():
    with pytest.raises(ValueError, match="empty"):
        ProxyPool([])


def test_round_robin_cycles():
    pool = ProxyPool(PROXIES, strategy="round_robin")
    results = [pool.next() for _ in range(9)]
    assert results[:3] == PROXIES
    assert results[3:6] == PROXIES
    assert results[6:9] == PROXIES


def test_random_returns_valid_proxy():
    pool = ProxyPool(PROXIES, strategy="random")
    for _ in range(20):
        p = pool.next()
        assert p in PROXIES


def test_mark_failed():
    pool = ProxyPool(PROXIES)
    pool.mark_failed(PROXIES[0])
    assert pool.failed_count == 1
    assert pool.available_count == 2


def test_mark_failed_skipped_in_round_robin():
    pool = ProxyPool(PROXIES, strategy="round_robin")
    pool.mark_failed(PROXIES[0])
    for _ in range(10):
        p = pool.next()
        assert p != PROXIES[0]


def test_mark_failed_skipped_in_random():
    pool = ProxyPool(PROXIES, strategy="random")
    pool.mark_failed(PROXIES[0])
    for _ in range(20):
        p = pool.next()
        assert p != PROXIES[0]


def test_mark_recovered():
    pool = ProxyPool(PROXIES)
    pool.mark_failed(PROXIES[0])
    assert pool.available_count == 2
    pool.mark_recovered(PROXIES[0])
    assert pool.available_count == 3


def test_all_failed_resets():
    pool = ProxyPool(PROXIES)
    for p in PROXIES:
        pool.mark_failed(p)
    assert pool.failed_count == 3
    result = pool.next()
    assert result in PROXIES
    assert pool.failed_count == 0


def test_reset():
    pool = ProxyPool(PROXIES)
    pool.mark_failed(PROXIES[0])
    pool.mark_failed(PROXIES[1])
    pool.reset()
    assert pool.failed_count == 0
    assert pool.available_count == 3


def test_len():
    pool = ProxyPool(PROXIES)
    assert len(pool) == 3


def test_repr():
    pool = ProxyPool(PROXIES)
    r = repr(pool)
    assert "ProxyPool" in r
    assert "total=3" in r


def test_single_proxy():
    pool = ProxyPool(["http://only.proxy:8080"])
    assert pool.next() == "http://only.proxy:8080"
    assert pool.next() == "http://only.proxy:8080"


def test_single_proxy_recovered_after_fail():
    pool = ProxyPool(["http://only.proxy:8080"])
    pool.mark_failed("http://only.proxy:8080")
    result = pool.next()
    assert result == "http://only.proxy:8080"


def test_round_robin_two_proxies():
    two = ["http://a:8080", "http://b:8080"]
    pool = ProxyPool(two, strategy="round_robin")
    seq = [pool.next() for _ in range(6)]
    assert seq == ["http://a:8080", "http://b:8080"] * 3


def test_failed_count_property():
    pool = ProxyPool(PROXIES)
    assert pool.failed_count == 0
    pool.mark_failed(PROXIES[0])
    assert pool.failed_count == 1
    pool.mark_failed(PROXIES[1])
    assert pool.failed_count == 2
