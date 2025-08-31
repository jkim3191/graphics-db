from graphics_db_server.db.crud import insert_assets
from graphics_db_server.db.session import get_db_connection
from graphics_db_server.sources.from_objaverse import load_objaverse_assets
from graphics_db_server.logging import logger

from graphics_db_server.core.config import VALIDATE_SCALE, SCALE_RESOLUTION_STRATEGY


if __name__ == "__main__":
    logger.info("Ingesting data...")
    with get_db_connection() as conn:
        options = {"validate_scale": VALIDATE_SCALE,
                    "scale_resolution_strategy": SCALE_RESOLUTION_STRATEGY}
        # assets = load_objaverse_assets(limit=10, **options)
        assets = load_objaverse_assets(**options)
        insert_assets(conn, assets)
    logger.info("Ingesting data complete")
