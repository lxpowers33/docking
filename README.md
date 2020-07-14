# Docking Module

This is a simple module for performing docking tasks. The goal is to provide a common system for naming files, folders
and make parallelizing docking tasks on sherlock easy. This can work as an independent module
for many different projects.

TODO: rewrite job submission to use job arrays
TODO: write tests for protein and ligand prep steps 
TODO: bundle prep steps into in a single job

### Install 
    
    git clone https://github.com/lxpowers33/docking.git
    cd docking
    python3 setup.py install

### Testing
Setup Schrodinger Python3

    ml load chemistry
    ml load schrodinger

In the top level of this module directory, run unit testing 

    $SCHRODINGER/run python3 -m unittest docking/test/unit_test/*.py
    
Run functional testing (only on Sherlock)

    $SCHRODINGER/run python3 -m unittest docking/test/functional_test/*.py

After functional tests run, you can see example docking output in testrun1 and testrun2 folders.

### API and Example Usage
Provide only list of file names and paths, using methods in Docking_Set class. 
Example usage to perform docking and calculate rmsds: 
Docking example: 
    
    #this would be a file called dock_all.py
    #run with $SCHRODINGER/run python3 dock_all.py
    
    #import this docking module
    import sys
    sys.path.insert(0, '<path>/docking')
    from docking.docking_class import Docking_Set, Docking
    
    docking_config = [{'folder':'absolute/path/lig1_to_struc1',
                       'name':'lig1_to_struc1',
                       'grid_file':'absolute/path/gridname_struc1.zip',
                       'prepped_ligand_file': 'absolute/path/ligname1.mae',
                       'glide_settings': {'num_poses': 20}},
                      {'folder': 'absolute/path/test_docking2',
                       'name': 'lig2_to_struc1',
                       'grid_file': 'absolute/path/gridname_struc1.zip',
                       'prepped_ligand_file': 'absolute/path/ligname2.mae',
                       'glide_settings': {'num_poses': 20}}
                      ]
    run_config = {'run_folder':'absolute/path/run',
                 'group_size':5,
                 'partition':'rondror',
                 'dry_run':False}
                 
    dock_set = Docking_Set()
    dock_set.run_docking_set(docking_config, run_config)
    #wait until docking is done to perform rmsd calculations
    for i in range(1,15):
        done_list, log_list = dock_set.check_docking_set_done(docking_config)
        if (all(done_list)):
            print("Docking Completed")
            dock_set.run_rmsd_set(docking_config, run_config)
    print("Docking did not complete in 15 minutes - possible error")

There is also a module for prepping proteins and ligands to use as docking inputs.    
See tests and comments for further details.

    
    sys.path.insert(0, '<path>/docking')

    from docking.prep_class import Prep_Protein_Set

    run_config = {'run_folder': 'prep_run',
        'partition': 'rondror',
        'group_size': 1,
        'dry_run':False }
    
    for s in ['CLC2_5TQQ_model', 'CLC2_5TR1_model', 'state_C_o', 'state_C_oi', 'state_O', 'state_U']:
        target_folder = base + '/' + s
        raw_protein_file = working +'/structures/'+s+'.pdb'
        raw_ligand_file = working +'/structures/MCFA_5TR1.pdb'
        prep_set_info.append(
                {'raw_protein_file': raw_protein_file,
          'raw_ligand_file': raw_ligand_file,
          'save_folder': target_folder,
          'name': s})

    step = sys.argv[1]
    Prepper = Prep_Protein_Set()
    if step == '1':
            Prepper.run_prep_wizard_set(prep_set_info, run_config)
    if step == '3':
            Prepper.run_split_prepped_set(prep_set_info)
    if step == '4':
            Prepper.run_build_grids(prep_set_info, run_config)
    if step == 'r':
            Prepper.report(prep_set_info)