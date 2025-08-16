from graphics_db_server.db.crud import insert_assets
from graphics_db_server.db.session import get_db_connection
from graphics_db_server.sources.from_objaverse import load_objaverse_assets


if __name__ == "__main__":
    with get_db_connection() as conn:
        assets = load_objaverse_assets(limit=10)
        insert_assets(conn, assets)
