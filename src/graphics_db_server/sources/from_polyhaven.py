import os
import requests
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import numpy as np
from PIL import Image
import io

from graphics_db_server.schemas.asset import AssetCreate
from graphics_db_server.core.config import (
    POLY_HAVEN_API_BASE,
    POLY_HAVEN_CDN_BASE,
    MATERIAL_CACHE_DIR,
    DEFAULT_MATERIAL_RESOLUTION,
    SUPPORTED_MATERIAL_TYPES,
    THUMBNAIL_RESOLUTION,
)
from graphics_db_server.embeddings.clip import get_clip_embeddings


# Runtime utility functions for material metadata
def get_material_metadata(asset_id: str) -> Dict[str, Any]:
    """
    Get runtime material metadata for a Poly Haven asset.
    
    Returns:
        Dictionary with resolution_options, material_maps, physical_dimensions, material_type
    """
    try:
        # Get asset info from Poly Haven API
        assets_url = f"{POLY_HAVEN_API_BASE}/assets/{asset_id}"
        response = requests.get(assets_url, timeout=10)
        response.raise_for_status()
        asset_data = response.json()
        
        # Get resolution options and material maps
        resolution_options = _get_available_resolutions(asset_id)
        material_maps = _get_material_maps(asset_id)
        
        # Extract physical dimensions
        dimensions = asset_data.get("dimensions")
        physical_dimensions = None
        if dimensions and len(dimensions) >= 2:
            physical_dimensions = [dimensions[0] / 1000.0, dimensions[1] / 1000.0]
        
        # Derive material type from categories
        categories = asset_data.get("categories", [])
        material_type = derive_material_type(categories)
        
        return {
            "resolution_options": resolution_options,
            "material_maps": material_maps,
            "physical_dimensions": physical_dimensions,
            "material_type": material_type,
            "categories": categories
        }
    except Exception as e:
        print(f"Warning: Could not fetch material metadata for {asset_id}: {e}")
        return {
            "resolution_options": ["1k", "2k"],
            "material_maps": ["Diffuse"],
            "physical_dimensions": None,
            "material_type": None,
            "categories": []
        }


def derive_material_type(categories_or_tags: List[str]) -> Optional[str]:
    """
    Derive material type from categories or tags.
    
    Args:
        categories_or_tags: List of categories or tags
        
    Returns:
        Material type string or None
    """
    for cat in categories_or_tags:
        if cat in ["floor", "wall", "brick", "wood", "concrete", "plaster-concrete"]:
            print(f"Found matching material type: {cat}")
            return cat
    print("No matching material type found, returning None")
    return None


def _is_valid_material(asset_data: Dict[str, Any]) -> bool:
    """
    Checks if a Poly Haven asset is a valid material for floor/wall use.
    """
    # Must be a texture (type=1)
    if asset_data.get("type") != 1:
        return False

    # Must have required fields
    required_fields = ["name", "categories", "tags", "thumbnail_url", "max_resolution"]
    if not all(field in asset_data for field in required_fields):
        print("Missing required fields, returning False")
        return False

    # Must have categories that match our supported material types
    categories = asset_data.get("categories", [])
    if not any(cat in SUPPORTED_MATERIAL_TYPES for cat in categories):
        print("No matching material type found, returning False")
        return False

    return True


def _extract_material_info(asset_id: str, asset_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts relevant material information from Poly Haven asset data.
    """
    categories = asset_data.get("categories", [])
    tags = asset_data.get("tags", [])

    # Determine material type based on categories
    material_type = None
    for cat in categories:
        if cat in ["floor", "wall", "brick", "wood", "concrete", "plaster-concrete"]:
            material_type = cat
            break

    # Get physical dimensions if available
    dimensions = asset_data.get("dimensions")
    physical_dimensions = None
    if dimensions and len(dimensions) >= 2:
        # Convert from mm to meters if needed (Poly Haven uses different units)
        physical_dimensions = [dimensions[0] / 1000.0, dimensions[1] / 1000.0]

    return {
        "uid": asset_id,
        "name": asset_data.get("name"),
        "categories": categories,
        "tags": tags,
        "material_type": material_type,
        "thumbnail_url": asset_data.get("thumbnail_url"),
        "max_resolution": asset_data.get("max_resolution", []),
        "physical_dimensions": physical_dimensions,
        "date_published": asset_data.get("date_published"),
        "download_count": asset_data.get("download_count", 0),
    }


def _get_available_resolutions(asset_id: str) -> List[str]:
    """
    Get available resolutions for a material by querying the files endpoint.
    """
    try:
        files_url = f"{POLY_HAVEN_API_BASE}/files/{asset_id}"
        response = requests.get(files_url, timeout=10)
        response.raise_for_status()

        files_data = response.json()

        # Extract available resolutions from the first material map (usually Diffuse)
        resolutions = []
        for map_type in ["Diffuse", "diffuse"]:
            if map_type in files_data:
                resolutions = list(files_data[map_type].keys())
                break

        # Sort resolutions properly (1k, 2k, 4k, 8k)
        resolution_order = {"1k": 1, "2k": 2, "4k": 4, "8k": 8}
        resolutions.sort(key=lambda x: resolution_order.get(x, 0))

        return resolutions
    except Exception as e:
        print(f"Warning: Could not fetch resolutions for {asset_id}: {e}")
        return ["1k", "2k"]  # Default fallback


def _get_material_maps(asset_id: str) -> List[str]:
    """
    Get available material maps (Diffuse, Normal, etc.) for a material.
    """
    try:
        files_url = f"{POLY_HAVEN_API_BASE}/files/{asset_id}"
        response = requests.get(files_url, timeout=10)
        response.raise_for_status()

        files_data = response.json()

        # Map internal names to standardized names
        map_mapping = {
            "Diffuse": "Diffuse",
            "nor_gl": "Normal",
            "nor_dx": "Normal_DX",
            "Rough": "Roughness",
            "AO": "AO",
            "Displacement": "Displacement",
            "arm": "ARM",  # Ambient occlusion, Roughness, Metallic
        }

        available_maps = []
        for internal_name, standard_name in map_mapping.items():
            if internal_name in files_data:
                available_maps.append(standard_name)

        return available_maps
    except Exception as e:
        print(f"Warning: Could not fetch material maps for {asset_id}: {e}")
        return ["Diffuse"]  # Default fallback


def load_polyhaven_materials(limit: Optional[int] = None) -> List[AssetCreate]:
    """
    Loads material metadata from Poly Haven API.
    """
    print("Loading materials from Poly Haven...")

    # Fetch all texture assets
    assets_url = f"{POLY_HAVEN_API_BASE}/assets?type=textures"

    try:
        response = requests.get(assets_url, timeout=30)
        response.raise_for_status()
        all_assets = response.json()
    except requests.RequestException as e:
        print(f"Error fetching Poly Haven assets: {e}")
        return []

    print(f"Found {len(all_assets)} total textures from Poly Haven")

    materials: List[AssetCreate] = []
    processed_count = 0

    for asset_id, asset_data in all_assets.items():
        if limit is not None and len(materials) >= limit:
            break

        processed_count += 1
        if processed_count % 100 == 0:
            print(f"Processed {processed_count}/{len(all_assets)} assets...")

        # Validate material
        if not _is_valid_material(asset_data):
            continue

        # Extract material information
        material_info = _extract_material_info(asset_id, asset_data)

        # Generate text for embedding (combine name, categories, and tags)
        text_for_embedding = f"{material_info['name']} {' '.join(material_info['categories'])} {' '.join(material_info['tags'])}"

        # Generate CLIP embedding from text
        try:
            embeddings = get_clip_embeddings([text_for_embedding])
            if len(embeddings) == 0:
                print(f"Warning: No embedding generated for {asset_id}")
                continue
            embedding = embeddings[0]
        except Exception as e:
            print(f"Warning: Could not generate embedding for {asset_id}: {e}")
            continue

        # Combine categories and tags for storage in tags field
        all_tags = material_info["tags"] + material_info["categories"]

        # Create asset with simplified schema
        asset = AssetCreate(
            uid=asset_id,
            url=material_info["thumbnail_url"],
            tags=all_tags,  # Store categories + tags together
            source="polyhaven",
            license="CC0",
            asset_type="material",
            embedding=embedding,
        )

        materials.append(asset)

    print(f"Successfully loaded {len(materials)} materials from Poly Haven")
    return materials


def download_material_files(
    asset_id: str,
    resolution: str = DEFAULT_MATERIAL_RESOLUTION,
    maps: Optional[List[str]] = None,
) -> Dict[str, str]:
    """
    Downloads material files from Poly Haven for a specific asset.

    Args:
        asset_id: Poly Haven asset ID
        resolution: Resolution to download (1k, 2k, 4k, 8k)
        maps: List of maps to download. If None, downloads Diffuse only.

    Returns:
        Dictionary mapping map types to local file paths
    """
    if maps is None:
        maps = ["Diffuse"]

    # Create cache directory
    cache_dir = Path(MATERIAL_CACHE_DIR).expanduser() / asset_id / resolution
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Get file URLs from Poly Haven API
    files_url = f"{POLY_HAVEN_API_BASE}/files/{asset_id}"

    try:
        response = requests.get(files_url, timeout=10)
        response.raise_for_status()
        files_data = response.json()
    except requests.RequestException as e:
        print(f"Error fetching file data for {asset_id}: {e}")
        return {}

    downloaded_files = {}

    # Map standardized names back to Poly Haven internal names
    map_reverse_mapping = {
        "Diffuse": "Diffuse",
        "Normal": "nor_gl",
        "Normal_DX": "nor_dx",
        "Roughness": "Rough",
        "AO": "AO",
        "Displacement": "Displacement",
        "ARM": "arm",
    }

    for map_type in maps:
        internal_name = map_reverse_mapping.get(map_type, map_type)

        if internal_name not in files_data:
            print(f"Warning: Map {map_type} not available for {asset_id}")
            continue

        resolution_data = files_data[internal_name].get(resolution)
        if not resolution_data:
            print(
                f"Warning: Resolution {resolution} not available for {map_type} in {asset_id}"
            )
            continue

        # Prefer JPG for smaller file size, fallback to PNG
        file_url = None
        file_ext = None
        if "jpg" in resolution_data:
            file_url = resolution_data["jpg"]["url"]
            file_ext = "jpg"
        elif "png" in resolution_data:
            file_url = resolution_data["png"]["url"]
            file_ext = "png"

        if not file_url:
            print(f"Warning: No supported format for {map_type} in {asset_id}")
            continue

        # Download file
        local_path = (
            cache_dir / f"{asset_id}_{map_type.lower()}_{resolution}.{file_ext}"
        )

        if local_path.exists():
            print(f"Using cached file: {local_path}")
            downloaded_files[map_type] = str(local_path)
            continue

        try:
            print(f"Downloading {map_type} map for {asset_id}...")
            file_response = requests.get(file_url, timeout=60)
            file_response.raise_for_status()

            with open(local_path, "wb") as f:
                f.write(file_response.content)

            downloaded_files[map_type] = str(local_path)
            print(f"Downloaded: {local_path}")

        except requests.RequestException as e:
            print(f"Error downloading {map_type} for {asset_id}: {e}")

    return downloaded_files


def generate_material_thumbnail(
    asset_id: str, output_path: Optional[str] = None
) -> Optional[str]:
    """
    Generates a thumbnail for a material by downloading and processing the diffuse map.

    Args:
        asset_id: Poly Haven asset ID
        output_path: Optional output path. If None, saves to cache directory.

    Returns:
        Path to generated thumbnail or None if failed
    """
    # Download diffuse map at low resolution for thumbnail
    downloaded_files = download_material_files(
        asset_id, resolution="1k", maps=["Diffuse"]
    )

    if "Diffuse" not in downloaded_files:
        print(f"Could not download diffuse map for thumbnail generation: {asset_id}")
        return None

    diffuse_path = downloaded_files["Diffuse"]

    try:
        # Open and resize image
        with Image.open(diffuse_path) as img:
            # Convert to RGB if needed
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Resize to thumbnail size
            img.thumbnail(
                (THUMBNAIL_RESOLUTION, THUMBNAIL_RESOLUTION), Image.Resampling.LANCZOS
            )

            # Save thumbnail
            if output_path is None:
                cache_dir = Path(MATERIAL_CACHE_DIR).expanduser() / asset_id
                cache_dir.mkdir(parents=True, exist_ok=True)
                output_path = cache_dir / f"{asset_id}_thumbnail.jpg"

            img.save(output_path, "JPEG", quality=85, optimize=True)
            print(f"Generated thumbnail: {output_path}")
            return str(output_path)

    except Exception as e:
        print(f"Error generating thumbnail for {asset_id}: {e}")
        return None


if __name__ == "__main__":
    # Test loading a few materials
    materials = load_polyhaven_materials(limit=5)
    print(f"Loaded {len(materials)} test materials")

    if materials:
        # Test downloading files for the first material
        test_material = materials[0]
        print(f"Testing download for material: {test_material.uid}")
        files = download_material_files(test_material.uid, resolution="1k")
        print(f"Downloaded files: {files}")

        # Test thumbnail generation
        thumbnail = generate_material_thumbnail(test_material.uid)
        print(f"Generated thumbnail: {thumbnail}")
