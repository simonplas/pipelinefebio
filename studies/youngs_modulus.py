"""run the compression simulation with several youngs modulus values

this keeps the mesh fixed and only changes the material stiffness
that makes it easier to see if the pipeline reacts in a logical way
"""

import csv
import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from config import (
    COMPRESSION_DISPLACEMENT_Z,
    COMPRESSION_FEB_FILE,
    CYLINDER_HEIGHT,
    CYLINDER_INNER_RADIUS,
    CYLINDER_RADIUS,
)
from febio_step.result_helpers import (
    calculate_compression_stiffness,
    calculate_percent_difference,
    calculate_theoretical_compression_stiffness,
    maximum_magnitude,
    read_last_result_values,
    read_reaction_forces_for_node_set,
)


MAIN_SCRIPT = ROOT / "main.py"
RESULTS_FOLDER = ROOT / "study_results"
RESULTS_FILE = RESULTS_FOLDER / "youngs_modulus.csv"
HDF5_FILE = COMPRESSION_FEB_FILE.with_suffix(".hdf5")

# keep the mesh fixed so mesh effects and material effects do not get mixed
MESH_SIZE = 0.5
CYLINDER_TYPES = ["solid", "hollow"]

# pa
# 193e9 is the stainless steel value used in the normal pipeline
YOUNG_MODULUS_VALUES = [50e9, 100e9, 150e9, 193e9, 250e9]


def calculate_result_numbers(cylinder_type, young_modulus):
    """Grab numbers from the HDF5 and compute extra metrics for the run.

    Parameters:
    cylinder_type : str
        'solid' or 'hollow'.
    young_modulus : float
        The Young's modulus used in this run.

    Returns:
    dict
        Results including nodes, elements, max values, reaction force and
        stiffness compared to theory.
    """
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
    theoretical_stiffness = calculate_theoretical_compression_stiffness(
        cylinder_type,
        CYLINDER_RADIUS,
        CYLINDER_INNER_RADIUS,
        CYLINDER_HEIGHT,
        young_modulus,
    )
    stiffness_error_percent = calculate_percent_difference(compression_stiffness, theoretical_stiffness)

    return {
        "nodes": result_values["nodes"],
        "elements": result_values["elements"],
        "max_displacement": maximum_magnitude(result_values["displacement"]),
        "max_stress": maximum_magnitude(result_values["stress"]),
        "max_strain": maximum_magnitude(result_values["strain"]),
        "z_reaction_force": z_reaction_force,
        "compression_stiffness": compression_stiffness,
        "theoretical_stiffness": theoretical_stiffness,
        "stiffness_error_percent": stiffness_error_percent,
    }


def remove_old_hdf5_file():
    """Delete the previous HDF5 output so we don't accidentally read old data.

    Called before each new pipeline run in the study.
    """
    if HDF5_FILE.exists():
        HDF5_FILE.unlink()


def run_pipeline_with_settings(cylinder_type, young_modulus):
    """Run the main pipeline once with temporary environment variables.

    Parameters:
    cylinder_type : str
        'solid' or 'hollow'.
    young_modulus : float
        Young's modulus for this run.

    Returns:
    dict
        Result numbers plus how long the run took.
    """
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
    result_numbers = calculate_result_numbers(cylinder_type, young_modulus)
    result_numbers["cylinder_type"] = cylinder_type
    result_numbers["mesh_size"] = MESH_SIZE
    result_numbers["young_modulus"] = young_modulus
    result_numbers["run_time_seconds"] = run_time

    return result_numbers


def write_results(rows):
    """Save the current list of study rows to the CSV results file.

    Parameters:
    rows : list[dict]
        Rows produced during the study; written to 'RESULTS_FILE'.
    """
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
        "theoretical_stiffness",
        "stiffness_error_percent",
        "status",
        "error",
    ]

    with RESULTS_FILE.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    """Run the Young's modulus study and write results as they complete.

    Loops over the configured modulus values and cylinder types and saves
    progress to CSV so the study can be resumed if interrupted.
    """
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
                    "theoretical_stiffness": "",
                    "stiffness_error_percent": "",
                    "status": "failed",
                    "error": str(error),
                }

            rows.append(row)
            write_results(rows)

    print(f"\nYoung's modulus results written to: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
