import json
import uuid

import psycopg
import numpy as np
from pgvector.psycopg import register_vector

# TODO: import logger

CONN_STRING = "postgresql://user:password@host:port/dbname"  # TODO: replace with config


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
        cur.excutemany(
            "INSERT INTO assets (id, asset_url, bounding_box, tags, embedding) VALUES (%s, %s, %s, %s, %s)",
            data,
        )

if __name__ == "__main__":
    with psycopg.connect(CONN_STRING) as conn:
        register_vector(conn)  # registers vector type into database
        insert_assets(conn, )

    # What a single asset looks like:
    # asset_id = uuid.uuid4()  # NOTE: may have to reuse existing id
    # asset_url = ""  # TODO
    # bounding_box = {}  # TODO
    # tags = []  # TODO
    # embedding = np.random.rand(768)  # TODO
