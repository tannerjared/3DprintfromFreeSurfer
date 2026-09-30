# 3D Print from FreeSurfer

Create a brain model from completed FreeSurfer results. FSQC generates the surface files, and this repository's script converts, combines, and smooths them into an STL file. You can then import that file into 3D modeling software or prepare it for printing.

The workflow is:

1. Process a T1-weighted MRI with FreeSurfer and check the reconstruction.
2. Run FSQC with `--shape` to generate BrainPrint VTK surfaces.
3. Run `3Dprintprep.py` or its container once per subject to create a combined STL.
4. Inspect and repair the mesh, choose its orientation and size, and prepare it in your printer's slicing software.

## Before you start

- You need **completed FreeSurfer subject directories**, not just the original MRI files. A T1 NIfTI or T1 DICOM series can be used for the earlier FreeSurfer processing step. See the [FreeSurfer documentation](https://surfer.nmr.mgh.harvard.edu/fswiki) for installation and reconstruction instructions.
- FreeSurfer must be available to the environment running FSQC's shape analysis, with a valid license.
- Choose how to run FSQC and how to run the STL conversion. These are **two separate tools**: the `3dprintprep` container converts existing surfaces; it does not run FreeSurfer reconstruction or FSQC.
- The conversion writes intermediate STL files into the input `surfaces` directory. You need write access there as well as to the final output directory.

## 1. Generate the surfaces with FSQC

[FSQC](https://github.com/Deep-MI/fsqc) can run as an installed command, a Python package, or a container. Whichever method you choose, include `--shape` (or `shape=True` in Python).

The examples below use a FreeSurfer subjects directory called `fs_subjects`, a subject called `sub-001`, and an output directory called `fsqc_out`. Replace these with your own paths and subject IDs. The subjects directory is the **parent** of the individual subject directories:

```text
fs_subjects/
└── sub-001/
    ├── mri/
    ├── surf/
    └── stats/
```

### Option A: Install FSQC in a Python environment

Use an isolated environment, such as a Python virtual environment or Conda/Mamba environment. For example:

```bash
python3 -m venv /path/to/fsqc-env
source /path/to/fsqc-env/bin/activate
python -m pip install fsqc
```

Set up FreeSurfer in that shell using your installation's setup instructions or your cluster's module. Then run:

```bash
run_fsqc \
    --subjects_dir ./fs_subjects \
    --subjects sub-001 \
    --output_dir ./fsqc_out \
    --shape
```

List several subject IDs after `--subjects` to process several subjects, or omit that option to let FSQC select subjects from the subjects directory. For this printing workflow, selecting subjects explicitly makes the next step easier to follow.

If you prefer to call FSQC from Python in the same configured environment:

```python
import fsqc

fsqc.run_fsqc(
    subjects_dir="./fs_subjects",
    subjects=["sub-001"],
    output_dir="./fsqc_out",
    shape=True,
)
```

### Option B: Run an Apptainer/Singularity `.sif` container

You can create your own FSQC image using the [upstream container instructions](https://github.com/Deep-MI/fsqc/blob/dev/singularity/Singularity.md). An example using the upstream Docker image as the base is:

```bash
apptainer build fsqc.sif docker://deepmi/fsqcdocker:2.1.7
```

That creates an FSQC image, but **does not add FreeSurfer**. For `--shape`, you must also provide a compatible Linux FreeSurfer installation, its environment, and its license inside the container. Use the course script's bind-and-environment pattern as an example, adapting every host path. This build command does not establish how the instructor's shared `.sif` was built or which version it contains.

### Option C: Run FSQC with Docker

FSQC also provides a Docker image and [Docker instructions](https://github.com/Deep-MI/fsqc/blob/dev/docker/Docker.md). The upstream image does not include FreeSurfer, and its documentation notes the resulting limitation for `--shape`. For this workflow, use a container setup that supplies a compatible Linux FreeSurfer installation and license, or use the installed FSQC or HiPerGator method above. Running the unmodified FSQC Docker image alone is insufficient for generating these shape surfaces.

### Check the FSQC output

After shape analysis, check for:

```text
fsqc_out/
└── brainprint/
    └── sub-001/
        └── surfaces/
            ├── lh.pial.vtk
            ├── rh.pial.vtk
            └── aseg.final.*.vtk
```

The conversion needs both pial surfaces and the specific segmentation surfaces used by [3Dprintprep.py](3Dprintprep.py). Pass this subject's **`brainprint/sub-001/surfaces` directory** to the converter. FSQC's separate surface screenshots are not the VTK input for this step.

## 2. Convert one subject's surfaces to STL

Choose one of the following methods. Each invocation converts **one subject**. Repeat it for each subject, using a different output filename.

### Option A: Run the Python script directly

Download or clone this repository. In an isolated Python environment, install the conversion dependencies. These pins match the repository's current [Dockerfile](Docker/Dockerfile):

```bash
python -m pip install numpy numpy-stl pymeshlab==2025.7.post1 vtk==9.7.0
```

You can use the same environment as FSQC if compatible, or keep separate environments for the two tools. Local installs may also need system libraries for PyMeshLab; the Dockerfile lists the libraries used by the container.

From the directory containing `3Dprintprep.py`, run:

```bash
python 3Dprintprep.py \
    ./fsqc_out/brainprint/sub-001/surfaces \
    ./fsqc_out/sub-001.stl
```

### Option B: Run the conversion with Docker

Run this from the directory containing `fsqc_out`:

```bash
docker run --rm \
    -v "$PWD/fsqc_out/brainprint/sub-001/surfaces:/in" \
    -v "$PWD/fsqc_out:/out" \
    jjtanner/3dprintprep:latest \
    /in /out/sub-001.stl
```

On Linux, you can add `--user "$(id -u):$(id -g)"` to keep generated files owned by your user. The mounted input directory must remain writable because the converter saves intermediate files there.

To build the converter from the code in your checkout, run this from the repository root, then use `3dprintprep:local` instead of the published image name:

```bash
docker build -t 3dprintprep:local ./Docker
```

### Option C: Run the conversion with Apptainer/Singularity

Build the image once, then run it against an existing FSQC output directory:

```bash
apptainer build 3dprintprep.sif docker://jjtanner/3dprintprep:latest

apptainer run \
    -B "$PWD/fsqc_out/brainprint/sub-001/surfaces:/in" \
    -B "$PWD/fsqc_out:/out" \
    3dprintprep.sif \
    /in /out/sub-001.stl
```

If your system uses Singularity, replace `apptainer` with `singularity`.

Published `latest` images and existing `.sif` files may contain a different script version from your checkout. Record the versions you use; rebuilding or replacing a `.sif` is a separate step from updating repository code.

### What the converter creates

The script converts VTK files to STL, combines and smooths the left/right pial surfaces, combines and smooths the selected non-cortical structures, and merges the smoothed meshes into the final brain STL. The current code excludes `aseg.final.14_24` from the combined model because it contains CSF and can create an unwanted shell.

Intermediate files stay in the input `surfaces` directory, including `cortex.stl`, `cortex_smoothed.stl`, `non-cortex.stl`, and `non-cortex_smoothed.stl`. The combined brain is saved to the output filename you supplied. Merging meshes does not guarantee a watertight, printable solid; inspect the result before printing.

## 1. Inspect and prepare the model for printing

Import the combined STL into your preferred 3D modeling or mesh-repair software. Check for missing structures, unwanted shells, disconnected pieces, and mesh errors. Repair the model as needed, confirm its size, and choose an orientation before slicing it for your printer.

One approach used for this workflow is to import the STL into **3D Builder on Windows 10 or 11**, fix the errors reported on import, and use **Settle** to rest the model on the medulla and temporal lobes. Use this approach if you already have that software available; another mesh-repair tool is fine. Then review supports and print settings in your slicer.

## Troubleshooting

- **No `brainprint/<subject>/surfaces` directory:** check the FSQC log, subject ID, completed FreeSurfer results, and `--shape` option. Also check that FreeSurfer and the license are visible inside the FSQC environment. A top-level `brainprint` directory alone does not prove every subject finished.
- **Missing pial or `aseg.final.*` files:** the converter expects the filenames listed in the current script. Confirm that shape analysis generated the complete set of surfaces.
- **FreeSurfer/license errors inside the course container:** check `module load freesurfer/7.4.1`, the `$FREESURFER_HOME` bind, `-B /apps`, and the `FS_LICENSE` setting.
- **Permission errors:** both the input surfaces directory and output directory must be writable. Copy course scripts to your own directory before editing them.
- **Python package or smoothing errors:** compare your environment with the current Dockerfile, or use a matching conversion container. An older shared image may behave differently from the current script.
- **Job fails or runs out of time/memory:** read the Slurm log before resubmitting and adjust resources as needed. An STL file's existence is not a substitute for visually checking it.

## Video walkthrough: older instructions

The [Preparing for 3D Printing video](https://youtu.be/ROm5F_075ac) shows both interactive processing and a script-based approach; the script appears in the last part of the video. **The video is dated.** Use it for background and a demonstration of the overall process, and use this README and your current course script for commands, package versions, container paths, and account settings.
