import uuid
from typing import Optional

import numpy as np
from pydantic import BaseModel, ConfigDict


class Asset(BaseModel):
    uid: uuid.UUID
    url: str
    tags: Optional[list[str]] = []
    source: str
    # sourceId: str  # NOTE: let's try not to keep this unless really necessary
    license: str

    model_config = ConfigDict(from_attributes=True)


class AssetCreate(Asset):
    embedding: list[float] | np.ndarray

    model_config = ConfigDict(arbitrary_types_allowed=True)


# class SearchResult(BaseModel):
#     raise NotImplementedError
#     # NOTE: Let's keep the schema simple for now.
