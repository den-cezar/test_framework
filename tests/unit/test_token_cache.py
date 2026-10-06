import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from core.auth.token_cache import SharedTokenCache, TokenRecord


def _record(token: str, ttl_seconds: float = 3600) -> TokenRecord:
    return TokenRecord(access_token=token, expires_at=time.time() + ttl_seconds)


def test_factory_is_called_once_while_token_is_valid(tmp_path: Path) -> None:
    cache = SharedTokenCache(tmp_path.joinpath("cache.json"))
    calls: list[int] = []

    def factory() -> TokenRecord:
        calls.append(1)
        return _record("token-1")

    first = cache.get_or_create("key", factory)
    second = cache.get_or_create("key", factory)

    assert first.access_token == second.access_token == "token-1"
    assert len(calls) == 1


def test_cache_is_shared_through_the_file(tmp_path: Path) -> None:
    path = tmp_path.joinpath("cache.json")
    SharedTokenCache(path).get_or_create("key", lambda: _record("from-worker-1"))

    record = SharedTokenCache(path).get_or_create("key", lambda: _record("from-worker-2"))

    assert record.access_token == "from-worker-1"


def test_token_inside_refresh_window_is_replaced(tmp_path: Path) -> None:
    cache = SharedTokenCache(tmp_path.joinpath("cache.json"))
    cache.get_or_create("key", lambda: _record("old", ttl_seconds=10))

    record = cache.get_or_create("key", lambda: _record("new"))

    assert record.access_token == "new"


def test_corrupt_cache_file_is_ignored(tmp_path: Path) -> None:
    path = tmp_path.joinpath("cache.json")
    path.write_text("{not json", encoding="utf-8")

    record = SharedTokenCache(path).get_or_create("key", lambda: _record("fresh"))

    assert record.access_token == "fresh"


def test_concurrent_callers_request_a_single_token(tmp_path: Path) -> None:
    path = tmp_path.joinpath("cache.json")
    calls: list[int] = []
    calls_lock = threading.Lock()

    def slow_factory() -> TokenRecord:
        with calls_lock:
            calls.append(1)
        time.sleep(0.05)
        return _record("only-one")

    with ThreadPoolExecutor(max_workers=8) as pool:
        tokens = list(
            pool.map(lambda _: SharedTokenCache(path).get_or_create("key", slow_factory).access_token, range(8))
        )

    assert tokens == ["only-one"] * 8
    assert len(calls) == 1
