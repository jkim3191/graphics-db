from pgvector.psycopg import register_vector
from psycopg_pool import ConnectionPool

from graphics_db_server.core.config import (
    db_settings,
    EMBEDDING_DIMS,
    INDEX_NAME,
    INDEX_TYPE,
    SIMILARITY_OPS,
    TABLE_NAME,
)
from graphics_db_server.logging import logger

EXTENSION_ENABLE_SQL = """
CREATE EXTENSION IF NOT EXISTS vectorscale CASCADE;
"""  # CASCADE auto-installs pgvector

TABLE_CREATION_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id UUID PRIMARY KEY,
    url TEXT,
    tags TEXT[],
    embedding VECTOR({EMBEDDING_DIMS})
)
"""

INDEX_CREATION_SQL = f"""
CREATE INDEX IF NOT EXISTS {INDEX_NAME}
ON {TABLE_NAME}
USING {INDEX_TYPE} (embedding {SIMILARITY_OPS})
"""


def setup_databse():
    """Connects to DB and runs setup commands."""

    pool = ConnectionPool(conninfo=db_settings.DATABASE_URL)
    with pool.getconn() as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            logger.info("Enabling extensions...")
            cur.execute(EXTENSION_ENABLE_SQL)
            logger.info("Extensions are ready.")

            logger.info("Creating table...")
            cur.execute(TABLE_CREATION_SQL)
            logger.info(f"Table {TABLE_NAME} is ready.")

            logger.info("Creating index...")
            cur.execute(INDEX_CREATION_SQL)
            logger.info("Index is ready.")

        conn.commit()
    pool.close()
    logger.success("Database setup complete.")


if __name__ == "__main__":
    setup_databse()
