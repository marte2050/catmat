from __future__ import annotations

from catmat.etl.loaders.base import BaseLoader
from catmat.etl.loaders.classes import ClassLoader
from catmat.etl.loaders.expense_nature import ExpenseNatureLoader
from catmat.etl.loaders.group import GroupLoader
from catmat.etl.loaders.item import ItemLoader
from catmat.etl.loaders.pdm import PdmLoader
from catmat.etl.loaders.supply_unit import SupplyUnitLoader

LOADER_TYPES: tuple[type[BaseLoader], ...] = (
    GroupLoader,
    ClassLoader,
    PdmLoader,
    ItemLoader,
    ExpenseNatureLoader,
    SupplyUnitLoader,
)

RESOURCES: tuple[str, ...] = tuple(loader.name for loader in LOADER_TYPES)


def default_loaders() -> list[BaseLoader]:
    return [loader() for loader in LOADER_TYPES]


__all__ = ["LOADER_TYPES", "RESOURCES", "BaseLoader", "default_loaders"]
