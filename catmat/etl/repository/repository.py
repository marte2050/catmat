from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase


async def existing_codes(
    session: AsyncSession,
    model: type[DeclarativeBase],
    column_name: str,
    codes: Iterable[Any],
) -> set[Any]:
    values = set(codes)
    if not values:
        return set()

    column = getattr(model, column_name)
    result = await session.execute(select(column).where(column.in_(values)))
    return set(result.scalars().all())


def model_to_row(instance: DeclarativeBase) -> dict[str, Any]:
    return {column.key: getattr(instance, column.key) for column in instance.__table__.columns}


def model_to_rows(instances: Iterable[DeclarativeBase]) -> list[dict[str, Any]]:
    return [model_to_row(instance) for instance in instances]


def dedupe_rows(
    rows: Iterable[dict[str, Any]],
    index_elements: Sequence[str],
) -> list[dict[str, Any]]:
    """Remove linhas com chave repetida; a última ocorrência vence.

    O PostgreSQL não permite que um mesmo `ON CONFLICT DO UPDATE` afete a mesma
    linha duas vezes numa instrução, e a API pode devolver chaves duplicadas na
    mesma página.
    """
    deduped: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in rows:
        key = tuple(row[element] for element in index_elements)
        deduped[key] = row
    return list(deduped.values())


def _chunks(rows: Sequence[dict[str, Any]], size: int) -> Iterable[Sequence[dict[str, Any]]]:
    for start in range(0, len(rows), size):
        yield rows[start : start + size]


async def bulk_upsert(
    session: AsyncSession,
    model: type[DeclarativeBase],
    instances: Sequence[DeclarativeBase],
    *,
    index_elements: Sequence[str],
    update_columns: Sequence[str] | None = None,
    chunk_size: int = 1000,
) -> int:
    if not instances:
        return 0

    if update_columns is None:
        primary_keys = {column.key for column in model.__table__.primary_key.columns}
        update_columns = [
            column.key
            for column in model.__table__.columns
            if column.key not in primary_keys
        ]

    rows = dedupe_rows(model_to_rows(instances), index_elements)
    for chunk in _chunks(rows, chunk_size):
        statement = insert(model).values(list(chunk))
        if update_columns:
            statement = statement.on_conflict_do_update(
                index_elements=list(index_elements),
                set_={
                    column: getattr(statement.excluded, column)
                    for column in update_columns
                },
            )
        else:
            statement = statement.on_conflict_do_nothing(
                index_elements=list(index_elements)
            )
        await session.execute(statement)

    return len(rows)


async def bulk_insert_ignore(
    session: AsyncSession,
    model: type[DeclarativeBase],
    instances: Sequence[DeclarativeBase],
    *,
    index_elements: Sequence[str],
    chunk_size: int = 1000,
) -> int:
    """Insere em lote ignorando conflitos (`INSERT ... ON CONFLICT DO NOTHING`)."""
    if not instances:
        return 0

    rows = dedupe_rows(model_to_rows(instances), index_elements)
    for chunk in _chunks(rows, chunk_size):
        statement = insert(model).values(list(chunk)).on_conflict_do_nothing(
            index_elements=list(index_elements)
        )
        await session.execute(statement)

    return len(rows)
