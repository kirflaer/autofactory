from typing import List
from pydantic.dataclasses import dataclass
from tasks.models import TaskBaseModel


@dataclass
class PalletContent:
    key: str
    count: int
    weight: int


@dataclass
class WriteOffTaskContent:
    pallets: List[PalletContent]


class WriteOffTask(TaskBaseModel):
    content: WriteOffTaskContent | None


@dataclass
class ProductContent:
    plan: int
    fact: int
    product: str


@dataclass
class InventoryAddressWarehouseTaskContent:
    products: List[ProductContent]


class InventoryAddressWarehouseTask(TaskBaseModel):
    content: InventoryAddressWarehouseTaskContent
