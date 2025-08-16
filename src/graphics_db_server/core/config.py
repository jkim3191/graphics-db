from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn

# Consts
TABLE_NAME = "assets"
EMBEDDING_DIMS = 768
INDEX_NAME = "assets_vec_idx"
INDEX_TYPE = "diskann"
SIMILARITY_OPS = "vector_cosine_ops"

EMBEDDING_PATHS = {"Objaverse": "data/objaverse/clip_features.pkl"}


class DBSettings(BaseSettings):
    DATABASE_URL: PostgresDsn
    SettingsConfigDict(env_file=".env")


db_settings = DBSettings()
