from typing import List
from pydantic.dataclasses import dataclass
from tasks.models import TaskBaseModel
from pydantic.main import BaseModel


@dataclass
class PalletContent:
    key: str
    count: int
    weight: int


class WriteOffTaskContent(BaseModel):
    pallets: List[PalletContent] | None
    comment: str | None


class WriteOffTask(TaskBaseModel):
    content: WriteOffTaskContent | None


class ProductContent(BaseModel):
    key: str
    count: int
    weight: int


@dataclass
class InventoryAddressWarehouseTaskContent:
    products: List[ProductContent]


class InventoryAddressWarehouseTask(TaskBaseModel):
    content: InventoryAddressWarehouseTaskContent
