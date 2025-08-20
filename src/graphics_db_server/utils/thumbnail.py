import os
import sys

import pyvista as pv


def generate_thumbnail_from_glb(glb_path, output_path, resolution, overwrite=False):
    """
    Generates a thumbnail for a single .glb file using PyVista.

    Args:
        glb_path (str): The full path to the input .glb file.
        output_path (str): The full path for the output PNG thumbnail.
        resolution (int): The resolution (width and height) of the thumbnail.
        overwrite (bool): If True, overwrites the thumbnail if it already exists.
    """
    # Check if thumbnail already exists and if we should skip it
    if os.path.exists(output_path) and not overwrite:
        print(
            f"INFO: Thumbnail already exists for {os.path.basename(glb_path)}. Skipping."
        )
        return

    print(
        f"Processing: {os.path.basename(glb_path)} -> {os.path.basename(output_path)}"
    )

    try:
        # Set up the plotter for off-screen rendering
        plotter = pv.Plotter(off_screen=True, window_size=[resolution, resolution])
        # plotter = pv.Plotter(window_size=[resolution, resolution])  # DEBUG

        # Directly import GLTF/GLB
        plotter.import_gltf(glb_path)

        # Set the camera to an isometric view for a good default angle
        # Option 1
        plotter.camera.up = (0, 1, 0)  # NOTE: doesn't really work with isometric...
        # plotter.reset_camera(). # NOTE: didn't help
        # plotter.view_isometric()

        # Option 2
        plotter.view_vector(vector=[1, 1, 1], viewup=[0, 1, 0])

        # Optional: add XYZ axes annotation gizmo
        plotter.add_axes()

        # # Optional: Use parallel projection for a clearer, more technical look
        # plotter.enable_parallel_projection()

        # Take a screenshot and save it
        # plotter.show()  # DEBUG
        plotter.screenshot(output_path, transparent_background=True)

        # Clean up and close the plotter to free memory
        plotter.close()

        print(f"SUCCESS: Created thumbnail {os.path.basename(output_path)}")

    except Exception as e:
        print(
            f"ERROR: Could not process {os.path.basename(glb_path)}. Reason: {e}",
            file=sys.stderr,
        )
