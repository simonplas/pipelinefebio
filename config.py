from pathlib import Path
import os


ROOT = Path(__file__).resolve().parent


# This name is used for output files and the FEBio job folder.
GEOMETRY_NAME = "cylinder"

# Choose which FEBio load case main.py should run.
# Options: "compression" or "pressure".
LOAD_CASE = os.environ.get("PIPELINE_LOAD_CASE", "compression")

# Compression test setting
COMPRESSION_DISPLACEMENT_Z = -0.1

# Pressure test settings
# Internal pressure is applied on the inner wall of the hollow cylinder.
PRESSURE_SURFACE = "inner_wall"
INTERNAL_PRESSURE = float(os.environ.get("PIPELINE_INTERNAL_PRESSURE", 2.0e10))


# material settings

MATERIAL_NAME = "stainless_steel"
YOUNG_MODULUS = float(os.environ.get("PIPELINE_YOUNG_MODULUS", 193e9))
POISSON_RATIO = 0.3
DENSITY = 8000


# FEBio output settings.
# The normal pipeline saves every step, so the animation in FEBio Studio is clear.
# Study scripts can temporarily change this to save less output for larger meshes.
FEBIO_TIME_STEPS = 20
FEBIO_STEP_SIZE = 0.05
FEBIO_PLOT_STRIDE = int(os.environ.get("PIPELINE_PLOT_STRIDE", 1))
FEBIO_OUTPUT_STRIDE = int(os.environ.get("PIPELINE_OUTPUT_STRIDE", 1))


# FreeCAD settings

# Command used by main.py to run the FreeCAD geometry script.
FREECAD_COMMAND = ROOT / ".tools" / "freecad-appimage" / "squashfs-root" / "AppRun"


# geometry settings

# Options: "solid" or "hollow".
CYLINDER_TYPE = os.environ.get("PIPELINE_CYLINDER_TYPE", "hollow")
CYLINDER_RADIUS = 3
CYLINDER_INNER_RADIUS = 2
CYLINDER_HEIGHT = 15


# basic mesh settings

MESH_SIZE = float(os.environ.get("PIPELINE_MESH_SIZE", 0.5))

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
