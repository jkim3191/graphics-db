import json
import uuid

import numpy as np

from graphics_db_server.db.session import get_db_connection
from graphics_db_server.sources.objaverse import load_objaverse_assets

# TODO: import logger


def insert_assets(conn, assets):
    """
    Inserts assets into the database.
    """
    data = []

    for asset in assets:
        data.append((
            asset.id,
            asset.url,
            json.dumps(asset.bounding_box),
            asset.tags,
            asset.embedding
        ))

    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO assets (id, asset_url, bounding_box, tags, embedding) VALUES (%s, %s, %s, %s, %s)",
            data,
        )

if __name__ == "__main__":
    with get_db_connection() as conn:
        assets = load_objaverse_assets(limit=10)
        insert_assets(conn, assets)
