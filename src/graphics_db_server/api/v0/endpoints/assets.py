import numpy as np
from fastapi import APIRouter

from graphics_db_server.db.session import get_db_connection
from graphics_db_server.db import crud
from graphics_db_server.schemas.asset import SearchResult

router = APIRouter()


@router.post("/search", response_model=list[SearchResult])
def search_assets(query_vector: list[float], top_k: int = 5):
    """
    Finds the top_k most similar assets for a given query vector.
    """
    with get_db_connection() as conn:
        results = crud.search_similar_assets(conn=conn, query_embedding=np.array())
    if not results:
        return []
    else:
        return results
