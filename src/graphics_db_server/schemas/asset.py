import uuid
from typing import Optional

import numpy as np
from pydantic import BaseModel, ConfigDict


class Asset(BaseModel):
    id: uuid.UUID
    url: str
    tags: Optional[list[str]] = []
    source: str
    sourceId: str
    license: str

    model_config = ConfigDict(from_attributes=True)


class AssetCreate(Asset):
    embedding: list[float] | np.ndarray


class SearchResult(BaseModel):
    raise NotImplementedError
    # NOTE: Let's keep the schema simple for now.
