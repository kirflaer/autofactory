from datetime import datetime
from typing import List, NamedTuple

from pydantic.main import BaseModel
from pydantic.dataclasses import dataclass


class Mark(BaseModel):
    scan_date: datetime
    mark: str


class MarkingData(BaseModel):
    aggregation_code: str
    product: str
    marks: List[Mark]
