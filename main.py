import subprocess
import sys
from pathlib import Path

from config import FREECAD_COMMAND, MSH_FILE, STEP_FILE


# Get the root path
ROOT = Path(__file__).resolve().parent
FREECAD_SCRIPT = ROOT / "freecad_step" / "script.py"
GMSH_SCRIPT = ROOT / "gmsh_step" / "mesh.py"


def main():
    print("Starting upppp the pipeline")

    # creates the geometry in FreeCAD and exports it as a STEP file
    print("\nStep 1: create the STEP geometry with FreeCAD")
    freecad_command = [str(FREECAD_COMMAND),"freecadcmd", str(FREECAD_SCRIPT),]
    print(" ".join(freecad_command))

    freecad_result = subprocess.run(freecad_command, cwd=ROOT)
    if freecad_result.returncode != 0:
        raise RuntimeError("FreeCAD failed")

    #  if step file wasnt created
    if not STEP_FILE.exists():
        raise FileNotFoundError(f"STEP file was not created: {STEP_FILE}")

    print(f"STEP file created: {STEP_FILE}")

    # imports the STEP file in Gmsh and creates a mesh
    print("\nStep 2: create the Gmsh mesh")
    gmsh_command = [sys.executable,str(GMSH_SCRIPT),]
    print(" ".join(gmsh_command))

    gmsh_result = subprocess.run(gmsh_command, cwd=ROOT)
    if gmsh_result.returncode != 0:
        raise RuntimeError("Gmsh step failed")

    # does that the msh file actually exist??
    if not MSH_FILE.exists():
        raise FileNotFoundError(f"Gmsh mesh was not created: {MSH_FILE}")

    print(f"Gmsh mesh created: {MSH_FILE}")

    print("\nPipeline finished successfully.")


if __name__ == "__main__":
    main()
