import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict


class Asset(BaseModel):
    id: uuid.UUID
    url: str
    tags: Optional[list[str]] = []
    source: str
    sourceId: str

    model_config = ConfigDict(from_attributes=True)


class SearchResult(BaseModel):
    raise NotImplementedError
    # NOTE: Let's keep the schema simple for now.
