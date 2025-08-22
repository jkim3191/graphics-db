from graphics_db_server.db.crud import insert_assets
from graphics_db_server.db.session import get_db_connection
from graphics_db_server.sources.from_objaverse import load_objaverse_assets
from graphics_db_server.sources.from_polyhaven import load_polyhaven_materials
from graphics_db_server.logging import logger


if __name__ == "__main__":
    logger.info("Ingesting data...")
    with get_db_connection() as conn:
        # assets = load_objaverse_assets(limit=10)
        assets = load_objaverse_assets()
        insert_assets(conn, assets)
        
        materials = load_polyhaven_materials(limit=50)  # Start with limited materials
        insert_assets(conn, materials)
    logger.info("Ingesting data complete")
