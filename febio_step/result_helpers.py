"""small helper functions for reading febio result files"""

import math
import h5py
import numpy as np


def read_values_from_group(group):
    """read all values in one hdf5 group"""
    values = []

    for dataset_name in group:
        values.append(group[dataset_name][:])

    return np.vstack(values)


def get_last_state(result_file):
    """get the last saved time step"""
    states_group = result_file["states"]
    state_numbers = sorted(states_group.keys(), key=int)
    last_state_number = state_numbers[-1]

    return last_state_number, states_group[last_state_number]


def count_elements(result_file):
    """count the volume elements in the result file"""
    domains_group = result_file["meshes/0/domains"]
    total_elements = 0

    for domain_name in domains_group:
        domain_elements = domains_group[domain_name]
        total_elements += len(domain_elements)

    return total_elements


def read_node_set(result_file, node_set_name):
    """read a named node set from the result file"""
    node_sets_group = result_file["meshes/0/nodesets"]

    if node_set_name not in node_sets_group:
        raise KeyError(f"node set was not found in the FEBio result file: {node_set_name}")

    return node_sets_group[node_set_name][:]


def read_last_result_values(hdf5_file):
    """read the main values from the last saved step"""
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
    """get the reaction forces for one node set"""
    with h5py.File(hdf5_file, "r") as result_file:
        node_indices = read_node_set(result_file, node_set_name)

    node_set_reaction_forces = []

    for node_index in node_indices:
        reaction_force_at_node = reaction_forces[node_index]
        node_set_reaction_forces.append(reaction_force_at_node)

    return np.array(node_set_reaction_forces)


def maximum_magnitude(values):
    """get the largest magnitude"""
    magnitudes = np.linalg.norm(values, axis=1)

    return magnitudes.max()


def calculate_compression_stiffness(top_face_reaction_forces, displacement):
    """calculate stiffness from force and displacement"""
    total_reaction_force = top_face_reaction_forces.sum(axis=0)
    z_reaction_force = total_reaction_force[2]
    stiffness = abs(z_reaction_force) / abs(displacement)

    return total_reaction_force, z_reaction_force, stiffness


def calculate_cylinder_area(cylinder_type, outer_radius, inner_radius):
    """calculate the area of a solid or hollow cylinder"""
    outer_area = math.pi * outer_radius**2

    if cylinder_type == "solid":
        return outer_area

    if cylinder_type == "hollow":
        inner_area = math.pi * inner_radius**2
        return outer_area - inner_area

    raise ValueError('cylinder_type should be either "solid" or "hollow"')


def calculate_theoretical_compression_stiffness(
    cylinder_type,
    outer_radius,
    inner_radius,
    height,
    young_modulus,
):
    """calculate the simple theoretical cylinder stiffness"""
    area = calculate_cylinder_area(cylinder_type, outer_radius, inner_radius)

    return young_modulus * area / height


def calculate_percent_difference(value, reference_value):
    """calculate the difference from a reference value"""
    return 100 * (value - reference_value) / reference_value
