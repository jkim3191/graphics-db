import os

from pydantic import BaseModel

# Consts
# Database
TABLE_NAME = "assets"
EMBEDDING_DIMS = 768
INDEX_NAME = "assets_vec_idx"
INDEX_TYPE = "diskann"
SIMILARITY_OPS = "vector_cosine_ops"

# Data sources
EMBEDDING_PATHS = {"Objaverse": "data/objaverse/clip_features.pkl"}

# App
USE_MEAN_POOL = True
THUMBNAIL_RESOLUTION = 1024


class DBSettings(BaseModel):
    pguser: str = os.environ["POSTGRES_USER"]
    pgpass: str = os.environ["POSTGRES_PASSWORD"]
    pgname: str = os.environ["POSTGRES_DB"]
    pghost: str = os.environ.get("POSTGRES_HOST", "db")
    port: str = os.environ.get("POSTGRES_PORT", "5432")
    DATABASE_URL: str = f"postgresql://{pguser}:{pgpass}@{pghost}:{port}/{pgname}"


db_settings = DBSettings()
