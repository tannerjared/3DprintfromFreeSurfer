# 3D Print from FreeSurfer

Note that this requires FreeSurfer installed (version >7.4 is best but >6.0 should work): https://surfer.nmr.mgh.harvard.edu/fswiki/rel7downloads.

Note: it's better to use something like Conda/Mamba to install and manage a virtual python environment for this, especially if running on a cluster computer: https://help.rc.ufl.edu/doc/Managing_Python_environments_and_Jupyter_kernels
Instructions to do that are not included here but generally would look like this (or check the documentation above for other options.
```
virtualenv /path/to/virtual/environment
source /path/to/virtual/environment/bin/activate
```

FSQC (https://github.com/Deep-MI/fsqc) and various Python packages also need to be installed (if you want to install fsqc a different way, check the link for options):
```
pip install fsqc pymeshlab vtk stl
```

If on a cluster computer, check documentation for running. You likely can pip install packages but might need to specify install location (it's probably best if you do):
```
pip install --install-option="--prefix=/some/path/" package_name
```

## Steps to run
1. Process a brain MRI using FreeSufer (version >7.4 is best). This can be done from a T1 NIfTI or from the T1 DICOM files.
3. Run FSQC with the --shape flag. An example looks like this (this runs on one subject, if you want this for all processed subjects, leave off the --subjects flag)
   ```
   run_fsqc --subjects_dir ./fs_subjects --subjects jt2021 --output_dir ./fsqc_out --shape
   ```
4. When the run_fsqc script is run, it will create subdirectories within the output directory you specified. One of those is called brainprint. Within that directory there will be a directory for each subject you ran through run_fsqc.
5. Download the 3Dprintprep.py script. It takes the VTK files created by the run_fsqc with --shape option, converts them to STL, combines the cortex files and smooths them, combines the needed non-cortex files and smooths them, and then saves out the combined STL file as specified by the user. The other STL files, including non-smoothed and smoothed cortex and non-cortex files are saved in the input directory where all the VTK and other created STL files are. You can save the final output to that directory or any other location.
6. The 3Dprintprep.py script currently only works on one brain at a time so call the script something like this (this was called from the directory where the Python script was, which was in the same location as the fsqc_out directory):
   ```
   python 3Dprintprep.py --i ./fsqc_out/brainprint/jt2021/surfaces --o ./fsqc_out/brainprint/jt2021/jt2021.stl
   ```

## Post-processing
You can use 3D modeling software of your choice to do any additional processing as needed. I typically import the STL into 3D Builder on Windows 10 or Windows 11, fix errors (pop-up when importing), and then "settle" the brain to have it rest on the medulla and temporal lobes (typically the auto settle in 3D Builder works well).
