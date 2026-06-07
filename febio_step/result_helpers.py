"""Small helpers to read FEBio result files and compute simple metrics."""

import math
import h5py
import numpy as np


def read_values_from_group(group):
    """Read and stack all datasets in an HDF5 group.

    Parameters:
    group : h5py.Group
        HDF5 group with several datasets that have the same shape.

    Returns:
    np.ndarray
        2D array with datasets stacked along axis 0.
    """
    values = []

    for dataset_name in group:
        values.append(group[dataset_name][:])

    return np.vstack(values)


def get_last_state(result_file):
    """Return the last saved state name and its HDF5 group.

    Parameters:
    result_file : h5py.File
        An opened HDF5 result file (read mode).

    Returns:
    (str, h5py.Group)
        The last state key and the group object for that state.
    """
    states_group = result_file["states"]
    state_numbers = sorted(states_group.keys(), key=int)
    last_state_number = state_numbers[-1]

    return last_state_number, states_group[last_state_number]


def count_elements(result_file):
    """Count total number of volume elements in the result file.

    Parameters:
    result_file : h5py.File
        Opened HDF5 result file.

    Returns:
    int
        Total number of elements across all solid domains.
    """
    domains_group = result_file["meshes/0/domains"]
    total_elements = 0

    for domain_name in domains_group:
        domain_elements = domains_group[domain_name]
        total_elements += len(domain_elements)

    return total_elements


def read_node_set(result_file, node_set_name):
    """Get the node indices for a named node set.

    Parameters:
    result_file : h5py.File
        Opened HDF5 result file.
    node_set_name : str
        Name of the node set to read.

    Returns:
    np.ndarray
        Array of node indices (integers).

    Raises:
    KeyError
        If the node set is missing in the file.
    """
    node_sets_group = result_file["meshes/0/nodesets"]

    if node_set_name not in node_sets_group:
        raise KeyError(f"node set was not found in the FEBio result file: {node_set_name}")

    return node_sets_group[node_set_name][:]


def read_last_result_values(hdf5_file):
    """Read main result arrays from the last saved step in an HDF5 file.

    Parameters:
    hdf5_file : str or Path
        Path to the HDF5 file converted from FEBio '.xplt'.

    Returns:
    dict
        Dict with keys: 'last_state', 'last_time', 'nodes', 'elements',
        'displacement', 'reaction_forces', 'stress', 'strain'. Arrays are
        NumPy arrays matching the stored shapes.
    """
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
    """Get reaction force vectors for nodes in a named node set.

    Parameters:
    hdf5_file : str or Path
        Path to the HDF5 file (used to read node set membership).
    reaction_forces : np.ndarray
        Array of reaction forces for all nodes.
    node_set_name : str
        The node set to extract.

    Returns:
    np.ndarray
        Reaction forces restricted to the nodes in the set.
    """
    with h5py.File(hdf5_file, "r") as result_file:
        node_indices = read_node_set(result_file, node_set_name)

    node_set_reaction_forces = []

    for node_index in node_indices:
        reaction_force_at_node = reaction_forces[node_index]
        node_set_reaction_forces.append(reaction_force_at_node)

    return np.array(node_set_reaction_forces)


def maximum_magnitude(values):
    """Return the maximum magnitude among a list of vectors.

    Parameters:
    values : np.ndarray
        Array of vectors with shape (N, dim).

    Returns:
    float
        Maximum Euclidean norm.
    """
    magnitudes = np.linalg.norm(values, axis=1)

    return magnitudes.max()


def calculate_compression_stiffness(top_face_reaction_forces, displacement):
    """Compute total reaction force on the top face and stiffness.

    Parameters:
    top_face_reaction_forces : np.ndarray
        Reaction forces for nodes on the top face (N x 3).
    displacement : float
        Prescribed displacement used for computing stiffness.

    Returns:
    tuple
        (total_reaction_force, z_reaction_force, stiffness)
    """
    total_reaction_force = top_face_reaction_forces.sum(axis=0)
    z_reaction_force = total_reaction_force[2]
    stiffness = abs(z_reaction_force) / abs(displacement)

    return total_reaction_force, z_reaction_force, stiffness


def calculate_cylinder_area(cylinder_type, outer_radius, inner_radius):
    """Return cross-sectional area for solid or hollow cylinder.

    Parameters:
    cylinder_type : str
        'solid' or 'hollow'.
    outer_radius : float
        Outer radius.
    inner_radius : float
        Inner radius (only used for 'hollow').

    Returns:
    float
        Cross-sectional area.
    """
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
    """Compute a simple theoretical axial stiffness E*A/L for a cylinder.

    Parameters are the cylinder geometry and Young's modulus.
    """
    area = calculate_cylinder_area(cylinder_type, outer_radius, inner_radius)

    return young_modulus * area / height


def calculate_percent_difference(value, reference_value):
    """Return percent difference relative to a reference value.

    The returned value is 100 * (value - reference_value) / reference_value.
    """
    return 100 * (value - reference_value) / reference_value
