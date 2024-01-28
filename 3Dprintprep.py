import os
import argparse

# Check if the required packages are installed
try:
    import pymeshlab
    import vtk
    from stl import mesh
except ImportError as e:
    print(f"Error: {e}")
    print("Please install the required packages using:")
    print("pip install pymeshlab vtk stl")
    exit()

def convert_vtk_to_stl(input_filename, output_filename):
    # Load VTK file
    vtk_reader = vtk.vtkDataSetReader()
    vtk_reader.SetFileName(input_filename)
    vtk_reader.Update()

    # Convert to STL
    vtk_to_stl = vtk.vtkDataSetSurfaceFilter()
    vtk_to_stl.SetInputConnection(vtk_reader.GetOutputPort())
    vtk_to_stl.Update()

    # Write STL file
    stl_writer = vtk.vtkSTLWriter()
    stl_writer.SetFileName(output_filename)
    stl_writer.SetInputConnection(vtk_to_stl.GetOutputPort())
    stl_writer.Write()

def combine_cortex(input_directory, output_directory):
    ms = pymeshlab.MeshSet()

    # Load lh.pial.stl and rh.pial.stl and merge them
    ms.load_new_mesh(os.path.join(input_directory, 'lh.pial.stl'))
    ms.load_new_mesh(os.path.join(input_directory, 'rh.pial.stl'))
    ms.apply_filter('generate_by_merging_visible_meshes', mergevertices=True)

    # Save the combined cerebrum mesh to the input directory
    output_cortex = os.path.join(input_directory, 'cortex.stl')
    ms.save_current_mesh(output_cortex)

    # Smooth cortex.stl
    percentage_delta = pymeshlab.Percentage(0.1)  # You can adjust the value accordingly
    ms.apply_filter('apply_coord_laplacian_smoothing_scale_dependent', stepsmoothnum=100, delta=percentage_delta)

    # Save the smoothed cerebrum mesh to the input directory
    output_cortex_smoothed = os.path.join(input_directory, 'cortex_smoothed.stl')
    ms.save_current_mesh(output_cortex_smoothed)

def combine_non_cortex(input_directory, output_directory):
    ms = pymeshlab.MeshSet()

    # Load specified files for non-cortex
    non_cortex_files = [
        'aseg.final.7_8_16_46_47.stl', 'aseg.final.10.stl', 'aseg.final.11_12_26.stl',
        'aseg.final.13.stl', 'aseg.final.14_24.stl', 'aseg.final.17.stl', 'aseg.final.18.stl',
        'aseg.final.26.stl', 'aseg.final.28.stl', 'aseg.final.49.stl', 'aseg.final.50_51_58.stl',
        'aseg.final.52.stl', 'aseg.final.53.stl', 'aseg.final.54.stl', 'aseg.final.60.stl',
        'aseg.final.251_252_253_254_255.stl'
    ]

    # Load specified files for non-cortex and merge them
    for non_cortex_file in non_cortex_files:
        ms.load_new_mesh(os.path.join(input_directory, non_cortex_file))

    # Apply the 'generate_by_merging_visible_meshes' filter with 'mergevertices' set to True
    ms.apply_filter('generate_by_merging_visible_meshes', mergevertices=True)
    
    # Save the combined non-cortex mesh to the input directory
    output_non_cortex = os.path.join(input_directory, 'non-cortex.stl')
    ms.save_current_mesh(output_non_cortex)

    # Smooth non-cortex.stl
    percentage_delta = pymeshlab.Percentage(0.1)  # You can adjust the value accordingly
    ms.apply_filter('apply_coord_laplacian_smoothing_scale_dependent', stepsmoothnum=100, delta=percentage_delta)
    
    # Save the smoothed non-cortex mesh to the input directory
    output_non_cortex_smoothed = os.path.join(input_directory, 'non-cortex_smoothed.stl')
    ms.save_current_mesh(output_non_cortex_smoothed)

def combine_and_save_brain(input_directory, output_filename):
    ms = pymeshlab.MeshSet()

    # Load and merge cortex.stl and non-cortex.stl
    ms.load_new_mesh(os.path.join(input_directory, 'cortex_smoothed.stl'))
    ms.load_new_mesh(os.path.join(input_directory, 'non-cortex_smoothed.stl'))
    ms.apply_filter('generate_by_merging_visible_meshes', mergevertices=True)
    
    # Save the combined mesh
    output_combined = os.path.join(output_filename)
    ms.save_current_mesh(output_combined)

def main():
    parser = argparse.ArgumentParser(description='Combine specified STL files and apply smoothing.')
    parser.add_argument('input_directory', type=str, help='Input directory containing STL files')
    parser.add_argument('output_filename', type=str, help='Output combined and cleaned STL file')

    args = parser.parse_args()

    # Convert VTK files to STL
    vtk_files = [f for f in os.listdir(args.input_directory) if f.endswith(".vtk")]
    for vtk_file in vtk_files:
        vtk_path = os.path.join(args.input_directory, vtk_file)
        stl_file = os.path.splitext(vtk_file)[0] + ".stl"
        stl_path = os.path.join(args.input_directory, stl_file)
        convert_vtk_to_stl(vtk_path, stl_path) 
    
    # Combine and smooth cerebrum
    combine_cortex(args.input_directory, args.input_directory)
    
    # Combine and smooth non-cortex
    combine_non_cortex(args.input_directory, args.input_directory)

    # Combine and save combined cortex and non-cortex to the input directory
    combine_and_save_brain(args.input_directory, args.output_filename)

if __name__ == "__main__":
    main()
