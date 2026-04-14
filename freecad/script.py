radius = 3
height = 15
doc = FreeCAD.newDocument()
cyl = doc.addObject("Part::Cylinder", "myCylinder")
cyl.Radius = radius
cyl.Height = height
doc.recompute()
cyl.Shape.exportStep("/home/simon/pipeline/freecad/cylinder.step")
