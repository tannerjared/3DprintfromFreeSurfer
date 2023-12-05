# 3DprintfromFreeSurfer

Note that this requires FreeSurfer installed (version >7.4 is best): https://surfer.nmr.mgh.harvard.edu/fswiki/rel7downloads.

FSQC and various Python packages also need to be installed:
```
pip install fsqc pymeshlab vtk stl
```

Steps to run:
1. Process a brain MRI using FreeSufer (version >7.4 is best).
2. Run FSQC (https://github.com/Deep-MI/fsqc) with the --shape flag. An example looks like this (this runs on one subject, if you want this for all processed subjects, leave off the --subjects flag)
   ```
   run_fsqc --subjects_dir ./fs_subjects --subjects jt2021 --output_dir ./fsqc_out --shape
   ```
4. When the run_fsqc script is run, it will create subdirectories within the output directory you specified. One of those is called brainprint. Within that directory there will be a directory for each subject you ran through run_fsqc. The 3Dprintprep.py script currently only works on one brain at a time so call the script something like this (this was called from the directory where the Python script was, which was in the same location as the fsqc_out directory):
   ```
   python 3Dprintprep.py --i ./fsqc_out/brainprint/jt2021/surfaces --o ./fsqc_out/brainprint/jt2021/jt2021.stl
   ```

It's likely best to run all this within a Python virtual environment. Instructions to do that are not included here but generally would look like this

```
virtualenv /path/to/virtual/environment
source /path/to/virtual/environment/bin/activate
```

If on a cluster computer, check documentation for running. You likely can pip install packages but might need to specify install location (it's probably best if you do):
```
pip install --install-option="--prefix=/some/path/" package_name
```

It's much better to use something like Conda/Mamba to install and manage a virtual python environment for this: https://help.rc.ufl.edu/doc/Managing_Python_environments_and_Jupyter_kernels
