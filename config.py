from pathlib import Path


ROOT = Path(__file__).resolve().parent

# This name is used for output files and the FEBio job folder.
GEOMETRY_NAME = "cylinder"

# Choose which FEBio load case main.py should run.
# Options: "compression" or "pressure".
LOAD_CASE = "compression"

# Compression test setting.
COMPRESSION_DISPLACEMENT_Z = -0.1



# FreeCAD settings

# Command used by main.py to run the FreeCAD geometry script.
FREECAD_COMMAND = ROOT / ".tools" / "freecad-appimage" / "squashfs-root" / "AppRun"


# geometry settings

# Options: "solid" or "hollow".
CYLINDER_TYPE = "hollow"
CYLINDER_RADIUS = 3
CYLINDER_INNER_RADIUS = 2
CYLINDER_HEIGHT = 15


# basic mesh settings

MESH_SIZE = 0.5

# For the simple cylinder, these can usually both be MESH_SIZE.
MESH_SIZE_MIN = MESH_SIZE
MESH_SIZE_MAX = MESH_SIZE
MESH_ELEMENT_ORDER = 1
MESH_FORMAT_VERSION = 4.1


# output paths

STEP_FILE = ROOT / "freecad_step" / "cylinder.step"
MSH_FILE = ROOT / "gmsh_step" / f"{GEOMETRY_NAME}.msh"
FEB_JOB_DIR = ROOT / "febio_step" / "jobs" / GEOMETRY_NAME
COMPRESSION_FEB_FILE = FEB_JOB_DIR / f"compression_{GEOMETRY_NAME}.feb"
PRESSURE_FEB_FILE = FEB_JOB_DIR / f"pressure_{GEOMETRY_NAME}.feb"

if LOAD_CASE == "compression":
    FEB_FILE = COMPRESSION_FEB_FILE
elif LOAD_CASE == "pressure":
    FEB_FILE = PRESSURE_FEB_FILE
else:
    raise ValueError('LOAD_CASE should be either "compression" or "pressure"')
