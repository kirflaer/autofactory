from typing import List

from pydantic.dataclasses import dataclass

from tasks.models import TaskBaseModel


@dataclass
class PalletContent:
    key: str
    count: int


@dataclass
class WriteOffTaskContent:
    pallets: List[PalletContent]


class WriteOffTask(TaskBaseModel):
    content: WriteOffTaskContent
