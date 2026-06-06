"""Run the compression simulation with several Young's modulus values.

This study keeps the mesh size fixed and only changes the material stiffness.
That makes it easier to check if the pipeline responds logically when the
material parameters are changed.
"""

import csv
import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from config import COMPRESSION_DISPLACEMENT_Z, COMPRESSION_FEB_FILE
from febio_step.result_helpers import (
    calculate_compression_stiffness,
    maximum_magnitude,
    read_last_result_values,
    read_reaction_forces_for_node_set,
)


MAIN_SCRIPT = ROOT / "main.py"
RESULTS_FOLDER = ROOT / "study_results"
RESULTS_FILE = RESULTS_FOLDER / "youngs_modulus.csv"
HDF5_FILE = COMPRESSION_FEB_FILE.with_suffix(".hdf5")

# Keep the mesh fixed, otherwise mesh effects and material effects get mixed.
MESH_SIZE = 0.5
CYLINDER_TYPES = ["solid", "hollow"]

# Pa. The 193e9 value is the stainless steel value used in the normal pipeline.
YOUNG_MODULUS_VALUES = [50e9, 100e9, 150e9, 193e9, 250e9]


def calculate_result_numbers():
    """Read the final displacement, stress, strain, reaction force, and stiffness."""
    result_values = read_last_result_values(HDF5_FILE)
    top_face_reaction_forces = read_reaction_forces_for_node_set(
        HDF5_FILE,
        result_values["reaction_forces"],
        "top_face",
    )
    _total_reaction_force, z_reaction_force, compression_stiffness = calculate_compression_stiffness(
        top_face_reaction_forces,
        COMPRESSION_DISPLACEMENT_Z,
    )

    return {
        "nodes": result_values["nodes"],
        "elements": result_values["elements"],
        "max_displacement": maximum_magnitude(result_values["displacement"]),
        "max_stress": maximum_magnitude(result_values["stress"]),
        "max_strain": maximum_magnitude(result_values["strain"]),
        "z_reaction_force": z_reaction_force,
        "compression_stiffness": compression_stiffness,
    }


def remove_old_hdf5_file():
    """Remove the previous HDF5 file so we do not read old results by mistake."""
    if HDF5_FILE.exists():
        HDF5_FILE.unlink()


def run_pipeline_with_settings(cylinder_type, young_modulus):
    """Run main.py once with a temporary cylinder type and Young's modulus."""
    print(f"\nrunning {cylinder_type} cylinder with Young's modulus {young_modulus}")

    environment = os.environ.copy()
    environment["PIPELINE_CYLINDER_TYPE"] = cylinder_type
    environment["PIPELINE_MESH_SIZE"] = str(MESH_SIZE)
    environment["PIPELINE_YOUNG_MODULUS"] = str(young_modulus)
    environment["PIPELINE_LOAD_CASE"] = "compression"
    environment["PIPELINE_PLOT_STRIDE"] = "20"
    environment["PIPELINE_OUTPUT_STRIDE"] = "20"

    remove_old_hdf5_file()

    start_time = time.perf_counter()
    subprocess.run([sys.executable, str(MAIN_SCRIPT)], cwd=ROOT, env=environment, check=True)
    end_time = time.perf_counter()

    run_time = end_time - start_time
    result_numbers = calculate_result_numbers()
    result_numbers["cylinder_type"] = cylinder_type
    result_numbers["mesh_size"] = MESH_SIZE
    result_numbers["young_modulus"] = young_modulus
    result_numbers["run_time_seconds"] = run_time

    return result_numbers


def write_results(rows):
    """Save the study results so they can be plotted later."""
    RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "cylinder_type",
        "mesh_size",
        "young_modulus",
        "nodes",
        "elements",
        "run_time_seconds",
        "max_displacement",
        "max_stress",
        "max_strain",
        "z_reaction_force",
        "compression_stiffness",
        "status",
        "error",
    ]

    with RESULTS_FILE.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    print("starting Young's modulus study")

    rows = []

    for cylinder_type in CYLINDER_TYPES:
        for young_modulus in YOUNG_MODULUS_VALUES:
            try:
                row = run_pipeline_with_settings(cylinder_type, young_modulus)
                row["status"] = "ok"
                row["error"] = ""
            except Exception as error:
                row = {
                    "cylinder_type": cylinder_type,
                    "mesh_size": MESH_SIZE,
                    "young_modulus": young_modulus,
                    "nodes": "",
                    "elements": "",
                    "run_time_seconds": "",
                    "max_displacement": "",
                    "max_stress": "",
                    "max_strain": "",
                    "z_reaction_force": "",
                    "compression_stiffness": "",
                    "status": "failed",
                    "error": str(error),
                }

            rows.append(row)
            write_results(rows)

    print(f"\nYoung's modulus results written to: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
