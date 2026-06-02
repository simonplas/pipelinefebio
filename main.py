"""
This is the main script to run the full pipeline. 

It calls each step in turn and checks that the expected files are created.
"""
import subprocess
import sys
from pathlib import Path

from config import FEB_FILE, FREECAD_COMMAND, LOAD_CASE, MSH_FILE, STEP_FILE

# The paths we need
ROOT = Path(__file__).resolve().parent
FREECAD_SCRIPT = ROOT / "freecad_step" / "script.py"
GMSH_SCRIPT = ROOT / "gmsh_step" / "mesh.py"
COMPRESSION_SCRIPT = ROOT / "febio_step" / "create_compression_feb.py"
PRESSURE_SCRIPT = ROOT / "febio_step" / "create_pressure_feb.py"
RESULT_SCRIPT = ROOT / "febio_step" / "extract_results.py"

FEBIO_SCRIPTS = {
    "compression": COMPRESSION_SCRIPT,
    "pressure": PRESSURE_SCRIPT,
}


def run_command(command, working_directory=ROOT):
    """Run a command and stop the pipeline if the command fails"""
    print(" ".join(str(part) for part in command))
    result = subprocess.run(command, cwd=working_directory)

    if result.returncode != 0:
        raise RuntimeError(f"Pipeline command failed: {' '.join(str(part) for part in command)}")


def check_file_exists(file_path, description):
    """Check that the previous step created the file we expected."""
    if not file_path.exists():
        raise FileNotFoundError(f"{description} was unfortunatly not created: {file_path}")

    print(f"{description}: {file_path}")


def main():
    print("Starting the pipeline!!")

    # FreeCAD creates the cylinder geometry and saves it as a STEP file.
    print("\nStep 1: create the geometry with FreeCAD")
    freecad_command = [str(FREECAD_COMMAND), "freecadcmd", str(FREECAD_SCRIPT)]
    run_command(freecad_command)

    check_file_exists(STEP_FILE, "STEP file")

    # Gmsh reads the STEP file and turns it into a mesh
    print("\nStep 2: create the Gmsh mesh")
    gmsh_command = [sys.executable, str(GMSH_SCRIPT)]
    run_command(gmsh_command)
    check_file_exists(MSH_FILE, "Gmsh mesh")

    # pyfebio builds the FEBio input file for the selected load case
    print(f"\nStep 3: create the FEBio {LOAD_CASE} model")
    febio_input_command = [sys.executable, str(FEBIO_SCRIPTS[LOAD_CASE])]
    run_command(febio_input_command)
    check_file_exists(FEB_FILE, "FEBio input file")

    # The FEBio solver runs the simulation and creates the result file
    print("\nStep 4: run the FEBio solver")
    febio_command = ["febio4", "-i", FEB_FILE.name]
    run_command(febio_command, working_directory=FEB_FILE.parent)
    check_file_exists(FEB_FILE.with_suffix(".xplt"), "FEBio result file")

    # Python reads the FEBio result file and prints a small result summary
    print("\nStep 5: extract result values")
    result_command = [sys.executable, str(RESULT_SCRIPT)]
    run_command(result_command)

    print("\nPipeline finished successfully.")


if __name__ == "__main__":
    main()
