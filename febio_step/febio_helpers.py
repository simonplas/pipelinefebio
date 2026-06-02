"""
helper functions for creating FEBio models.

The compression and pressure scripts use the same mesh, material, solver, load
curve, and output setup. Keeping that code here avoids importing one load case
from the other.
"""

from pathlib import Path
import sys

import meshio
import pyfebio as feb

sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import MSH_FILE

MATERIAL_NAME = "stainless_steel"
YOUNG_MODULUS = 193e9
POISSON_RATIO = 0.3
DENSITY = 8000

FIXED_NODE_SET = "bottom_face"
SOLID_PART = "stent_volume"

TIME_STEPS = 20
STEP_SIZE = 0.05


def print_febio_mesh_summary(mesh):
    """Print a short check of the labels pyfebio found in the mesh"""
    solid_parts = [elements.name for elements in mesh.elements]
    surfaces = [surface.name for surface in mesh.surfaces]
    node_sets = [node_set.name for node_set in mesh.node_sets]

    print("\nFEBio found these mesh labels:")
    print(f"- solid parts: {', '.join(solid_parts)}")
    print(f"- surfaces: {', '.join(surfaces)}")
    print(f"- node sets: {', '.join(node_sets)}")


def read_mesh_for_febio():
    """Read the Gmsh mesh and convert it to a pyfebio mesh"""
    print(f"Reading Gmsh mesh: {MSH_FILE}")

    gmsh_mesh = meshio.gmsh.read(MSH_FILE)
    febio_mesh = feb.mesh.translate_meshio(gmsh_mesh)

    return febio_mesh


def add_stainless_steel_material(model):
    """Add a stainless steel material model and assign it to the solid part"""
    material = feb.material.IsotropicElastic(
        name=MATERIAL_NAME,
        E=feb.material.MaterialParameter(text=YOUNG_MODULUS),
        v=feb.material.MaterialParameter(text=POISSON_RATIO),
        density=feb.material.MaterialParameter(text=DENSITY),
    )

    model.material_.add_material(material)
    model.meshdomains_.add_solid_domain(
        feb.meshdomains.SolidDomain(name=SOLID_PART, mat=MATERIAL_NAME)
    )


def add_load_curve(model):
    """Add a linear load curve from 0 to 100 percent."""
    model.loaddata_.add_load_curve(
        feb.loaddata.LoadCurve(
            id=1,
            points=feb.loaddata.CurvePoints(points=["0.0,0.0", "1.0,1.0"]),
        )
    )


def add_output_requests(model):
    model.output_.add_plotfile(
        feb.output.OutputPlotfile(
            all_vars=[
                feb.output.Var(type="displacement"),
                feb.output.Var(type="stress"),
                feb.output.Var(type="Lagrange strain"),
                feb.output.Var(type="reaction forces"),
            ]
        )
    )


def add_solver_control(model):
    model.control_ = feb.control.Control(
        time_steps=TIME_STEPS,
        step_size=STEP_SIZE,
        plot_stride=1,
        output_stride=1,
        time_stepper=None,
    )
