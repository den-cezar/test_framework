"""
Shared token cache for OAuth tokens across parallel workers.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from filelock import FileLock

from core.logging.logger import Logger


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
        logger = Logger.get_logger("TokenCache")
        logger.debug("Checking token expiry.")

        if not isinstance(refresh_skew_seconds, int) or refresh_skew_seconds < 0:
            raise ValueError("refresh_skew_seconds must be a non-negative integer.")
        return time.time() >= (self.expires_at - refresh_skew_seconds)


class SharedTokenCache:
    """
    File-based token cache shared across all workers.
    """

    def __init__(self, cache_path: Path) -> None:
        """
        Initialize the shared token cache.

        :param cache_path: Mandatory, Path to the cache file.
        """
        logger = Logger.get_logger("TokenCache")
        logger.debug("Initializing shared token cache.")

        if not isinstance(cache_path, Path):
            raise ValueError("cache_path must be a Path.")
        self.cache_path = cache_path
        self.lock_path = cache_path.with_suffix(cache_path.suffix + ".lock")

        if not self.cache_path.parent.exists():
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)

    def get_token(self, cache_key: str) -> TokenRecord | None:
        """
        Retrieve a token from the cache.

        :param cache_key: Mandatory, Cache key for the token.
        :return: TokenRecord or None if missing.
        """
        logger = Logger.get_logger("TokenCache")
        logger.debug("Fetching token from cache.")

        if not isinstance(cache_key, str) or not cache_key:
            raise ValueError("cache_key must be a non-empty string.")

        if not self.cache_path.exists():
            return None

        lock = FileLock(str(self.lock_path))
        with lock:
            raw_data = self._read_cache()

        token_data = raw_data.get(cache_key)
        if not token_data:
            return None

        access_token = token_data.get("access_token") or token_data.get("accessToken")
        expires_at = token_data.get("expires_at") or token_data.get("expiresAt")
        if access_token is None or expires_at is None:
            return None

        return TokenRecord(access_token=str(access_token), expires_at=float(expires_at))

    def set_token(self, cache_key: str, token_record: TokenRecord) -> None:
        """
        Store a token in the cache.

        :param cache_key: Mandatory, Cache key for the token.
        :param token_record: Mandatory, Token data to store.
        """
        logger = Logger.get_logger("TokenCache")
        logger.debug("Storing token in cache.")

        if not isinstance(cache_key, str) or not cache_key:
            raise ValueError("cache_key must be a non-empty string.")
        if not isinstance(token_record, TokenRecord):
            raise ValueError("token_record must be a TokenRecord.")

        lock = FileLock(str(self.lock_path))
        with lock:
            raw_data = self._read_cache()
            raw_data[cache_key] = {"access_token": token_record.access_token, "expires_at": token_record.expires_at}
            self._write_cache(raw_data)

    def _read_cache(self) -> dict[str, Any]:
        """
        Read the cache file contents.

        :return: Parsed cache data.
        """
        logger = Logger.get_logger("TokenCache")
        logger.debug("Reading token cache file.")

        if not self.cache_path.exists():
            return {}

        content = self.cache_path.read_text(encoding="utf-8").strip()
        if not content:
            return {}
        return json.loads(content)

    def _write_cache(self, raw_data: dict[str, Any]) -> None:
        """
        Write cache data to the cache file.

        :param raw_data: Mandatory, Cache data to persist.
        """
        logger = Logger.get_logger("TokenCache")
        logger.debug("Writing token cache file.")

        if not isinstance(raw_data, dict):
            raise ValueError("raw_data must be a dictionary.")
        self.cache_path.write_text(json.dumps(raw_data, indent=2), encoding="utf-8")
