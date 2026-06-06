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
    """Internal pressure only makes sense for the hollow cylinder"""
    if CYLINDER_TYPE != "hollow":
        raise ValueError('Set CYLINDER_TYPE = "hollow" in config.py before using internal pressure.')


def add_support_boundary_condition(model):
    """Fix the bottom face so the tube is stable during pressurize"""
    model.boundary_.add_bc(
        feb.boundary.BCZeroDisplacement(
            node_set=FIXED_NODE_SET,
            x_dof=1,
            y_dof=1,
            z_dof=1,
        )
    )


def add_internal_pressure(model):
    """Apply pressure to the inner wall of the hollow cylinder"""
    model.loads_.add_surface_load(
        feb.loads.PressureLoad(
            surface=PRESSURE_SURFACE,
            pressure=feb.loads.Scale(lc=1, text=INTERNAL_PRESSURE),
        )
    )


def main():
    """Build a FEBio file for pressure loading from the inside wall"""
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
