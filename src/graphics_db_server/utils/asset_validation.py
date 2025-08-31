import sys
from pathlib import Path
from typing import Optional

import pyvista as pv


def validate_asset_scale(glb_path: str, max_edge_length: float = 100.0) -> tuple[bool, Optional[str]]:
    """
    Validates that a GLB asset has a reasonable scale by checking if the largest bounding box edge
    exceeds the specified threshold. This helps identify assets that may be in centimeters instead
    of meters.
    
    Args:
        glb_path: Path to the GLB file to validate
        max_edge_length: Maximum allowed edge length in meters (default: 100.0)
        
    Returns:
        tuple: (is_valid, reason) where is_valid is True if the asset passes validation,
               and reason is a string explaining why validation failed (if applicable)
    """
    try:
        # Create an off-screen plotter to load the GLB file
        plotter = pv.Plotter(off_screen=True)
        plotter.import_gltf(glb_path)
        
        # Get the bounds of all actors in the scene
        bounds = plotter.renderer.ComputeVisiblePropBounds()
        plotter.close()
        
        if len(bounds) != 6:
            return False, "Could not compute bounding box"
        
        # Calculate the size of each dimension
        x_size = abs(bounds[1] - bounds[0])  # xmax - xmin
        y_size = abs(bounds[3] - bounds[2])  # ymax - ymin  
        z_size = abs(bounds[5] - bounds[4])  # zmax - zmin
        
        # Find the largest edge
        max_edge = max(x_size, y_size, z_size)
        
        if max_edge > max_edge_length:
            return False, f"Asset too large: max edge is {max_edge:.2f}m (limit: {max_edge_length}m)"
        
        return True, None
        
    except Exception as e:
        return False, f"Error validating asset: {str(e)}"


def is_valid_asset_scale(glb_path: str, max_edge_length: float = 100.0) -> bool:
    """
    Simple boolean check for asset scale validation.
    
    Args:
        glb_path: Path to the GLB file to validate
        max_edge_length: Maximum allowed edge length in meters (default: 100.0)
        
    Returns:
        bool: True if the asset passes validation, False otherwise
    """
    is_valid, _ = validate_asset_scale(glb_path, max_edge_length)
    return is_valid


def validate_asset_scales(asset_paths: dict[str, str], max_edge_length: float = 100.0) -> dict[str, bool]:
    """
    Validates the scale of downloaded GLB assets to reject those that are too large
    (likely in centimeters instead of meters).

    Args:
        asset_paths: A dictionary mapping asset UIDs to their .glb file paths.
        max_edge_length: Maximum allowed edge length in meters (default: 100.0)

    Returns:
        A dictionary mapping asset UIDs to validation results (True if valid, False if rejected).
    """
    validation_results = {}
    for uid, glb_path_str in asset_paths.items():
        glb_path = Path(glb_path_str).resolve()

        if not glb_path.exists():
            validation_results[uid] = False
            print(f"WARNING: GLB file not found for asset {uid}: {glb_path}")
            continue

        is_valid, reason = validate_asset_scale(str(glb_path), max_edge_length)
        validation_results[uid] = is_valid

        if not is_valid:
            print(f"INFO: Rejecting asset {uid}: {reason}")
        else:
            print(f"INFO: Asset {uid} passed scale validation")

    return validation_results
