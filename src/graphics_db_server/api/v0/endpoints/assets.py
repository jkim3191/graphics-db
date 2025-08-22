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
from graphics_db_server.sources.from_polyhaven import (
    download_material_files,
    generate_material_thumbnail,
    get_material_metadata,
)

router = APIRouter()


@router.get("/assets/search", response_model=list[Asset])
def search_assets(
    query: str, top_k: int = 5, asset_type: str = None, material_type: str = None
):
    """
    Finds the top_k most similar assets for a given query.
    Optionally filter by asset_type (model/material) and material_type (floor/wall/etc).
    """
    query_embedding = get_clip_embeddings(query)
    with get_db_connection() as conn:
        results = crud.search_assets(
            conn=conn,
            query_embedding=query_embedding,
            top_k=top_k,
            asset_type=asset_type,
            material_type=material_type,
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


# Material-specific endpoints


@router.get("/materials/search", response_model=list[Asset])
def search_materials(query: str, top_k: int = 5, material_type: str = None):
    """
    Search specifically for materials (floor/wall textures) from Poly Haven.
    """
    query_embedding = get_clip_embeddings(query)
    with get_db_connection() as conn:
        results = crud.search_assets(
            conn=conn,
            query_embedding=query_embedding,
            top_k=top_k,
            asset_type="material",
            material_type=material_type,
        )
    if not results:
        logger.debug(f"No material results found for query: {query}")
        return []
    else:
        return results


class MaterialFilesRequest(BaseModel):
    material_id: str
    resolution: str = "2k"
    maps: list[str] = ["Diffuse"]


@router.post("/materials/files")
def get_material_files(request: MaterialFilesRequest):
    """
    Download and get local paths for material texture files.
    """
    downloaded_files = download_material_files(
        asset_id=request.material_id, resolution=request.resolution, maps=request.maps
    )

    return JSONResponse(content={"files": downloaded_files})


class MaterialThumbnailsRequest(BaseModel):
    material_ids: list[str]


@router.post("/materials/thumbnails")
def get_material_thumbnails(request: MaterialThumbnailsRequest):
    """
    Generate thumbnails for material assets.
    """
    response_data = {}

    for material_id in request.material_ids:
        thumbnail_path = generate_material_thumbnail(material_id)

        with open(thumbnail_path, "rb") as f:
            image_data = f.read()
        response_data[material_id] = base64.b64encode(image_data).decode("utf-8")

    return JSONResponse(content=response_data)


@router.get("/materials/{material_id}/metadata")
def get_material_metadata_endpoint(material_id: str):
    """
    Get runtime metadata for a material asset (resolution options, maps, etc.).
    """
    metadata = get_material_metadata(material_id)
    return JSONResponse(content=metadata)
