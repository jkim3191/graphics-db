import numpy as np
from fastapi import APIRouter

from graphics_db_server.db.session import get_db_connection
from graphics_db_server.db import crud
from graphics_db_server.embeddings.clip import get_clip_embeddings
from graphics_db_server.logging import logger
from graphics_db_server.schemas.asset import Asset

router = APIRouter()


@router.get("/v0/assets/search", response_model=list[Asset])
def search_assets(query: str, top_k: int = 5):
    """
    Finds the top_k most similar assets for a given query.
    """
    query_embedding = get_clip_embeddings(query)
    logger.info(f"{query_embedding=}")
    with get_db_connection() as conn:
        results = crud.search_assets(
            conn=conn, query_embedding=query_embedding, top_k=top_k
        )
    if not results:
        return []
    else:
        return results
