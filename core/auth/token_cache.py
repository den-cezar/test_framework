"""
Shared token cache for OAuth tokens across parallel workers.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from filelock import FileLock

from core.logging.logger import Logger

logger = Logger.get_logger("TokenCache")


@dataclass(frozen=True)
class TokenRecord:
    """
    Token record stored in the cache.
    """

    access_token: str
    expires_at: float

    def is_expired(self, refresh_skew_seconds: int = 30) -> bool:
        """
        Determine if the token is expired.

        :param refresh_skew_seconds: Optional, The skew seconds before expiry to refresh.
        :return: True if expired or near expiry.
        """
        return time.time() >= (self.expires_at - refresh_skew_seconds)


class SharedTokenCache:
    """
    File-based token cache shared across all xdist workers.
    """

    def __init__(self, cache_path: Path, lock_timeout_seconds: float = 60) -> None:
        """
        Initialize the shared token cache.

        :param cache_path: Mandatory, Path to the cache file.
        :param lock_timeout_seconds: Optional, Max wait for the file lock.
        """
        self.cache_path = cache_path
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = FileLock(f"{cache_path}.lock", timeout=lock_timeout_seconds)

    def get_or_create(self, cache_key: str, factory: Callable[[], TokenRecord]) -> TokenRecord:
        """
        Return a valid cached token, or create and store one with `factory`.

        The lock is held for the whole check-fetch-store sequence, so parallel workers
        request at most one token per key.

        :param cache_key: Mandatory, Cache key for the token.
        :param factory: Mandatory, Callable that requests a new token.
        :return: A non-expired TokenRecord.
        """
        with self._lock:
            raw_data = self._read_cache()
            cached = _parse_record(raw_data.get(cache_key))
            if cached and not cached.is_expired():
                logger.debug("Token cache hit.")
                return cached

            logger.debug("Token cache miss; requesting a new token.")
            record = factory()
            raw_data[cache_key] = {"access_token": record.access_token, "expires_at": record.expires_at}
            self._write_cache(raw_data)
            return record

    def _read_cache(self) -> dict[str, Any]:
        """
        Read the cache file contents. A missing or corrupt file is treated as empty.

        :return: Parsed cache data.
        """
        if not self.cache_path.exists():
            return {}
        try:
            data = json.loads(self.cache_path.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError:
            logger.warning("Token cache %s is corrupt; ignoring it.", self.cache_path)
            return {}
        return data if isinstance(data, dict) else {}

    def _write_cache(self, raw_data: dict[str, Any]) -> None:
        """
        Atomically write cache data to the cache file.

        :param raw_data: Mandatory, Cache data to persist.
        """
        tmp_path = self.cache_path.with_suffix(f"{self.cache_path.suffix}.tmp")
        tmp_path.write_text(json.dumps(raw_data, indent=2), encoding="utf-8")
        os.replace(tmp_path, self.cache_path)


def _parse_record(token_data: Any) -> TokenRecord | None:
    """
    Build a TokenRecord from a raw cache entry.

    :param token_data: Optional, Raw cache entry.
    :return: TokenRecord, or None if the entry is missing or malformed.
    """
    if not isinstance(token_data, dict):
        return None
    access_token = token_data.get("access_token")
    expires_at = token_data.get("expires_at")
    if not access_token or expires_at is None:
        return None
    return TokenRecord(access_token=str(access_token), expires_at=float(expires_at))
