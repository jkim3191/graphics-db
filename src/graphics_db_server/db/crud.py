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


def search_assets(conn, query_embedding: np.ndarray, top_k: int) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"""
            SELECT
                id,
                url,
                1 - (embedding <=> %(query_vector)s) AS similarity_score
            FROM {TABLE_NAME}
            ORDER BY embedding <=> %(query_vector)s
            LIMIT %(limit)s;
            """,
            {"query_vector": query_embedding, "limit": top_k},
        )
        results = cur.fetchall()
    return results


def insert_assets(conn, assets: List[Asset]):
    """
    Inserts assets into the database.
    """
    data = []

    for asset in assets:
        data.append(
            (
                asset.id,
                asset.url,
                json.dumps(asset.bounding_box),
                asset.tags,
                asset.embedding,
            )
        )

    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO assets (id, asset_url, bounding_box, tags, embedding) VALUES (%s, %s, %s, %s, %s)",
            data,
        )

    logger.success(f"Inserted {len(assets)} assets.")
