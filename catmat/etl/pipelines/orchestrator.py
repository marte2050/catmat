from __future__ import annotations

import logging
from collections.abc import Sequence

from sqlalchemy import text

from catmat.core.config import settings
from catmat.core.database import AsyncSessionLocal, engine
from catmat.etl.client import ComprasApiClient
from catmat.etl.loaders import LOADER_TYPES, BaseLoader

logger = logging.getLogger(__name__)

ADVISORY_LOCK_KEY = 815_492_026


class ETLPipeline:
    def __init__(
        self,
        *,
        page_size: int | None = None,
        concurrency: int | None = None,
        request_interval: float | None = None,
        batch_size: int | None = None,
        retries: int | None = None,
        limit_pages: int | None = None,
    ) -> None:
        self.page_size = page_size or settings.ingestion_page_size
        self.concurrency = concurrency or settings.ingestion_concurrency
        self.request_interval = (
            request_interval
            if request_interval is not None
            else settings.ingestion_request_interval
        )
        self.batch_size = batch_size or settings.ingestion_batch_size
        self.retries = retries if retries is not None else settings.http_retries
        self.limit_pages = limit_pages

    def _select_loaders(self, targets: Sequence[str] | None) -> list[BaseLoader]:
        available = {loader_type.name: loader_type for loader_type in LOADER_TYPES}

        if targets is None:
            selected = set(available)
        else:
            unknown = [name for name in targets if name not in available]
            if unknown:
                raise ValueError(
                    f"Recurso(s) inválido(s): {', '.join(unknown)}. "
                    f"Disponíveis: {', '.join(available)}"
                )
            selected = set(targets)

        return [
            loader_type()
            for loader_type in LOADER_TYPES
            if loader_type.name in selected
        ]

    async def run(self, targets: Sequence[str] | None = None) -> dict[str, int]:
        loaders = self._select_loaders(targets)
        counts: dict[str, int] = {}

        async with engine.connect() as lock_connection:
            acquired = (
                await lock_connection.execute(
                    text("SELECT pg_try_advisory_lock(:key)"),
                    {"key": ADVISORY_LOCK_KEY},
                )
            ).scalar()

            if not acquired:
                raise RuntimeError(
                    "Outra execução do ETL já está em andamento (advisory lock ativo)."
                )

            try:
                async with AsyncSessionLocal() as session:  # noqa: SIM117
                    async with ComprasApiClient(
                        page_size=self.page_size,
                        concurrency=self.concurrency,
                        request_interval=self.request_interval,
                        retries=self.retries,
                    ) as client:
                        for loader in loaders:
                            logger.info(
                                "Carregando '%s' (%s) ...",
                                loader.name,
                                loader.endpoint,
                            )
                            counts[loader.name] = await loader.load(
                                session,
                                client,
                                batch_size=self.batch_size,
                                limit_pages=self.limit_pages,
                            )
                            logger.info(
                                "'%s' carregado: %s registros",
                                loader.name,
                                counts[loader.name],
                            )
            finally:
                await lock_connection.execute(
                    text("SELECT pg_advisory_unlock(:key)"),
                    {"key": ADVISORY_LOCK_KEY},
                )
                await lock_connection.commit()

        return counts
