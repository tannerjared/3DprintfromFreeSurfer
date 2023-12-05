# 3DprintfromFreeSurfer

Steps to run:
1. Process a brain MRI using FreeSufer (Version >7.4 is best): https://surfer.nmr.mgh.harvard.edu/fswiki/rel7downloads
2. Run FSQC (https://github.com/Deep-MI/fsqc) with the --shape flag. An example looks like this: run_fsqc --subjects_dir ./fs_subjects --subjects jt2021 --output_dir ./fsqc_out --shape
3. Run the script like this (change the input directory and output file): python 3Dprintprep.py --i ./fsqc_out/brainprint/jt2021/surfaces --o ./fsqc_out/brainprint/jt2021/jt2021.stl

Note that this requires FreeSurfer installed, FSQC: `pip install fsqc`, and various Python packages: `pip install pymeshlab vtk stl`
