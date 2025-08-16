"""
Create, Read, Update, Delete operations in the database.
"""

import numpy as np
from psycopg.rows import dict_row


def search_assets(conn, query_embedding: np.ndarray, top_k: int) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT
                id,
                url,
                1 - (embedding <=> %(query_vector)s) AS similarity_score
            FROM assets
            ORDER BY embedding <=> %(query_vector)s
            LIMIT %(limit)s;
            """,
            {"query_vector": query_embedding, "limit": top_k},
        )
        results = cur.fetchall()
    return results
