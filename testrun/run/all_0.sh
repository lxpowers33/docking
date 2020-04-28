#!/bin/bash
cd /home/users/lxpowers/projects/combind/code_modules/docking/testrun/test_docking1
$SCHRODINGER/glide -WAIT test_docking1.in
$SCHRODINGER/run rmsd.py -use_neutral_scaffold -pv second -c test_docking1_rmsd.csv /home/users/lxpowers/projects/combind/code_modules/docking/docking/test/functional_test/test_data/2W1I_lig_correct.mae test_docking1_pv.maegz
rm test_docking1_pv.maegz
cd /home/users/lxpowers/projects/combind/code_modules/docking/testrun/run
