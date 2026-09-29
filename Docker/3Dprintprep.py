import os
import sys
import argparse

# ---------------------------------------------------------
# Smoothing parameters
# ---------------------------------------------------------

CORTEX_SMOOTHING_STEPS = 100

# VTK windowed-sinc smoothing for non-cortical structures
NON_CORTEX_SMOOTHING_ITERATIONS = 30

# Lower = more smoothing.
# Start at 0.05.
# If still blocky: 0.02, then 0.01.
NON_CORTEX_PASSBAND = 0.2

# ---------------------------------------------------------
# Check if the required packages are installed
# ---------------------------------------------------------
try:
    import pymeshlab
    import vtk
    from stl import mesh
except ImportError as e:
    print(f"Error: {e}")
    print("Please install the required packages using:")
    print("pip install pymeshlab vtk numpy-stl")
    sys.exit(1)


def convert_vtk_to_stl(input_filename, output_filename):
    """Convert a VTK surface file to STL."""

    vtk_reader = vtk.vtkDataSetReader()
    vtk_reader.SetFileName(input_filename)
    vtk_reader.Update()

    vtk_to_stl = vtk.vtkDataSetSurfaceFilter()
    vtk_to_stl.SetInputConnection(vtk_reader.GetOutputPort())
    vtk_to_stl.Update()

    stl_writer = vtk.vtkSTLWriter()
    stl_writer.SetFileName(output_filename)
    stl_writer.SetInputConnection(vtk_to_stl.GetOutputPort())
    stl_writer.Write()

def smooth_stl_windowed_sinc(
    input_filename,
    output_filename,
    iterations=30,
    passband=0.05
):
    """
    Smooth an STL using VTK windowed-sinc smoothing.

    This is intended to reduce voxel/marching-cubes stair-step artifacts
    while preserving overall surface geometry better than repeated
    Laplacian smoothing.
    """

    # Read STL
    reader = vtk.vtkSTLReader()
    reader.SetFileName(input_filename)
    reader.Update()

    # Clean duplicate/coincident points
    cleaner = vtk.vtkCleanPolyData()
    cleaner.SetInputConnection(reader.GetOutputPort())
    cleaner.Update()

    # Ensure triangular polygons
    triangulate = vtk.vtkTriangleFilter()
    triangulate.SetInputConnection(cleaner.GetOutputPort())
    triangulate.Update()

    # Windowed-sinc smoothing
    smoother = vtk.vtkWindowedSincPolyDataFilter()
    smoother.SetInputConnection(triangulate.GetOutputPort())

    smoother.SetNumberOfIterations(iterations)
    smoother.SetPassBand(passband)

    # Better numerical stability
    smoother.NormalizeCoordinatesOn()

    # Allow smoothing across the voxel-derived mesh
    smoother.FeatureEdgeSmoothingOff()
    smoother.BoundarySmoothingOn()
    smoother.NonManifoldSmoothingOn()

    # Nuttall is VTK's recommended window
    smoother.SetWindowFunctionToNuttall()

    smoother.Update()

    # Write smoothed STL
    writer = vtk.vtkSTLWriter()
    writer.SetFileName(output_filename)
    writer.SetInputConnection(smoother.GetOutputPort())
    writer.Write()

def combine_cortex(input_directory):
    """Combine left and right pial surfaces and create a smoothed cortex."""

    ms = pymeshlab.MeshSet()

    # Load left and right pial surfaces
    ms.load_new_mesh(
        os.path.join(input_directory, "lh.pial.stl")
    )

    ms.load_new_mesh(
        os.path.join(input_directory, "rh.pial.stl")
    )

    # Merge hemispheres
    ms.apply_filter(
        "generate_by_merging_visible_meshes",
        mergevertices=True
    )

    # Save unsmoothed cortex
    output_cortex = os.path.join(
        input_directory,
        "cortex.stl"
    )

    ms.save_current_mesh(output_cortex)

    # Smooth cortex
    percentage_delta = pymeshlab.PercentageValue(0.1)

    ms.apply_filter(
        "apply_coord_laplacian_smoothing_scale_dependent",
        stepsmoothnum=CORTEX_SMOOTHING_STEPS,
        delta=percentage_delta
    )

    # Save smoothed cortex
    output_cortex_smoothed = os.path.join(
        input_directory,
        "cortex_smoothed.stl"
    )

    ms.save_current_mesh(output_cortex_smoothed)


def combine_non_cortex(input_directory):
    """Combine all non-cortical structures and smooth them together."""

    ms = pymeshlab.MeshSet()

    # Cerebellum, brainstem, subcortical structures, and corpus callosum.
    # aseg.final.14_24.stl is intentionally excluded because it contains
    # CSF and can generate an unwanted shell around the cortex.
    non_cortex_files = [
        "aseg.final.7_8_16_46_47.stl",
        "aseg.final.10.stl",
        "aseg.final.11_12_26.stl",
        "aseg.final.13.stl",
        "aseg.final.17.stl",
        "aseg.final.18.stl",
        "aseg.final.28.stl",
        "aseg.final.49.stl",
        "aseg.final.50_51_58.stl",
        "aseg.final.52.stl",
        "aseg.final.53.stl",
        "aseg.final.54.stl",
        "aseg.final.60.stl",
        "aseg.final.251_252_253_254_255.stl"
    ]

    # Load all non-cortical structures
    for filename in non_cortex_files:
        ms.load_new_mesh(
            os.path.join(
                input_directory,
                filename
            )
        )

    # Merge everything first
    ms.apply_filter(
        "generate_by_merging_visible_meshes",
        mergevertices=True
    )

    # Save merged unsmoothed non-cortex mesh
    output_non_cortex = os.path.join(
        input_directory,
        "non-cortex.stl"
    )

    ms.save_current_mesh(output_non_cortex)

    # Destination for windowed-sinc smoothed mesh
    output_non_cortex_smoothed = os.path.join(
        input_directory,
        "non-cortex_smoothed.stl"
    )

    print(
        "Applying VTK windowed-sinc smoothing "
        f"({NON_CORTEX_SMOOTHING_ITERATIONS} iterations, "
        f"passband={NON_CORTEX_PASSBAND})..."
    )

    smooth_stl_windowed_sinc(
        output_non_cortex,
        output_non_cortex_smoothed,
        iterations=NON_CORTEX_SMOOTHING_ITERATIONS,
        passband=NON_CORTEX_PASSBAND
    )


def combine_and_save_brain(
    input_directory,
    output_filename
):
    """Combine the smoothed cortex and non-cortex meshes."""

    ms = pymeshlab.MeshSet()

    ms.load_new_mesh(
        os.path.join(
            input_directory,
            "cortex_smoothed.stl"
        )
    )

    ms.load_new_mesh(
        os.path.join(
            input_directory,
            "non-cortex_smoothed.stl"
        )
    )

    # Merge only; no additional smoothing
    ms.apply_filter(
        "generate_by_merging_visible_meshes",
        mergevertices=True
    )

    # Create destination directory if necessary
    output_directory = os.path.dirname(
        os.path.abspath(
            output_filename
        )
    )

    os.makedirs(
        output_directory,
        exist_ok=True
    )

    ms.save_current_mesh(
        output_filename
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Convert FreeSurfer/FSQC VTK surfaces to STL, "
            "combine the cortical and non-cortical meshes, "
            "apply smoothing, and produce a combined STL "
            "suitable for 3D-print preparation."
        )
    )

    parser.add_argument(
        "input_directory",
        type=str,
        help=(
            "Directory containing the FSQC BrainPrint "
            "VTK surface files"
        )
    )

    parser.add_argument(
        "output_filename",
        type=str,
        help="Filename for the final combined STL"
    )

    args = parser.parse_args()

    input_directory = os.path.abspath(
        args.input_directory
    )

    output_filename = os.path.abspath(
        args.output_filename
    )

    if not os.path.isdir(
        input_directory
    ):
        parser.error(
            f"Input directory does not exist: "
            f"{input_directory}"
        )

    # ---------------------------------------------------------
    # Convert VTK files to STL
    # ---------------------------------------------------------
    vtk_files = [
        filename
        for filename in os.listdir(
            input_directory
        )
        if filename.lower().endswith(
            ".vtk"
        )
    ]

    if not vtk_files:
        print(
            "Warning: No VTK files were found. "
            "Existing STL files will be used if present."
        )

    for vtk_file in sorted(
        vtk_files
    ):
        vtk_path = os.path.join(
            input_directory,
            vtk_file
        )

        stl_file = (
            os.path.splitext(
                vtk_file
            )[0]
            + ".stl"
        )

        stl_path = os.path.join(
            input_directory,
            stl_file
        )

        print(
            f"Converting: "
            f"{vtk_file} -> {stl_file}"
        )

        convert_vtk_to_stl(
            vtk_path,
            stl_path
        )

    # ---------------------------------------------------------
    # Process cortex
    # ---------------------------------------------------------
    print(
        "Combining and smoothing cortex..."
    )

    combine_cortex(
        input_directory
    )

    # ---------------------------------------------------------
    # Process non-cortex
    # ---------------------------------------------------------
    print(
        "Combining and smoothing "
        "non-cortex structures..."
    )

    combine_non_cortex(
        input_directory
    )

    # ---------------------------------------------------------
    # Final brain
    # ---------------------------------------------------------
    print(
        "Combining cortex and "
        "non-cortex meshes..."
    )

    combine_and_save_brain(
        input_directory,
        output_filename
    )

    print(
        f"Finished: {output_filename}"
    )


if __name__ == "__main__":
    main()
