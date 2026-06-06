"""Experimental mesh script for the real stent STEP file.

The normal pipeline still uses the simple cylinder. This file is only for
testing whether the inner boundary of the stent can be selected automatically.
"""

from pathlib import Path
import sys

import gmsh

sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import ROOT


STENT_STEP_FILE = ROOT / "stent.step"
STENT_MSH_FILE = ROOT / "gmsh_step" / "stent_inner_selection.msh"

# The stent STEP needed quite tolerant healing settings in the Gmsh GUI.
GEOMETRY_TOLERANCE = 1e-2
MESH_SIZE_MIN = 0.01
MESH_SIZE_MAX = 0.1

# The real stent has many tiny faces. The inner and outer cylindrical
# boundaries are much larger, so this keeps the selection focused on those.
MIN_BOUNDARY_AREA = 10


def set_gmsh_options():
    """Use the healing and mesh settings that helped in the Gmsh GUI."""
    gmsh.option.setNumber("Geometry.Tolerance", GEOMETRY_TOLERANCE)
    gmsh.option.setNumber("Geometry.OCCFixDegenerated", 1)
    gmsh.option.setNumber("Geometry.OCCFixSmallEdges", 1)
    gmsh.option.setNumber("Geometry.OCCFixSmallFaces", 1)
    gmsh.option.setNumber("Geometry.OCCSewFaces", 1)
    gmsh.option.setNumber("Geometry.OCCMakeSolids", 1)

    gmsh.option.setNumber("Mesh.MeshSizeMin", MESH_SIZE_MIN)
    gmsh.option.setNumber("Mesh.MeshSizeMax", MESH_SIZE_MAX)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)


def get_model_center():
    """Get the center of the full stent bounding box in x and y."""
    x_min, y_min, _z_min, x_max, y_max, _z_max = gmsh.model.getBoundingBox(-1, -1)

    center_x = (x_min + x_max) / 2
    center_y = (y_min + y_max) / 2

    return center_x, center_y


def get_surface_radius_from_bounding_box(surface_tag, center_x, center_y):
    """Estimate the cylinder radius covered by one surface bounding box."""
    x_min, y_min, _z_min, x_max, y_max, _z_max = gmsh.model.getBoundingBox(2, surface_tag)

    radius_x = max(abs(x_min - center_x), abs(x_max - center_x))
    radius_y = max(abs(y_min - center_y), abs(y_max - center_y))

    return (radius_x + radius_y) / 2


def collect_surface_info():
    """Collect the area and approximate radius of every boundary surface."""
    center_x, center_y = get_model_center()
    surface_info = []

    for _dim, surface_tag in gmsh.model.getEntities(2):
        area = gmsh.model.occ.getMass(2, surface_tag)
        radius = get_surface_radius_from_bounding_box(surface_tag, center_x, center_y)
        surface_info.append(
            {
                "tag": surface_tag,
                "area": area,
                "radius": radius,
            }
        )

    return surface_info


def find_inner_and_outer_wall(surface_info):
    """Find the large inner and outer cylindrical boundaries."""
    large_surfaces = [
        surface for surface in surface_info
        if surface["area"] >= MIN_BOUNDARY_AREA
    ]

    if len(large_surfaces) < 2:
        raise RuntimeError("Could not find two large cylindrical stent boundaries.")

    large_surfaces.sort(key=lambda surface: surface["radius"])

    inner_wall = large_surfaces[0]
    outer_wall = large_surfaces[-1]

    return inner_wall, outer_wall


def add_stent_labels(inner_wall, outer_wall):
    """Add Physical Groups so Gmsh/FEBio can see the selected stent regions."""
    volumes = gmsh.model.getEntities(3)

    if not volumes:
        raise RuntimeError(f"No 3d volume found in STEP file: {STENT_STEP_FILE}")

    gmsh.model.addPhysicalGroup(
        3,
        [tag for _dim, tag in volumes],
        tag=1,
        name="stent_volume",
    )
    gmsh.model.addPhysicalGroup(2, [inner_wall["tag"]], tag=2, name="inner_wall")
    gmsh.model.addPhysicalGroup(2, [outer_wall["tag"]], tag=3, name="outer_wall")


def print_selection_summary(inner_wall, outer_wall):
    """Print what was selected so it can be checked in Gmsh/FEBio Studio."""
    print("\nstent boundary selection")
    print(
        f"- inner_wall: surface {inner_wall['tag']}, "
        f"area {inner_wall['area']:.4f}, radius {inner_wall['radius']:.4f}"
    )
    print(
        f"- outer_wall: surface {outer_wall['tag']}, "
        f"area {outer_wall['area']:.4f}, radius {outer_wall['radius']:.4f}"
    )


def main():
    gmsh.initialize()
    gmsh.model.add("stent")

    try:
        set_gmsh_options()
        gmsh.model.occ.importShapes(str(STENT_STEP_FILE))
        gmsh.model.occ.synchronize()

        surface_info = collect_surface_info()
        inner_wall, outer_wall = find_inner_and_outer_wall(surface_info)

        add_stent_labels(inner_wall, outer_wall)
        print_selection_summary(inner_wall, outer_wall)

        gmsh.model.mesh.generate(3)
        gmsh.write(str(STENT_MSH_FILE))
        print(f"\nstent mesh written to: {STENT_MSH_FILE}")

    finally:
        gmsh.finalize()


if __name__ == "__main__":
    main()
