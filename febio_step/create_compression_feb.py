from pathlib import Path
import sys

import pyfebio as feb

sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import COMPRESSION_DISPLACEMENT_Z, FEB_FILE
from febio_step.febio_helpers import (
    FIXED_NODE_SET,
    add_load_curve,
    add_output_requests,
    add_solver_control,
    add_stainless_steel_material,
    print_febio_mesh_summary,
    read_mesh_for_febio,
)

LOADED_NODE_SET = "top_face"


def add_compression_boundary_conditions(model):
    """Add the simple BCs used for the compression test.

    Parameters:
    model : feb.model.Model
        The pyfebio model to update.

    Adds a fixed bottom and a prescribed z-displacement on the top face.
    """
    model.boundary_.add_bc(
        feb.boundary.BCZeroDisplacement(
            node_set=FIXED_NODE_SET,
            x_dof=1,
            y_dof=1,
            z_dof=1,
        )
    )

    model.boundary_.add_bc(
        feb.boundary.BCPrescribedDisplacement(
            node_set=LOADED_NODE_SET,
            dof="z",
            value=feb.boundary.Value(lc=1, text=COMPRESSION_DISPLACEMENT_Z),
        )
    )


def main():
    """Build and save the FEBio input file for the compression test.

    Side effects:
    - Loads the mesh via 'read_mesh_for_febio()'.
    - Writes the FEB file configured in 'FEB_FILE'.
    """
    febio_mesh = read_mesh_for_febio()
    print_febio_mesh_summary(febio_mesh)

    model = feb.model.Model(mesh_=febio_mesh)

    add_solver_control(model)
    add_stainless_steel_material(model)
    add_compression_boundary_conditions(model)
    add_load_curve(model)
    add_output_requests(model)

    output_folder = FEB_FILE.parent
    output_folder.mkdir(parents=True, exist_ok=True)


    model.save(str(FEB_FILE))

    print(f"\nCompression FEBio file written: {FEB_FILE}")


if __name__ == "__main__":
    main()
