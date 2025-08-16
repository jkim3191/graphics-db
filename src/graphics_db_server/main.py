from fastapi import FastAPI

from graphics_db_server.api.v0.endpoints import assets
from graphics_db_server.logging import configure_logging

configure_logging()

app = FastAPI(title="Graphics DB API")
app.include_router(assets.router, prefix="/api/v0", tags=["Assets"])


@app.get("/")
def read_root():
    """
    Health check endpoint.
    """
    return {"status": "ok"}
