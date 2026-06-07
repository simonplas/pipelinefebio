"""Helpful bits for building FEBio models.

The compression and pressure scripts share mesh, material, solver, load curve
and output setup. Keeping these helpers here avoids copying code between the
load cases.
"""

from pathlib import Path
import sys

import meshio
import pyfebio as feb

sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import (
    DENSITY,
    FEBIO_OUTPUT_STRIDE,
    FEBIO_PLOT_STRIDE,
    FEBIO_STEP_SIZE,
    FEBIO_TIME_STEPS,
    MATERIAL_NAME,
    MSH_FILE,
    POISSON_RATIO,
    YOUNG_MODULUS,
)

FIXED_NODE_SET = "bottom_face"
SOLID_PART = "stent_volume"

def print_febio_mesh_summary(mesh):
    """Print a quick summary of parts, surfaces and node sets found.

    Parameters:
    mesh : feb.mesh.Mesh
        The pyfebio mesh returned by 'feb.mesh.translate_meshio'.

    This just prints what labels FEBio sees so we can sanity-check the mesh.
    """
    solid_parts = [elements.name for elements in mesh.elements]
    surfaces = [surface.name for surface in mesh.surfaces]
    node_sets = [node_set.name for node_set in mesh.node_sets]

    print("\nFEBio found these mesh labels:")
    print(f"- solid parts: {', '.join(solid_parts)}")
    print(f"- surfaces: {', '.join(surfaces)}")
    print(f"- node sets: {', '.join(node_sets)}")


def read_mesh_for_febio():
    """Load the Gmsh '.msh' and translate it to a pyfebio mesh.

    Returns the pyfebio mesh object that contains 'elements', 'surfaces' and
    'node_sets'.
    """
    print(f"Reading Gmsh mesh: {MSH_FILE}")

    gmsh_mesh = meshio.gmsh.read(MSH_FILE)
    febio_mesh = feb.mesh.translate_meshio(gmsh_mesh)

    return febio_mesh


def add_stainless_steel_material(model):
    """Add a simple isotropic elastic material and a matching solid domain.

    Parameters:
    model : feb.model.Model
        The pyfebio model to update.

    The function registers a material with the name from config and creates
    a solid domain that expects elements labelled 'SOLID_PART'.
    """
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
    """Add a basic linear load curve (0 -> 1) with id=1.

    The boundary conditions and loads in the models reference this curve (lc=1).
    """
    model.loaddata_.add_load_curve(
        feb.loaddata.LoadCurve(
            id=1,
            points=feb.loaddata.CurvePoints(points=["0.0,0.0", "1.0,1.0"]),
        )
    )


def add_output_requests(model):
    """Tell FEBio to write a standard set of variables to the plotfile.

    This requests displacement, stress, Lagrange strain and reaction forces.
    """
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
    """Set a basic control block with time steps and output stride.

    Parameters:
    model : feb.model.Model
        The model to configure.

    Uses values from 'config.py'.
    """
    model.control_ = feb.control.Control(
        time_steps=FEBIO_TIME_STEPS,
        step_size=FEBIO_STEP_SIZE,
        plot_stride=FEBIO_PLOT_STRIDE,
        output_stride=FEBIO_OUTPUT_STRIDE,
    )
    
