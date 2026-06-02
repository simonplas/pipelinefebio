"""
Create the cylinder geometry for the pipeline.

The cylinder settings are read from config.py. The generated shape is exported
as a STEP file, which is then used by Gmsh in the next pipeline step.
"""

from pathlib import Path
import sys

import Part

# Allows us to use files from the root of this project
sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import (
    CYLINDER_HEIGHT,
    CYLINDER_INNER_RADIUS,
    CYLINDER_RADIUS,
    CYLINDER_TYPE,
    STEP_FILE,
)

doc = FreeCAD.newDocument()

if CYLINDER_TYPE == "solid":
    cylinder_shape = Part.makeCylinder(CYLINDER_RADIUS, CYLINDER_HEIGHT)

elif CYLINDER_TYPE == "hollow":
    outer_cylinder = Part.makeCylinder(CYLINDER_RADIUS, CYLINDER_HEIGHT)
    inner_cylinder = Part.makeCylinder(CYLINDER_INNER_RADIUS, CYLINDER_HEIGHT)
    cylinder_shape = outer_cylinder.cut(inner_cylinder)

else:
    raise ValueError('CYLINDER_TYPE must be "solid" or "hollow"')

cyl = doc.addObject("Part::Feature", "cylinder")
cyl.Shape = cylinder_shape

doc.recompute()
cyl.Shape.exportStep(str(STEP_FILE))
