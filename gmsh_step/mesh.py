from pathlib import Path
import sys

import gmsh

sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import (
    MESH_ELEMENT_ORDER,
    MESH_FORMAT_VERSION,
    MESH_SIZE_MAX,
    MESH_SIZE_MIN,
    MSH_FILE,
    STEP_FILE,
)


gmsh.initialize()
gmsh.model.add("cylinder")

gmsh.model.occ.importShapes(str(STEP_FILE))
gmsh.model.occ.synchronize()

volumes = gmsh.model.getEntities(3)

if not volumes:
    gmsh.finalize()
    raise RuntimeError(f"No 3d volumes found in STEP file: {STEP_FILE}")


gmsh.model.addPhysicalGroup(
    3,
    [tag for _, tag in volumes],
    tag=1,
    name="stent_volume"
)

# These labels are used later for boundary conditions, loads, and checking the mesh in FEBio.
surfaces = gmsh.model.getEntities(2)

if not surfaces:
    gmsh.finalize()
    raise RuntimeError(f"No surfaces found in STEP file: {STEP_FILE}")

surface_data = []

for _dim, tag in surfaces:
    com = gmsh.model.occ.getCenterOfMass(2, tag)
    area = gmsh.model.occ.getMass(2, tag)
    surface_data.append((tag, com, area))

bottom_face = min(surface_data, key=lambda item: item[1][2])
top_face = max(surface_data, key=lambda item: item[1][2])

bottom_face_tag = bottom_face[0]
top_face_tag = top_face[0]

wall_faces = [
    (tag, area) for tag, com, area in surface_data
    if tag not in {bottom_face_tag, top_face_tag}
]

if not wall_faces:
    gmsh.finalize()
    raise RuntimeError("No wall surfaces were found in the geometry.")

gmsh.model.addPhysicalGroup(2, [bottom_face_tag], tag=2, name="bottom_face")
gmsh.model.addPhysicalGroup(2, [top_face_tag], tag=3, name="top_face")

# The outer wall has a larger area than the inner wall for this cylinder obviously
wall_faces.sort(key=lambda item: item[1], reverse=True)
outer_wall = wall_faces[0][0]

gmsh.model.addPhysicalGroup(2, [outer_wall], tag=4, name="outer_wall")

if len(wall_faces) > 1:
    inner_wall = wall_faces[1][0]
    gmsh.model.addPhysicalGroup(2, [inner_wall], tag=5, name="inner_wall")


gmsh.option.setNumber("Mesh.MeshSizeMin", MESH_SIZE_MIN)
gmsh.option.setNumber("Mesh.MeshSizeMax", MESH_SIZE_MAX)
gmsh.option.setNumber("Mesh.MshFileVersion", MESH_FORMAT_VERSION)

gmsh.model.mesh.generate(3)
gmsh.model.mesh.setOrder(MESH_ELEMENT_ORDER)
gmsh.write(str(MSH_FILE))

gmsh.finalize()
