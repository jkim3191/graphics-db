import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from graphics_db_server.api.v0.endpoints import assets
from graphics_db_server.core.config import TABLE_NAME
from graphics_db_server.db.session import get_db_connection
from graphics_db_server.logging import configure_logging, logger

configure_logging(level="DEBUG")

app = FastAPI(title="Graphics DB API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assets.router, prefix="/api/v0", tags=["Assets"])


@app.get("/healthcheck")
def healthcheck():
    """
    Check database connection and if data is loaded.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")

                cur.execute(f"SELECT EXISTS (SELECT 1 FROM {TABLE_NAME});")
                data_exists = cur.fetchone()[0]

        return {"status": "ok", "db": "ok", "data_exists": data_exists}
    except psycopg.Error as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")
