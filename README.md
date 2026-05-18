# pipelinefebio

This repository contains a Bachelor thesis project about building a Python
pipeline for finite element simulations. The aim is to connect the main steps
that are needed before a FEBio simulation can be run:

```text
geometry generation -> mesh generation -> FEBio simulation setup
```

The current version focuses on the first two steps. It creates a simple
parameterised geometry in FreeCAD, exports it as a STEP file, and then creates a
3D mesh in Gmsh.

The intended full workflow is:

```text
FreeCAD -> STEP -> Gmsh -> MSH -> pyfebio/FEBio -> results
```

The currently working workflow is:

```text
FreeCAD -> STEP -> Gmsh -> MSH
```

## Current status

At the moment, the pipeline can:

- create a cylinder geometry in FreeCAD using Python;
- change basic geometry parameters from one config file;
- export the geometry to `freecad_step/cylinder.step`;
- import the STEP file in Gmsh;
- generate a 3D tetrahedral mesh;
- label the volume and main boundary surfaces in Gmsh;
- export the mesh to `gmsh_step/cylinder.msh`;
- run the FreeCAD and Gmsh steps from one main script.

The FEBio step is still being redesigned. The plan is to use `pyfebio` together
with `meshio`, so that the Gmsh mesh can later be translated into a FEBio model
while keeping useful mesh information such as named regions.

## Project structure

```text
.
├── config.py
├── main.py
├── freecad_step/
│   └── script.py
├── gmsh_step/
│   └── mesh.py
├── documents/
└── thesis/
```

The most important files are:

- `main.py`: runs the current pipeline from FreeCAD to Gmsh.
- `config.py`: stores shared settings such as geometry parameters, mesh settings,
  file paths, and the FreeCAD command.
- `freecad_step/script.py`: creates the geometry in FreeCAD and writes the STEP
  file.
- `gmsh_step/mesh.py`: imports the STEP file, creates the mesh, adds physical
  groups, and writes the MSH file.
- `documents/`: contains project documents and background material.
- `thesis/`: contains the thesis draft and literature notes. These files are not
  part of the code pipeline.

## Requirements

The current pipeline uses:

- Python 3;
- FreeCAD, run through command-line mode;
- Gmsh Python API;
- a Python virtual environment.

For the later FEBio part, the project is moving toward:

- `pyfebio`;
- `meshio`;
- FEBio.

## Configuration

Most values that should be easy to change are stored in `config.py`.

Current geometry parameters:

```python
CYLINDER_RADIUS = 3
CYLINDER_HEIGHT = 15
```

Current mesh parameters:

```python
MESH_SIZE = 0.5
MESH_ELEMENT_ORDER = 1
MESH_FORMAT_VERSION = 2.2
```

Current output files:

```python
STEP_FILE = ROOT / "freecad_step" / "cylinder.step"
MSH_FILE = ROOT / "gmsh_step" / "cylinder.msh"
FEB_FILE = ROOT / "febio_step" / "compression_test.feb"
```

Changing the geometry or mesh values in `config.py` changes what the pipeline
generates the next time it is run.

## Running the pipeline

First activate the virtual environment:

```bash
source venv/bin/activate
```

Then run:

```bash
python main.py
```

If the run succeeds, the expected output files are:

```text
freecad_step/cylinder.step
gmsh_step/cylinder.msh
```

## FreeCAD note

FreeCAD is currently called from `main.py` using the command stored in
`config.py`:

```python
FREECAD_COMMAND = ROOT / ".tools" / "freecad-appimage" / "squashfs-root" / "AppRun"
```

This points to the extracted FreeCAD AppImage in this workspace. Running FreeCAD
this way avoids some AppImage/FUSE problems and allows the geometry script to be
executed from the command line.

## Mesh labels

The Gmsh step adds physical groups to the mesh. These labels are important
because they can later be used to decide where boundary conditions and loads
should be applied in FEBio.

The current labels are:

- `stent_volume`
- `bottom_face`
- `top_face`
- `outer_wall`

Even though the current geometry is only a cylinder, these labels are a first
step toward a more useful simulation workflow.
