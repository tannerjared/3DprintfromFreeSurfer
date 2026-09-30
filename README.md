# 3D Print from FreeSurfer

Create a brain model from completed FreeSurfer results. FSQC generates the surface files, and this repository's script converts, combines, and smooths them into an STL file. You can then import that file into 3D modeling software or prepare it for printing.

The workflow is:

1. Process a T1-weighted MRI with FreeSurfer and check the reconstruction.
2. Run FSQC with `--shape` to generate BrainPrint VTK surfaces.
3. Run `3Dprintprep.py` or its container once per subject to create a combined STL.
4. Inspect and repair the mesh, choose its orientation and size, and prepare it in your printer's slicing software.

**For PSY4930 students on HiPerGator:** use the [complete student workflow](#hipergator-student-workflow) below. It uses the shared containers and processes the two course subjects.

## Before you start

- You need **completed FreeSurfer subject directories**, not just the original MRI files. A T1 NIfTI or T1 DICOM series can be used for the earlier FreeSurfer processing step. See the [FreeSurfer documentation](https://surfer.nmr.mgh.harvard.edu/fswiki) for installation and reconstruction instructions.
- FreeSurfer must be available to the environment running FSQC's shape analysis, with a valid license. The student example uses `freesurfer/7.4.1`; use the appropriate installed version elsewhere.
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

On HiPerGator, the course provides `/blue/psy4930/share/data/neurotools/fsqc.sif`. The [student script](#hipergator-student-workflow) shows the complete invocation, including the FreeSurfer installation and license mounts needed for shape analysis. Students using that shared image do not need to install FSQC with `pip` or build another image.

Outside the course, you can create your own FSQC image using the [upstream container instructions](https://github.com/Deep-MI/fsqc/blob/dev/singularity/Singularity.md). An example using the upstream Docker image as the base is:

```bash
apptainer build fsqc.sif docker://deepmi/fsqcdocker:latest
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

**The current script takes two positional arguments:** the input surfaces directory and the final STL filename. Older examples using `--i` and `--o` do not match the current script.

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

If your system uses Singularity, replace `apptainer` with `singularity`. On HiPerGator, use Apptainer and follow [UF Research Computing's container guidance](https://docs.rc.ufl.edu/software/apps/apptainer/usage/).

Published `latest` images and existing `.sif` files may contain a different script version from your checkout. Record the versions you use; rebuilding or replacing a `.sif` is a separate step from updating repository code.

### What the converter creates

The script converts VTK files to STL, combines and smooths the left/right pial surfaces, combines and smooths the selected non-cortical structures, and merges the smoothed meshes into the final brain STL. The current code excludes `aseg.final.14_24` from the combined model because it contains CSF and can create an unwanted shell.

Intermediate files stay in the input `surfaces` directory, including `cortex.stl`, `cortex_smoothed.stl`, `non-cortex.stl`, and `non-cortex_smoothed.stl`. The combined brain is saved to the output filename you supplied. Merging meshes does not guarantee a watertight, printable solid; inspect the result before printing.

## HiPerGator student workflow

This example follows the PSY4930 Module 4 assignment. It uses the FreeSurfer results from Module 3 and creates one combined STL per subject: **two STL files** for the default subject list, or one if you select only one subject.

### Copy and edit the script

The course script is available in `/blue/psy4930/share/data/Module4`. **Copy it; do not move it.** Save your copy in your own course directory, edit it, and submit that copy. You can also save the script below as `3dprintprep-student.sh`.

Before submitting:

- Change `USER@ufl.edu` to your email address and `your_username` to your GatorLink username.
- Check `BASE_DIR` against your actual Module 3 FreeSurfer results. Keep `sub-6367` and `sub-6303` for the assignment unless instructed otherwise.
- Keep `--account=psy4930` and `--qos=psy4930` for the course allocation. For another project, use an account/QOS you are authorized to use and update the data/container paths. These settings are course-specific.
- The 8 GB memory request and 40-minute time limit come from the student example. Adjust them for larger workloads and your allocation's limits.

| Setting | Course path or value |
| --- | --- |
| Shared script directory | `/blue/psy4930/share/data/Module4` |
| FreeSurfer results | `/blue/psy4930/share/students/${USERNAME}/Module3/ADNI_bids/derivatives/freesurfer` |
| Output directory | `${BASE_DIR}/3dprint` |
| FSQC image | `/blue/psy4930/share/data/neurotools/fsqc.sif` |
| Conversion image | `/blue/psy4930/share/data/neurotools/3dprintprep.sif` |
| FreeSurfer module | `freesurfer/7.4.1` |
| FreeSurfer license | `/apps/freesurfer/license/license.txt` |
| Slurm account and QOS | `psy4930` |

These shared paths are provided by the course; they are not files distributed in this repository. Verify that they are available in your course environment.

### Complete Slurm script

This version retains the course paths and allocation settings, uses a subject array, and stops if a command fails or an expected output is missing.

```bash
#!/bin/bash
#SBATCH --job-name=3dprintprep-student
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=USER@ufl.edu
#SBATCH --ntasks=1
#SBATCH --mem=8gb
#SBATCH --time=00:40:00
#SBATCH --account=psy4930
#SBATCH --qos=psy4930
#SBATCH --output=3dprintprep_%j.log

set -eo pipefail

pwd; hostname; date

# STUDENT CONFIGURATION: edit your email above and the values below.
USERNAME="your_username"
SUBJECTS=(sub-6367 sub-6303)
BASE_DIR="/blue/psy4930/share/students/${USERNAME}/Module3/ADNI_bids/derivatives/freesurfer"

OUT_DIR="${BASE_DIR}/3dprint"
FS_LICENSE_PATH="/apps/freesurfer/license/license.txt"
FSQC_IMAGE="/blue/psy4930/share/data/neurotools/fsqc.sif"
PRINT_IMAGE="/blue/psy4930/share/data/neurotools/3dprintprep.sif"

cd "$BASE_DIR" || { echo "ERROR: Could not find $BASE_DIR"; exit 1; }
mkdir -p "$OUT_DIR"

module load apptainer
module load freesurfer/7.4.1

for FILE in "$FS_LICENSE_PATH" "$FSQC_IMAGE" "$PRINT_IMAGE"; do
    [ -r "$FILE" ] || { echo "ERROR: Cannot read $FILE"; exit 1; }
done
for SUBJ in "${SUBJECTS[@]}"; do
    [ -d "${BASE_DIR}/${SUBJ}" ] || {
        echo "ERROR: Missing FreeSurfer subject directory: ${BASE_DIR}/${SUBJ}"
        exit 1
    }
done

echo "Step 1: Running FSQC and generating shape surfaces..."

# Mount the host FreeSurfer installation and its license into FSQC.
# /apps is required so the container can read FS_LICENSE_PATH.
apptainer run \
    --env FREESURFER_HOME=/opt/freesurfer \
    --env "FS_LICENSE=${FS_LICENSE_PATH}" \
    --env "PATH=/opt/freesurfer/bin:$PATH" \
    -B "$PWD":/in \
    -B "$OUT_DIR":/out \
    -B /apps \
    -B "$FREESURFER_HOME":/opt/freesurfer \
    "$FSQC_IMAGE" \
    --subjects_dir /in \
    --subjects "${SUBJECTS[@]}" \
    --output_dir /out \
    --shape

echo "Step 2: Converting each subject's surfaces to STL..."

for SUBJ in "${SUBJECTS[@]}"; do
    SURF_DIR="${OUT_DIR}/brainprint/${SUBJ}/surfaces"
    [ -d "$SURF_DIR" ] || {
        echo "ERROR: Missing $SURF_DIR; check the FSQC log/output."
        exit 1
    }

    apptainer run \
        -B "$SURF_DIR":/in \
        -B "$OUT_DIR":/out \
        "$PRINT_IMAGE" \
        /in \
        "/out/${SUBJ}.stl"

    [ -s "${OUT_DIR}/${SUBJ}.stl" ] || {
        echo "ERROR: No nonempty STL created for ${SUBJ}."
        exit 1
    }
done

# The original assignment uses the following command for group access.
# Uncomment it if your course requires this sharing permission:
# chmod -R 775 "$OUT_DIR"

echo "Processing complete. Check ${OUT_DIR} for your .stl files."
date
```

The FreeSurfer bind exposes the loaded host installation as `/opt/freesurfer` inside FSQC. The `FREESURFER_HOME`, `FS_LICENSE`, and `PATH` settings tell the container where to find that installation and license. Keep these mounts when using this course workflow.

### Submit and check the results

From your own working directory on `/blue`, submit your edited script:

```bash
sbatch 3dprintprep-student.sh
```

Check `3dprintprep_<jobID>.log` in the submission directory. Successful output for the default subjects is:

```text
${BASE_DIR}/3dprint/sub-6367.stl
${BASE_DIR}/3dprint/sub-6303.stl
```

The VTK files and intermediate STL files remain under `${BASE_DIR}/3dprint/brainprint/<subject>/surfaces/`. Follow the course's group-access requirements if the instructor needs to inspect your results.

You can also run the steps interactively for practice, but do the processing in a scheduled compute-node session. See [HiPerGator computation guidance](https://help.rc.ufl.edu/doc/HPG_Computation); submit the script with `sbatch` for the batch workflow.

## 3. Inspect and prepare the model for printing

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
