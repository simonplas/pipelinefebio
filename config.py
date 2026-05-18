from pathlib import Path


ROOT = Path(__file__).resolve().parent

# Command used by main.py to run FreeCAD.
FREECAD_COMMAND = ROOT / ".tools" / "freecad-appimage" / "squashfs-root" / "AppRun"

# Geometry parameters used by freecad_step/script.py.
CYLINDER_RADIUS = 3
CYLINDER_HEIGHT = 15

# Mesh parameters used by gmsh_step/mesh.py.
MESH_SIZE = 0.5
MESH_ELEMENT_ORDER = 1
MESH_FORMAT_VERSION = 2.2

# Output files used by the current pipeline.
STEP_FILE = ROOT / "freecad_step" / "cylinder.step"
MSH_FILE = ROOT / "gmsh_step" / "cylinder.msh"
FEB_FILE = ROOT / "febio_step" / "compression_test.feb"
