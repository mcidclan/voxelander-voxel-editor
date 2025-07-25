# Voxelander

Voxelander is a simple voxel editor written in Python for creating and exporting voxel regions. It's designed for use with experimental voxel rendering projects like Beamcaster.

## Installation & Usage

### Linux/macOS (Recommended)
Simply run the automated setup script:
```bash
./run_linux.sh
```
This script will automatically:
- Create a Python virtual environment
- Install required dependencies (PyOpenGL, glfw, numpy)
- Launch the application

### Windows
1. Install dependencies manually:
```bash
pip install PyOpenGL glfw numpy
```

2. Launch the application:
```bash
python main.py
```

## Controls

### View Controls
| Key | Action |
|-----|--------|
| **R** | Move camera right |
| **L** | Move camera left |
| **F** | Move camera forward |
| **B** | Move camera backward |
| **←** | Rotate camera left |
| **→** | Rotate camera right |
| **↑** | Rotate camera up |
| **↓** | Rotate camera down |

### Editor Controls
| Key | Action |
|-----|--------|
| **1** | Switch voxel region origin |
| **2** | Switch voxel region size |
| **3** | Switch voxel block (grouped voxels) size |
| **4** | Switch axis visualization size |
| **C** | Change voxel/block color |
| **A** (QWERTY) / **Q** (AZERTY) | Add new voxel/block |
| **E** | Export to .565 file format (for Beamcaster project) |

## File Format
Exports are saved in the `565` format (`.bin`), specifically designed for the Beamcaster voxel rendering project.

## Requirements
- Python 3.x
- PyOpenGL
- GLFW
- NumPy

*m-c/d*
