from pathlib import Path
import sys

from h5py._hl.attrs import AttributeManager
import numpy as np
from pyfebio import xplt


sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import (
    COMPRESSION_DISPLACEMENT_Z,
    CYLINDER_HEIGHT,
    CYLINDER_INNER_RADIUS,
    CYLINDER_RADIUS,
    CYLINDER_TYPE,
    FEB_FILE,
    LOAD_CASE,
    YOUNG_MODULUS,
)
from febio_step.result_helpers import (
    calculate_compression_stiffness,
    calculate_percent_difference,
    calculate_theoretical_compression_stiffness,
    read_last_result_values,
    read_reaction_forces_for_node_set,
)


XPLT_FILE = FEB_FILE.with_suffix(".xplt")
HDF5_FILE = FEB_FILE.with_suffix(".hdf5")
LOG_FILE = FEB_FILE.with_suffix(".log")


def febio_finished_normally():
    """Check the FEBio log for the normal termination message.

    Returns True if the log file exists and contains the 'N O R M A L'
    termination phrase.
    """
    if not LOG_FILE.exists():
        return False

    return 'N O R M A L   T E R M I N A T I O N' in LOG_FILE.read_text()


def convert_xplt_to_hdf5():
def convert_xplt_to_hdf5():
    """Convert a FEBio '.xplt' file to HDF5 for easier access in Python.

    This writes 'HDF5_FILE' and temporarily patches h5py to avoid storing a
    duplicate 'faces' attribute that can get huge on fine meshes.
    """
    if not XPLT_FILE.exists():
        raise FileNotFoundError(f"FEBio xplt file was not found: {XPLT_FILE}")

    original_set_attribute = AttributeManager.__setitem__

    def skip_duplicate_surface_faces_attribute(attribute_manager, name, value):
        # pyfebio already saves surface faces as datasets
        # on fine meshes the duplicate hdf5 attribute gets too large
        if name == "faces":
            return

        original_set_attribute(attribute_manager, name, value)

    AttributeManager.__setitem__ = skip_duplicate_surface_faces_attribute

    try:
        xplt.to_hdf5(inputfile=str(XPLT_FILE), outputfile=str(HDF5_FILE))
    finally:
        AttributeManager.__setitem__ = original_set_attribute


def print_result_summary(name, values):
def print_result_summary(name, values):
    """Print simple stats (count, max, mean, min/max components).

    name : str
        Header printed for the section.
    values : np.ndarray
        Array of vectors (N x dim).
    """
    magnitude = np.linalg.norm(values, axis=1)

    print(f"\n{name.lower()}")
    print(f"- number of values: {len(values)}")
    print(f"- maximum magnitude: {magnitude.max()}")
    print(f"- average magnitude: {magnitude.mean()}")
    print(f"- minimum components: {values.min(axis=0)}")
    print(f"- maximum components: {values.max(axis=0)}")


def print_compression_stiffness(top_face_reaction_forces):
def print_compression_stiffness(top_face_reaction_forces):
    """Compute and print stiffness vs simple theory for the top face.

    Parameters:
    top_face_reaction_forces : np.ndarray
        Reaction forces for nodes on the top face (N x 3).

    Prints a short comparison between FEBio stiffness and the E*A/L formula.
    """
    total_reaction_force, z_reaction_force, stiffness = calculate_compression_stiffness(
        top_face_reaction_forces,
        COMPRESSION_DISPLACEMENT_Z,
    )
    theoretical_stiffness = calculate_theoretical_compression_stiffness(
        CYLINDER_TYPE,
        CYLINDER_RADIUS,
        CYLINDER_INNER_RADIUS,
        CYLINDER_HEIGHT,
        YOUNG_MODULUS,
    )
    stiffness_difference = calculate_percent_difference(stiffness, theoretical_stiffness)

    print("\ncompression stiffness")
    print(f"- total reaction force on top face: {total_reaction_force}")
    print(f"- z reaction force: {z_reaction_force}")
    print(f"- prescribed displacement: {COMPRESSION_DISPLACEMENT_Z}")
    print(f"- febio stiffness: {stiffness}")
    print(f"- simple theoretical stiffness: {theoretical_stiffness}")
    print(f"- difference from theory: {stiffness_difference}%")
    print("- note: the theoretical value uses the same model units as the geometry and material settings")


def main():
def main():
    """Convert the '.xplt' to HDF5 and print a short summary of results.

    The function is tolerant of missing or non-convertible '.xplt' files and
    checks the FEBio log to report whether the run finished normally.
    """
    print(f"reading febio result file: {XPLT_FILE}")

    try:
        convert_xplt_to_hdf5()
    except FileNotFoundError as error:
        print("\nresult extraction warning")
        print("- the expected febio xplt result file was not found")
        print("- this usually means the febio model has not been run yet after the latest config change")
        print(f"- missing file: {XPLT_FILE}")
        print(f"- error: {error}")
        return
    except OSError as error:
        print("\nresult extraction warning")
        print("- febio created an xplt result file, but python could not convert it to hdf5")

        if febio_finished_normally():
            print("- the febio log still shows normal termination, so the simulation itself finished")
        else:
            print("- the febio log does not show normal termination, so the simulation should be checked")

        print(f"- conversion error: {error}")
        return

    result_values = read_last_result_values(HDF5_FILE)

    print("\nresult summary")
    print(f"- last state: {result_values['last_state']}")
    print(f"- last time: {result_values['last_time']}")
    print_result_summary("displacement", result_values["displacement"])
    print_result_summary("reaction forces", result_values["reaction_forces"])
    print_result_summary("stress", result_values["stress"])
    print_result_summary("lagrange strain", result_values["strain"])

    if LOAD_CASE == "compression":
        top_face_reaction_forces = read_reaction_forces_for_node_set(
            HDF5_FILE,
            result_values["reaction_forces"],
            "top_face",
        )
        print_compression_stiffness(top_face_reaction_forces)


if __name__ == "__main__":
    main()
