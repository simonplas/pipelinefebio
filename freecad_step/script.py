from pathlib import Path
import sys


sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import CYLINDER_HEIGHT, CYLINDER_RADIUS, STEP_FILE


doc = FreeCAD.newDocument()
cyl = doc.addObject("Part::Cylinder", "myCylinder")
cyl.Radius = CYLINDER_RADIUS
cyl.Height = CYLINDER_HEIGHT
doc.recompute()
cyl.Shape.exportStep(str(STEP_FILE))
