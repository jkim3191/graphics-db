"""
Create, Read, Update, Delete operations in the database.
"""

import json
from typing import List

import numpy as np
from psycopg.rows import dict_row

from graphics_db_server.core.config import TABLE_NAME
from graphics_db_server.schemas.asset import Asset
from graphics_db_server.logging import logger
from graphics_db_server.sources.from_polyhaven import derive_material_type


def search_assets(conn, query_embedding: np.ndarray, top_k: int, 
                  asset_type: str = None, material_type: str = None) -> list[dict]:
    """
    Search assets with optional filtering by asset type and material type.
    """
    where_conditions = []
    params = {"query_vector": query_embedding}
    
    if asset_type:
        where_conditions.append("asset_type = %(asset_type)s")
        params["asset_type"] = asset_type
    
    # For material_type filtering, we need to filter by tags containing the material type
    if material_type:
        where_conditions.append("%(material_type)s = ANY(tags)")
        params["material_type"] = material_type
    
    where_clause = ""
    if where_conditions:
        where_clause = "WHERE " + " AND ".join(where_conditions)
    
    # Get more results initially for material_type post-filtering
    search_limit = top_k * 3 if material_type else top_k
    params["limit"] = search_limit
    
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"""
            SELECT
                uid,
                url,
                tags,
                source,
                license,
                asset_type,
                1 - (embedding <=> %(query_vector)s) AS similarity_score
            FROM {TABLE_NAME}
            {where_clause}
            ORDER BY embedding <=> %(query_vector)s
            LIMIT %(limit)s;
            """,
            params,
        )
        results = cur.fetchall()
    
    # Post-process results to add material metadata and apply material_type filtering
    filtered_results = []
    for result in results:
        # Convert to Asset object for consistent interface
        asset_data = {
            "uid": result["uid"],
            "url": result["url"],
            "tags": result["tags"],
            "source": result["source"],
            "license": result["license"],
            "asset_type": result["asset_type"],
            "similarity_score": result["similarity_score"]
        }
        
        # For materials, add derived material_type if needed
        if result["asset_type"] == "material" and material_type:
            derived_type = derive_material_type(result["tags"])
            if derived_type == material_type:
                filtered_results.append(asset_data)
        else:
            filtered_results.append(asset_data)
        
        # Stop when we have enough results
        if len(filtered_results) >= top_k:
            break
    
    if not filtered_results:
        logger.warning("No results found. The database might be empty.")
    return filtered_results[:top_k]


def insert_assets(conn, assets: List[Asset]):
    """
    Inserts assets into the database.
    """
    data = []

    for asset in assets:
        data.append(
            (
                asset.uid,
                asset.url,
                asset.tags,
                asset.source,
                asset.license,
                asset.asset_type,
                asset.embedding,
            )
        )

    with conn.cursor() as cur:
        cur.executemany(
            """INSERT INTO assets (
                uid, url, tags, source, license, asset_type, embedding
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            data,
        )
        conn.commit()

    logger.success(f"Inserted {len(assets)} assets.")
