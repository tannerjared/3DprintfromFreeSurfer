# 3DprintfromFreeSurfer

Steps to run:
1. Process a brain MRI using FreeSufer (Version >7.4 is best).
2. Run FSQC with the --shape flag. An example looks like this: run_fsqc --subjects_dir ./fs_subjects --subjects jt2021 --output_dir ./fsqc_out --shape
3. Run the script like this (change the input directory and output file): python 3DprintPrep.py --i ./fsqc_out/brainprint/jt2021/surfaces --o ./fsqc_out/brainprint/jt2021/jt2021.stl
