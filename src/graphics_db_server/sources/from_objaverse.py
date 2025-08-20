import os
import multiprocessing
import subprocess
import uuid
from pathlib import Path
from typing import Any

import compress_pickle
import numpy as np
import objaverse

# import objaverse.xl as oxl
from pydantic import BaseModel

from graphics_db_server.schemas.asset import AssetCreate
from graphics_db_server.core.config import EMBEDDING_PATHS, USE_MEAN_POOL


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
    embeddings_path: str = EMBEDDING_PATHS["Objaverse"],
) -> dict[str, np.ndarray]:
    """
    Loads CLIP embeddings from a pickled file and returns a map from UID to embedding.

    The pickled file is expected to be a dictionary with two keys:
    - "uids": A list of object UIDs.
    - "img_features": A numpy array of CLIP image features.

    Args:
        embeddings_path: The path to the pickled embeddings file.

    Returns:
        A dictionary mapping object UIDs to their corresponding embedding vectors.
    """
    if not os.path.exists(embeddings_path):
        raise FileNotFoundError(f"Embeddings file not found at {embeddings_path}")

    embeddings_dict = compress_pickle.load(embeddings_path)
    uids_with_embeddings = embeddings_dict["uids"]
    embeddings = embeddings_dict["img_features"].astype(np.float32)
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
    embedding_map = _load_embedding_map()

    assets: list[AssetCreate] = []
    for uid, annotation in annotations.items():
        if limit is not None and len(assets) >= limit:
            break

        if not _is_valid_annotation(annotation):
            continue

        embedding = embedding_map.get(uid)
        if embedding is None:
            continue

        if embedding.ndim != 1:
            if USE_MEAN_POOL:
                embedding = embedding.mean(0)
            else:
                raise NotImplementedError()

        asset = AssetCreate(
            uid=uid,
            url=annotation.get("viewerUrl"),  # NOTE: there's also uri
            tags=_get_tag_names(annotation.get("tags")),
            source="objaverse",
            license=annotation.get("license"),
            embedding=embedding,
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


def get_thumbnails(asset_paths):
    # HACK: this is actually unfathomably hacky but whatever... it freaking works.
    subprocess.run(
        [
            "py",
            Path("~/GitHub/scripts/generate_thumbnails_for_glb.py").expanduser(),
            Path("~/.objaverse").expanduser(),
        ]
    )
    image_paths = []
    for i, (id, path) in enumerate(asset_paths.items()):
        image_path = Path(path.replace(".glb", ".png")).expanduser()
        image_paths.append(image_path)

    return image_paths


if __name__ == "__main__":
    load_objaverse_assets(limit=3)
