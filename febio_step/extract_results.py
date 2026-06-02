from pathlib import Path
import sys

import h5py
import numpy as np
from pyfebio import xplt


sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import COMPRESSION_DISPLACEMENT_Z, FEB_FILE, LOAD_CASE


XPLT_FILE = FEB_FILE.with_suffix(".xplt")
HDF5_FILE = FEB_FILE.with_suffix(".hdf5")
LOG_FILE = FEB_FILE.with_suffix(".log")


def febio_finished_normally():
    """Check the FEBio log file for a normal termination message."""
    if not LOG_FILE.exists():
        return False

    return "N O R M A L   T E R M I N A T I O N" in LOG_FILE.read_text()


def convert_xplt_to_hdf5():
    """Convert FEBio's xplt result file to hdf5 so Python can read it."""
    if not XPLT_FILE.exists():
        raise FileNotFoundError(f"FEBio xplt file was not found: {XPLT_FILE}")

    xplt.to_hdf5(inputfile=str(XPLT_FILE), outputfile=str(HDF5_FILE))


def read_group_values(group):
    """Read all datasets inside one HDF5 group."""
    values = []

    for dataset_name in group:
        values.append(group[dataset_name][:])

    return np.vstack(values)


def read_last_results():
    """Read the main result fields from the last time step."""
    with h5py.File(HDF5_FILE, "r") as result_file:
        states_group = result_file["states"]
        state_numbers = sorted(states_group.keys(), key=int)
        last_state = state_numbers[-1]

        last_state_group = states_group[last_state]
        last_time_attribute = last_state_group.attrs["time"]
        last_time = last_time_attribute[0]

        node_data_group = last_state_group["node_data"]
        element_data_group = last_state_group["element_data"]

        displacement_group = node_data_group["displacement"]
        reaction_force_group = node_data_group["reaction forces"]
        stress_group = element_data_group["stress"]
        strain_group = element_data_group["Lagrange strain"]

        displacement = read_group_values(displacement_group)
        reaction_forces = read_group_values(reaction_force_group)
        stress = read_group_values(stress_group)
        strain = read_group_values(strain_group)

        top_face_node_indices = result_file["meshes/0/nodesets/top_face"][:]
        top_face_reaction_forces = []

        for node_index in top_face_node_indices:
            reaction_force_at_node = reaction_forces[node_index]
            top_face_reaction_forces.append(reaction_force_at_node)

        top_face_reaction_forces = np.array(top_face_reaction_forces)

    return last_state, last_time, displacement, reaction_forces, top_face_reaction_forces, stress, strain


def print_result_summary(name, values):
    magnitude = np.linalg.norm(values, axis=1)

    print(f"\n{name.lower()}")
    print(f"- number of values: {len(values)}")
    print(f"- maximum magnitude: {magnitude.max()}")
    print(f"- average magnitude: {magnitude.mean()}")
    print(f"- minimum components: {values.min(axis=0)}")
    print(f"- maximum components: {values.max(axis=0)}")


def print_compression_stiffness(top_face_reaction_forces):
    """Estimate compression stiffness from reaction force and displacement."""
    total_reaction_force = top_face_reaction_forces.sum(axis=0)
    z_reaction_force = total_reaction_force[2]
    displacement = abs(COMPRESSION_DISPLACEMENT_Z)
    stiffness = abs(z_reaction_force) / displacement

    print("\ncompression stiffness")
    print(f"- total reaction force on top face: {total_reaction_force}")
    print(f"- z reaction force: {z_reaction_force}")
    print(f"- prescribed displacement: {COMPRESSION_DISPLACEMENT_Z}")
    print(f"- estimated stiffness: {stiffness}")


def main():
    """Print a small summary of the simulation results."""
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

    last_state, last_time, displacement, reaction_forces, top_face_reaction_forces, stress, strain = read_last_results()

    print("\nresult summary")
    print(f"- last state: {last_state}")
    print(f"- last time: {last_time}")
    print_result_summary("displacement", displacement)
    print_result_summary("reaction forces", reaction_forces)
    print_result_summary("stress", stress)
    print_result_summary("lagrange strain", strain)

    if LOAD_CASE == "compression":
        print_compression_stiffness(top_face_reaction_forces)


if __name__ == "__main__":
    main()
