import uuid
from typing import Any

import numpy as np
import objaverse
from pydantic import BaseModel

from graphics_db_server.schemas.asset import AssetCreate


def _is_valid_annotation(annotation: dict[str, Any]) -> bool:
    """
    Checks if an objaverse annotation has all the required fields and non-None values.
    """
    required_fields = ["fileIdentifier", "tags", "boundingBox"]
    return not any(annotation.get(field) is None for field in required_fields)


def load_objaverse_assets(limit: int = None) -> list[AssetCreate]:
    """
    Loads asset metadata from the objaverse dataset.
    """
    # NOTE: this will download a ~3GB file on first run.
    annotations = objaverse.load_annotations()

    assets: list[AssetCreate] = []
    for uid, annotation in annotations.items():
        if limit is not None and len(assets) >= limit:
            break

        if not _is_valid_annotation(annotation):
            continue

        # Construct URL from file identifier
        url = f"https://huggingface.co/datasets/allenai/objaverse/resolve/main/{annotation['fileIdentifier']}"

        asset = AssetCreate(
            id=uuid.uuid4(),
            url=url,
            tags=annotation.get("tags"),
            source="objaverse",
            sourceId="",  # TODO
            license="",  # TODO
            embedding="",  # TODO
            # bounding_box=annotation.get("boundingBox"),  # ?
        )
        assets.append(asset)

    return assets
