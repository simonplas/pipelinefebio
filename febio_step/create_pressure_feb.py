from pathlib import Path
import sys

import pyfebio as feb

sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import CYLINDER_TYPE, INTERNAL_PRESSURE, PRESSURE_FEB_FILE, PRESSURE_SURFACE
from febio_step.febio_helpers import (
    FIXED_NODE_SET,
    add_load_curve,
    add_output_requests,
    add_solver_control,
    add_stainless_steel_material,
    print_febio_mesh_summary,
    read_mesh_for_febio,
)


def check_geometry_type():
    """Ensure the geometry is a hollow cylinder for internal pressure.

    Raises ValueError if 'CYLINDER_TYPE' is not 'hollow'.
    """
    if CYLINDER_TYPE != "hollow":
        raise ValueError('Set CYLINDER_TYPE = "hollow" in config.py before using internal pressure.')


def add_support_boundary_condition(model):
    """Add a fixed support BC on the 'FIXED_NODE_SET'.

    Parameters:
    model : feb.model.Model
        The pyfebio model to modify.

    Adds a zero-displacement BC fixing x, y and z on the fixed node set.
    """
    model.boundary_.add_bc(
        feb.boundary.BCZeroDisplacement(
            node_set=FIXED_NODE_SET,
            x_dof=1,
            y_dof=1,
            z_dof=1,
        )
    )


def add_internal_pressure(model):
    """Apply an internal pressure load to the configured surface.

    Parameters:
    model : feb.model.Model
        The pyfebio model to update.

    Adds a PressureLoad on 'PRESSURE_SURFACE' scaled by 'INTERNAL_PRESSURE'.
    """
    model.loads_.add_surface_load(
        feb.loads.PressureLoad(
            surface=PRESSURE_SURFACE,
            pressure=feb.loads.Scale(lc=1, text=INTERNAL_PRESSURE),
        )
    )


def main():
    """Create and save the FEBio input file for the internal pressure case.

    Side effects:
    - Loads the mesh via 'read_mesh_for_febio()'.
    - Writes the FEB file to 'PRESSURE_FEB_FILE'.
    """
    check_geometry_type()

    febio_mesh = read_mesh_for_febio()
    print_febio_mesh_summary(febio_mesh)

    model = feb.model.Model(mesh_=febio_mesh)

    add_solver_control(model)
    add_stainless_steel_material(model)
    add_support_boundary_condition(model)
    add_internal_pressure(model)
    add_load_curve(model)
    add_output_requests(model)

    output_folder = PRESSURE_FEB_FILE.parent
    output_folder.mkdir(parents=True, exist_ok=True)

    model.save(str(PRESSURE_FEB_FILE))

    print(f"\nPressure FEBio file written: {PRESSURE_FEB_FILE}")


if __name__ == "__main__":
    main()
