import base64
import numpy as np
from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from graphics_db_server.db.session import get_db_connection
from graphics_db_server.db import crud
from graphics_db_server.embeddings.clip import get_clip_embeddings
from graphics_db_server.logging import logger
from graphics_db_server.schemas.asset import Asset
from graphics_db_server.sources.from_objaverse import (
    download_assets,
    get_thumbnails,
)

router = APIRouter()


@router.get("/assets/search", response_model=list[Asset])
def search_assets(query: str, top_k: int = 5):
    """
    Finds the top_k most similar assets for a given query.
    """
    query_embedding = get_clip_embeddings(query)
    with get_db_connection() as conn:
        results = crud.search_assets(
            conn=conn, query_embedding=query_embedding, top_k=top_k
        )
    if not results:
        logger.debug(f"No results found for query: {query}")
        return []
    else:
        return results


class AssetThumbnailsRequest(BaseModel):
    asset_uids: list[str]


@router.post("/assets/thumbnails")
def get_asset_thumbnails(request: AssetThumbnailsRequest):
    """
    Gets asset thumbnails for a list of asset UIDs.
    """
    asset_paths = download_assets(request.asset_uids)
    asset_thumbnails = get_thumbnails(asset_paths)

    response_data = {}
    for uid, image_path in asset_thumbnails.items():
        with open(image_path, "rb") as f:
            image_data = f.read()
        response_data[uid] = base64.b64encode(image_data).decode("utf-8")

    return JSONResponse(content=response_data)
