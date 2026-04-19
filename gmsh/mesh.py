import gmsh

gmsh.initialize()
gmsh.model.add("cylinder")
gmsh.model.occ.importShapes("/home/simon/pipelinefebio/freecad/cylinder.step")
gmsh.model.occ.synchronize()

volumes = gmsh.model.getEntities(3)
gmsh.model.addPhysicalGroup(3, [v[1] for v in volumes], tag=1, name="stent_volume")

gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
gmsh.model.mesh.generate(3)
gmsh.write("/home/simon/pipelinefebio/gmsh/cylinder.msh")
gmsh.finalize()
