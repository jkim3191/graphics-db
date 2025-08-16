# app/db/session.py

from contextlib import contextmanager
from psycopg_pool import ConnectionPool
from pgvector.psycopg import register_vector

from graphics_db_server.core.config import settings

# reusable connection pool
pool = ConnectionPool(conninfo=str(settings.DATABASE_URL))


@contextmanager
def get_db_connection():
    """
    A context manager to get a connection from the pool and ensure it's returned.
    """
    conn = pool.getconn()
    try:
        # This is required for every connection!
        register_vector(conn)
        yield conn
    finally:
        pool.putconn(conn)
