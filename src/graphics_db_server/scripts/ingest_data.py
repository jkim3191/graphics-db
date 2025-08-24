from graphics_db_server.db.crud import insert_assets
from graphics_db_server.db.session import get_db_connection
from graphics_db_server.sources.from_objaverse import load_objaverse_assets
from graphics_db_server.sources.from_polyhaven import load_polyhaven_assets
from graphics_db_server.logging import logger


if __name__ == "__main__":
    logger.info("Ingesting data...")
    with get_db_connection() as conn:
        # Load Objaverse assets
        logger.info("Loading Objaverse assets...")
        # objaverse_assets = load_objaverse_assets(limit=10)
        objaverse_assets = load_objaverse_assets()
        logger.info(f"Loaded {len(objaverse_assets)} Objaverse assets")
        
        # Load Poly Haven assets (start with small sample)
        logger.info("Loading Poly Haven assets...")
        polyhaven_assets = load_polyhaven_assets(limit=50, asset_type="textures")
        logger.info(f"Loaded {len(polyhaven_assets)} Poly Haven assets")
        
        # Combine and insert all assets
        all_assets = objaverse_assets + polyhaven_assets
        logger.info(f"Inserting {len(all_assets)} total assets...")
        insert_assets(conn, all_assets)
        
    logger.info("Ingesting data complete")
