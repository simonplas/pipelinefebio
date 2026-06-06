"""Small helper functions for reading FEBio result files."""

import h5py
import numpy as np


def read_values_from_group(group):
    """Read all datasets in a HDF5 group and combine them into one array."""
    values = []

    for dataset_name in group:
        values.append(group[dataset_name][:])

    return np.vstack(values)


def get_last_state(result_file):
    """Get the final saved time step from the FEBio result file."""
    states_group = result_file["states"]
    state_numbers = sorted(states_group.keys(), key=int)
    last_state_number = state_numbers[-1]

    return last_state_number, states_group[last_state_number]


def count_elements(result_file):
    """Count how many volume elements are stored in the FEBio result file."""
    domains_group = result_file["meshes/0/domains"]
    total_elements = 0

    for domain_name in domains_group:
        domain_elements = domains_group[domain_name]
        total_elements += len(domain_elements)

    return total_elements


def read_node_set(result_file, node_set_name):
    """Read one named node set from the first mesh in the result file."""
    node_sets_group = result_file["meshes/0/nodesets"]

    if node_set_name not in node_sets_group:
        raise KeyError(f"node set was not found in the FEBio result file: {node_set_name}")

    return node_sets_group[node_set_name][:]


def read_last_result_values(hdf5_file):
    """Read the main result values from the last saved time step."""
    with h5py.File(hdf5_file, "r") as result_file:
        nodes = result_file["meshes/0/nodes"]
        number_of_nodes = len(nodes)
        number_of_elements = count_elements(result_file)

        last_state_number, last_state = get_last_state(result_file)
        last_time = last_state.attrs["time"][0]

        node_data = last_state["node_data"]
        element_data = last_state["element_data"]

        displacement = read_values_from_group(node_data["displacement"])
        reaction_forces = read_values_from_group(node_data["reaction forces"])
        stress = read_values_from_group(element_data["stress"])
        strain = read_values_from_group(element_data["Lagrange strain"])

    return {
        "last_state": last_state_number,
        "last_time": last_time,
        "nodes": number_of_nodes,
        "elements": number_of_elements,
        "displacement": displacement,
        "reaction_forces": reaction_forces,
        "stress": stress,
        "strain": strain,
    }


def read_reaction_forces_for_node_set(hdf5_file, reaction_forces, node_set_name):
    """Read the reaction force values for one named node set."""
    with h5py.File(hdf5_file, "r") as result_file:
        node_indices = read_node_set(result_file, node_set_name)

    node_set_reaction_forces = []

    for node_index in node_indices:
        reaction_force_at_node = reaction_forces[node_index]
        node_set_reaction_forces.append(reaction_force_at_node)

    return np.array(node_set_reaction_forces)


def maximum_magnitude(values):
    """Calculate the largest vector magnitude in an array."""
    magnitudes = np.linalg.norm(values, axis=1)

    return magnitudes.max()


def calculate_compression_stiffness(top_face_reaction_forces, displacement):
    """Calculate compression stiffness from reaction force and displacement."""
    total_reaction_force = top_face_reaction_forces.sum(axis=0)
    z_reaction_force = total_reaction_force[2]
    stiffness = abs(z_reaction_force) / abs(displacement)

    return total_reaction_force, z_reaction_force, stiffness
