# pipelinefebio

simple thesis project for building a small simulation pipeline with freecad gmsh and later febio

## current status

right now this repo does two things

- creates a cylinder in freecad and exports it as a step file
- loads that step file in gmsh and generates a 3d mesh

## files

- `freecad/script.py` creates `freecad/cylinder.step`
- `gmsh/mesh.py` creates `gmsh/cylinder.msh`

## run

run the freecad script inside freecad to generate the step file

then run the gmsh step with

```bash
source venv/bin/activate
python gmsh/mesh.py
```
