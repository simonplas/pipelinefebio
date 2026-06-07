"""First FEBio pressure model for the experimental stent mesh.

This is a small, separate script used to test whether the labelled stent
mesh can be translated to FEBio and run. It's not part of the normal
cylinder pipeline.
"""

from pathlib import Path
import sys

import meshio
import numpy as np
import pyfebio as feb

sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import ROOT
from febio_step.febio_helpers import (
    add_load_curve,
    add_output_requests,
    add_solver_control,
    add_stainless_steel_material,
    print_febio_mesh_summary,
)


STENT_MSH_FILE = ROOT / "gmsh_step" / "stent_inner_selection.msh"
STENT_JOB_DIR = ROOT / "febio_step" / "jobs" / "stent"
STENT_FEB_FILE = STENT_JOB_DIR / "pressure_stent.feb"

PRESSURE_SURFACE = "inner_wall"
# Keep this small for the first stent test. A high pressure can invert the
# small tetrahedral elements before the solver has a chance to converge.
INTERNAL_PRESSURE = 1.0e5
SUPPORT_NODE_COUNT = 10


def read_stent_mesh():
    """Read the labelled stent '.msh' and return meshio + pyfebio meshes.

    Returns a tuple (gmsh_mesh, febio_mesh) where gmsh_mesh is the meshio mesh
    and febio_mesh is the translated pyfebio mesh.
    """
    print(f"reading stent mesh: {STENT_MSH_FILE}")

    gmsh_mesh = meshio.gmsh.read(STENT_MSH_FILE)
    febio_mesh = feb.mesh.translate_meshio(gmsh_mesh)

    return gmsh_mesh, febio_mesh


def node_id_from_point_index(point_index):
    """Convert a numpy point index (0-based) to a FEBio node id (1-based)."""
    return int(point_index) + 1


def find_nodes_closest_to_target(points, target, amount):
    """Find a few mesh nodes closest to a target point.

    Returns the indices of the closest nodes.
    """
    distances = np.linalg.norm(points - target, axis=1)
    closest_nodes = np.argsort(distances)

    return [int(node_index) for node_index in closest_nodes[:amount]]


def add_support_node_set(gmsh_mesh, febio_mesh):
    """Add a small 'support_nodes' set to the pyfebio mesh.

    Parameters:
    gmsh_mesh : meshio.Mesh
        The original meshio mesh used to find candidate nodes.
    febio_mesh : feb.mesh.Mesh
        The pyfebio mesh that will receive the node set.

    This mutates 'febio_mesh' by adding a NodeSet named 'support_nodes'.
    """
    points = gmsh_mesh.points
    min_corner = points.min(axis=0)
    max_corner = points.max(axis=0)
    target = np.array([max_corner[0], max_corner[1], (min_corner[2] + max_corner[2]) / 2])

    support_node_indices = find_nodes_closest_to_target(points, target, SUPPORT_NODE_COUNT)
    support_node_ids = [
        node_id_from_point_index(node_index)
        for node_index in support_node_indices
    ]

    node_text = ",".join(str(node_id) for node_id in support_node_ids)
    febio_mesh.add_node_set(feb.mesh.NodeSet(name="support_nodes", text=node_text))

    print("\nadded support nodes:")
    print(f"- support_nodes: {support_node_ids}")


def add_support_boundary_conditions(model):
    """Add a fixed BC for the small 'support_nodes' set.

    Parameters:
    model : feb.model.Model
        The pyfebio model to update.
    """
    model.boundary_.add_bc(
        feb.boundary.BCZeroDisplacement(
            node_set="support_nodes",
            x_dof=1,
            y_dof=1,
            z_dof=1,
        )
    )


def add_internal_pressure(model):
    """Apply a PressureLoad to the surface named by 'PRESSURE_SURFACE'.

    Parameters:
    model : feb.model.Model
        The pyfebio model to update.
    """
    model.loads_.add_surface_load(
        feb.loads.PressureLoad(
            surface=PRESSURE_SURFACE,
            pressure=feb.loads.Scale(lc=1, text=INTERNAL_PRESSURE),
        )
    )


def main():
    """Create and save a FEBio input file for the labelled stent mesh.

    Side effects:
    - Reads the stent '.msh' file.
    - Adds a small support node set to the translated pyfebio mesh.
    - Writes the FEB file to 'STENT_FEB_FILE'.
    """
    gmsh_mesh, febio_mesh = read_stent_mesh()
    add_support_node_set(gmsh_mesh, febio_mesh)
    print_febio_mesh_summary(febio_mesh)

    model = feb.model.Model(mesh_=febio_mesh)

    add_solver_control(model)
    add_stainless_steel_material(model)
    add_support_boundary_conditions(model)
    add_internal_pressure(model)
    add_load_curve(model)
    add_output_requests(model)

    STENT_JOB_DIR.mkdir(parents=True, exist_ok=True)
    model.save(str(STENT_FEB_FILE))

    print(f"\nstent pressure FEBio file written: {STENT_FEB_FILE}")


if __name__ == "__main__":
    main()
