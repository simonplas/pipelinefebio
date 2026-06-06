"""Create a first FEBio pressure model for the experimental stent mesh.

This file is separate from the normal cylinder pipeline. The stent STEP file is
more complex, so this script is only meant as a first test of whether the
labelled stent mesh can be used in FEBio.
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
    """Read the labelled stent mesh and convert it to a pyfebio mesh."""
    print(f"reading stent mesh: {STENT_MSH_FILE}")

    gmsh_mesh = meshio.gmsh.read(STENT_MSH_FILE)
    febio_mesh = feb.mesh.translate_meshio(gmsh_mesh)

    return gmsh_mesh, febio_mesh


def node_id_from_point_index(point_index):
    """FEBio node ids start at 1, while numpy point indices start at 0."""
    return int(point_index) + 1


def find_nodes_closest_to_target(points, target, amount):
    """Find a small group of mesh nodes close to a target point."""
    distances = np.linalg.norm(points - target, axis=1)
    closest_nodes = np.argsort(distances)

    return [int(node_index) for node_index in closest_nodes[:amount]]


def add_support_node_set(gmsh_mesh, febio_mesh):
    """Add one small fixed support group for the first stent pressure test."""
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
    """Fix one small node group so the stent cannot freely drift in space."""
    model.boundary_.add_bc(
        feb.boundary.BCZeroDisplacement(
            node_set="support_nodes",
            x_dof=1,
            y_dof=1,
            z_dof=1,
        )
    )


def add_internal_pressure(model):
    """Apply pressure to the labelled inner wall surface."""
    model.loads_.add_surface_load(
        feb.loads.PressureLoad(
            surface=PRESSURE_SURFACE,
            pressure=feb.loads.Scale(lc=1, text=INTERNAL_PRESSURE),
        )
    )


def main():
    """Build the first FEBio input file for the labelled stent mesh."""
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
