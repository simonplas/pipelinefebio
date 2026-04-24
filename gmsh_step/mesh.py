import gmsh

mesh_size = 0.5

gmsh.initialize()
gmsh.model.add("cylinder")

gmsh.model.occ.importShapes("/home/simon/pipelinefebio/freecad_step/cylinder.step")
gmsh.model.occ.synchronize()

volumes = gmsh.model.getEntities(3)

# group for volume
gmsh.model.addPhysicalGroup(
    3,
    [tag for _, tag in volumes],
    tag=1,
    name="stent_volume"
)

# physical groups for suface
surfaces = gmsh.model.getEntities(2)

surface_data = []

for dim, tag in surfaces:
    com = gmsh.model.occ.getCenterOfMass(dim, tag)
    surface_data.append((tag, com))

# sort by z value since lowest z value means bottom surface in between is the wall and top is top value
surface_data.sort(key=lambda item: item[1][2])

bottom_face = surface_data[0][0]
outer_wall = surface_data[1][0]
top_face = surface_data[2][0]

gmsh.model.addPhysicalGroup(2, [bottom_face], tag=2, name="bottom_face")
gmsh.model.addPhysicalGroup(2, [top_face], tag=3, name="top_face")
gmsh.model.addPhysicalGroup(2, [outer_wall], tag=4, name="outer_wall")


gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size)
gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)

gmsh.model.mesh.generate(3)
gmsh.write("/home/simon/pipelinefebio/gmsh_step/cylinder.msh")

gmsh.finalize()