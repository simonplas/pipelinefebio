# pipelinefebio

This repository contains a Bachelor thesis project about building a Python
pipeline for finite element simulations in FEBio

The workflow connects geometry, meshing, FEBio model creation, simulation, and
basic result extraction:

```text
FreeCAD -> STEP -> Gmsh -> MSH -> pyfebio -> FEBio -> XPLT -> HDF5 -> Python results
```

The normal pipeline currently focuses on a simple FreeCAD-generated cylinder.
The cylinder can be solid or hollow, which keeps the geometry simple enough to
understand while still making it possible to test meshing, compression, and
radial pressure

## Current status

At the moment, the pipeline can:

- create a solid or hollow cylinder in FreeCAD using Python;
- change geometry, mesh, load-case, and file settings from `config.py`;
- import the generated STEP file in Gmsh;
- generate a 3D mesh;
- label the volume and boundary surfaces in Gmsh;
- create either a FEBio compression model or pressure model with pyfebio;
- run the FEBio solver from the command line with `febio4`;
- create an `.xplt` result file;
- convert the `.xplt` result file to `.hdf5`;
- extract displacement, reaction force, stress, strain, and compression
  stiffness values with Python;
- run small parameter studies for mesh convergence and Young's modulus.

There is also a separate experimental stent workflow. This is not part of the
normal `main.py` pipeline yet, because selecting the correct boundaries on a
real stent STEP file is more complicated than on the simple cylinder.

## Project structure

```text
.
├── config.py
├── main.py
├── freecad_step/
│   └── script.py
├── gmsh_step/
│   ├── mesh.py
│   └── mesh_stent_selection.py
├── febio_step/
│   ├── create_compression_feb.py
│   ├── create_pressure_feb.py
│   ├── create_stent_pressure_feb.py
│   ├── extract_results.py
│   ├── febio_helpers.py
│   └── result_helpers.py
├── studies/
│   ├── mesh_convergence.py
│   └── youngs_modulus.py
└── thesis/
```

## Configuration

Most settings are stored in `config.py`

### Cylinder parameters

```python
CYLINDER_TYPE = "hollow"
CYLINDER_RADIUS = 3
CYLINDER_INNER_RADIUS = 2
CYLINDER_HEIGHT = 15
```

Available options:

- `CYLINDER_TYPE = "solid"`: creates a solid cylinder.
- `CYLINDER_TYPE = "hollow"`: creates a hollow cylinder with an inner wall.

The hollow cylinder is useful for testing radial pressure on the inside wall.

### Load case

```python
LOAD_CASE = "compression"
```

Available options:

- `LOAD_CASE = "compression"`: fixes the bottom face and moves the top face
  downward
- `LOAD_CASE = "pressure"`: applies pressure to a wall surface, usually the
  `inner_wall` of the hollow cylinder.

The compression displacement and pressure settings are also stored in
`config.py`:

```python
COMPRESSION_DISPLACEMENT_Z = -0.1
PRESSURE_SURFACE = "inner_wall"
INTERNAL_PRESSURE = 2.0e10
```

### Mesh settings

```python
MESH_SIZE = 0.5
MESH_SIZE_MIN = MESH_SIZE
MESH_SIZE_MAX = MESH_SIZE
MESH_ELEMENT_ORDER = 1
MESH_FORMAT_VERSION = 4.1
```

Useful options:

- smaller `MESH_SIZE_MIN` and `MESH_SIZE_MAX` values create a finer mesh
- `MESH_ELEMENT_ORDER = 1` uses first-order tetrahedral elements (for now thats enough, can be changed to 2 later if needed)
- `MESH_FORMAT_VERSION = 4.1` is used because pyfebio/meshio keeps the Gmsh
  physical groups as named surfaces and node sets in this format which is very handy.

## Running the pipeline

First activate the virtual environment:

```bash
source venv/bin/activate
```

Install the Python dependencies if needed:

```bash
pip install -r requirements.txt
```

Then run:

```bash
python main.py
```

This runs:

```text
1. create FreeCAD geometry
2. generate a Gmsh mesh
3. create the FEBio model for the selected load case
4. run the FEBio solver with `febio4`
5. convert the XPLT result file to HDF5 and extract values with Python
```

For `GEOMETRY_NAME = "cylinder"` and `LOAD_CASE = "compression"` for example, the main
output files are:

```text
freecad_step/cylinder.step
gmsh_step/cylinder.msh
febio_step/jobs/cylinder/compression_cylinder.feb
febio_step/jobs/cylinder/compression_cylinder.xplt
febio_step/jobs/cylinder/compression_cylinder.hdf5
```

FEBio Studio is not required to run the pipeline. It is still useful for
opening the `.feb` or `.xplt` files visually.

## Experimental stent workflow

The real stent STEP-file is kept separate from the normal cylinder pipeline for
now. The cylinder pipeline is the reproducible core of the project. The stent
scripts are an exploratory extension to test whether a more complex implant
geometry can be meshed and labelled automatically.

To try the stent workflow manually:

```bash
python gmsh_step/mesh_stent_selection.py
python febio_step/create_stent_pressure_feb.py
cd febio_step/jobs/stent
febio4 -i pressure_stent.feb
cd ../../..
```

This creates a labelled stent mesh and a first pressure-based FEBio model. It
should be treated as experimental, because the inner-wall and support-region
selection still needs more validation before it can be used as part of the main
pipeline.

## FEBio model creation

The FEBio input file is created with pyfebio.

The shared FEBio setup is stored in `febio_step/febio_helpers.py`. This file
contains the common material, solver settings, load curve, output requests, and
mesh-reading function.

The load-case-specific files are:

- `febio_step/create_compression_feb.py`: this file fixes the bottom face and puts
  a downward displacement on the top face.
- `febio_step/create_pressure_feb.py`: this file fixes the bottom face and applies
  pressure to the inner wall of a hollow cylinder.

The current material is stainless steel:

```python
Young's modulus = 193e9
Poisson ratio = 0.3
density = 8000
```

## Result extraction

FEBio writes result data to an `.xplt` file. Python does not read this file
directly. Instead, `febio_step/extract_results.py` uses pyfebio to convert it
to HDF5:

```python
from pyfebio import xplt

xplt.to_hdf5(inputfile="result.xplt", outputfile="result.hdf5")
```

The result extraction step currently prints:

- final displacement values;
- reaction forces;
- stress;
- Lagrange strain;
- compression stiffness for the compression case.

## Parameter studies

Two small study scripts are included:

- `studies/mesh_convergence.py`: runs the compression case for solid and hollow
  cylinders with several mesh sizes.
- `studies/youngs_modulus.py`: runs the compression case for several Young's
  modulus values while keeping the mesh size fixed.

The study scripts write CSV files to `study_results/`. That folder is ignored by
Git because the files are generated output.
