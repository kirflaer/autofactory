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
class InventoryAddressContent:
    key: str
    fact: int


class InventoryAddressTask(TaskBaseModel):
    content: List[InventoryAddressContent] | None
