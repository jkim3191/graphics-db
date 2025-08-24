import os
import multiprocessing
from pathlib import Path
from typing import Any

import compress_pickle
import numpy as np
import objaverse

# import objaverse.xl as oxl
from pydantic import BaseModel

from graphics_db_server.schemas.asset import AssetCreate
from graphics_db_server.core.config import (
    EMBEDDING_PATHS,
    USE_MEAN_POOL,
    THUMBNAIL_RESOLUTION,
)
from graphics_db_server.utils.thumbnail import generate_thumbnail_from_glb


def _is_valid_annotation(annotation: dict[str, Any]) -> bool:
    """
    Checks if an objaverse annotation has all the required fields and non-None values.
    """
    required_fields = ["uid", "viewerUrl", "tags", "license"]
    return not any(annotation.get(field) is None for field in required_fields)


def _get_tag_names(tags: list[dict[str, Any]]) -> list[str]:
    """
    Extracts the 'name' from a list of tag dictionaries.
    """
    if not isinstance(tags, list):
        return []
    return [
        tag["name"]
        for tag in tags
        if isinstance(tag, dict) and isinstance(tag.get("name"), str)
    ]


def _load_embedding_map(
    embedding_type: str,
    data_source: str = "Objaverse",
) -> dict[str, np.ndarray]:
    """
    Loads embeddings from a pickled file and returns a map from UID to embedding.

    The pickled file is expected to be a dictionary with keys for UIDs and features.

    Args:
        embedding_type: The type of embedding to load ('clip' or 'sbert').
        data_source: The name of the data source from the config.

    Returns:
        A dictionary mapping object UIDs to their corresponding embedding vectors.
    """
    path = EMBEDDING_PATHS[data_source][embedding_type]
    if not os.path.exists(path):
        raise FileNotFoundError(f"Embeddings file not found at {path}")

    embeddings_dict = compress_pickle.load(path)
    uids_with_embeddings = embeddings_dict["uids"]

    feature_key = "img_features" if embedding_type == "clip" else "text_features"
    embeddings = embeddings_dict[feature_key].astype(np.float32)

    embedding_map = {
        uid: embedding for uid, embedding in zip(uids_with_embeddings, embeddings)
    }
    return embedding_map


def load_objaverse_assets(limit: int = None) -> list[AssetCreate]:
    """
    Loads asset metadata from the objaverse dataset.
    """
    # NOTE: this will download a ~3GB file on first run.
    annotations = objaverse.load_annotations()
    clip_embedding_map = _load_embedding_map("clip")
    sbert_embedding_map = _load_embedding_map("sbert")

    assets: list[AssetCreate] = []
    for uid, annotation in annotations.items():
        if limit is not None and len(assets) >= limit:
            break

        if not _is_valid_annotation(annotation):
            continue

        clip_embedding = clip_embedding_map.get(uid)
        sbert_embedding = sbert_embedding_map.get(uid)
        if clip_embedding is None or sbert_embedding is None:
            continue

        if clip_embedding.ndim != 1:
            if USE_MEAN_POOL:
                # NOTE: The reference implementation handles this differently at query
                #       time, by taking the maximum similarity across all embeddings
                #       for a single item. This is often a more effective approach.
                clip_embedding = clip_embedding.mean(0)
            else:
                raise NotImplementedError()

        asset = AssetCreate(
            uid=uid,
            url=annotation.get("viewerUrl"),  # NOTE: there's also uri
            tags=_get_tag_names(annotation.get("tags")),
            source="objaverse",
            license=annotation.get("license"),
            asset_type="model",
            clip_embedding=clip_embedding,
            sbert_embedding=sbert_embedding,
        )
        assets.append(asset)

    return assets


def download_assets(asset_ids: list[str]):
    """
    Downloads 3D assets from Objaverse based on a list of asset UIDs.

    Args:
        asset_ids (list[str]): A list of asset UIDs to download.
    """
    processes = multiprocessing.cpu_count()
    asset_paths = objaverse.load_objects(
        uids=asset_ids, download_processes=int(processes / 2)
    )
    return asset_paths


def get_thumbnails(asset_paths: dict[str, str]) -> dict[str, Path]:
    """
    Generates thumbnails for a dictionary of asset paths.

    Args:
        asset_paths: A dictionary mapping asset UIDs to their .glb file paths.

    Returns:
        A dictionary mapping asset UIDs to the file paths of their generated thumbnails.
    """
    asset_thumbnails = {}
    for uid, glb_path_str in asset_paths.items():
        glb_path = Path(glb_path_str).resolve()
        output_path = glb_path.with_suffix(".png")

        generate_thumbnail_from_glb(
            glb_path=str(glb_path),
            output_path=str(output_path),
            resolution=THUMBNAIL_RESOLUTION,
        )

        if output_path.exists():
            asset_thumbnails[uid] = output_path

    return asset_thumbnails


if __name__ == "__main__":
    load_objaverse_assets(limit=3)
