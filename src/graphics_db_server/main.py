import psycopg
from fastapi import FastAPI, HTTPException

from graphics_db_server.api.v0.endpoints import assets
from graphics_db_server.db.session import get_db_connection
from graphics_db_server.logging import configure_logging, logger

configure_logging()

app = FastAPI(title="Graphics DB API")
app.include_router(assets.router, prefix="/api/v0", tags=["Assets"])


@app.get("/healthcheck")
def healthcheck():
    """
    Check database connection.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return {"status": "ok", "db": "ok"}
    except psycopg.Error as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")
