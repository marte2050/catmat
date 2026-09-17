from __future__ import annotations

import asyncio
import logging
import random
import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any, Self

import httpx

from catmat.core.config import settings

from .contracts.iclient import RETRYABLE_STATUS_CODES, TRANSPORT_RETRIES
from .errors.etl_error_request import ETLRequestError

logger = logging.getLogger(__name__)


class ComprasApiClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        page_size: int | None = None,
        concurrency: int | None = None,
        request_interval: float | None = None,
        timeout: float | None = None,
        retries: int | None = None,
        backoff_base: float | None = None,
        backoff_max: float | None = None,
    ) -> None:
        self.base_url = base_url or settings.compras_api_base_url
        self.page_size = page_size or settings.ingestion_page_size
        self.concurrency = max(1, concurrency or settings.ingestion_concurrency)
        self.request_interval = (
            request_interval
            if request_interval is not None
            else settings.ingestion_request_interval
        )
        self.timeout = timeout or settings.http_timeout
        self.retries = retries if retries is not None else settings.http_retries
        self.backoff_base = (
            backoff_base if backoff_base is not None else settings.http_backoff_base
        )
        self.backoff_max = (
            backoff_max if backoff_max is not None else settings.http_backoff_max
        )
        self._client: httpx.AsyncClient | None = None
        self._throttle_lock = asyncio.Lock()
        self._next_request_at = 0.0

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("ComprasApiClient não inicializado; use 'async with'")
        return self._client

    async def __aenter__(self) -> Self:
        transport = httpx.AsyncHTTPTransport(retries=TRANSPORT_RETRIES)
        limits = httpx.Limits(
            max_connections=self.concurrency,
            max_keepalive_connections=self.concurrency,
        )
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            transport=transport,
            limits=limits,
            headers={"Accept": "application/json"},
        )
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _throttle(self) -> None:
        if self.request_interval <= 0:
            return

        async with self._throttle_lock:
            now = time.monotonic()
            wait = self._next_request_at - now
            if wait > 0:
                await asyncio.sleep(wait)
                now = time.monotonic()
            self._next_request_at = now + self.request_interval

    @staticmethod
    def _retry_after(response: httpx.Response) -> float | None:
        value = response.headers.get("Retry-After")
        if not value:
            return None

        value = value.strip()
        try:
            return max(0.0, float(value))
        except ValueError:
            pass

        try:
            when = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None
        if when is None:
            return None
        if when.tzinfo is None:
            when = when.replace(tzinfo=UTC)
        return max(0.0, (when - datetime.now(UTC)).total_seconds())

    async def _wait_before_retry(
        self,
        attempt: int,
        *,
        endpoint: str,
        page: int,
        reason: str,
        retry_after: float | None = None,
    ) -> None:
        delay = (
            retry_after
            if retry_after is not None
            else min(self.backoff_base * (2**attempt), self.backoff_max)
        )
        delay += random.uniform(0.0, delay * 0.25)
        logger.warning(
            "[retry %s/%s] esperando %.1fs (%s) em '%s' página %s",
            attempt + 1,
            self.retries,
            delay,
            reason,
            endpoint,
            page,
        )
        await asyncio.sleep(delay)

    async def fetch_page(
        self,
        endpoint: str,
        page: int,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        params = {"pagina": page, "tamanhoPagina": page_size or self.page_size}
        last_status: int | None = None
        last_error: Exception | None = None
        attempts = self.retries + 1

        for attempt in range(attempts):
            await self._throttle()

            try:
                response = await self.client.get(endpoint, params=params)
            except httpx.TransportError as error:
                last_error = error
                if attempt < self.retries:
                    await self._wait_before_retry(
                        attempt,
                        endpoint=endpoint,
                        page=page,
                        reason="erro de rede",
                    )
                    continue
                break

            if response.status_code in RETRYABLE_STATUS_CODES:
                last_status = response.status_code
                if attempt < self.retries:
                    await self._wait_before_retry(
                        attempt,
                        endpoint=endpoint,
                        page=page,
                        reason=f"HTTP {response.status_code}",
                        retry_after=self._retry_after(response),
                    )
                    continue
                break

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                raise ETLRequestError(
                    endpoint,
                    page,
                    attempts,
                    status_code=response.status_code,
                    cause=error,
                ) from error

            return response.json()

        raise ETLRequestError(
            endpoint,
            page,
            attempts,
            status_code=last_status,
            cause=last_error,
        )

    async def iter_pages(self, endpoint: str) -> AsyncIterator[list[dict[str, Any]]]:
        first = await self.fetch_page(endpoint, 1)
        total_pages = int(first.get("totalPaginas") or 1)

        yield first.get("resultado") or []

        next_page = 2
        while next_page <= total_pages:
            last_page = min(next_page + self.concurrency, total_pages + 1)
            pages = await asyncio.gather(
                *(self.fetch_page(endpoint, page) for page in range(next_page, last_page))
            )
            for payload in pages:
                yield payload.get("resultado") or []
            next_page = last_page
