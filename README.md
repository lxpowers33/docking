# Docking Module

This is a simple module for performing docking tasks.

### Install 
    
    git clone https://github.com/lxpowers33/docking.git
    cd docking
    python3 setup.py install

### Testing
Run unit testing 

    python3 -m unittest docking/test/unit_test/*.py
    
Run functional testing (only on Sherlock)

    python3 -m unittest docking/test/functional_test/*.py

### API and Example Usage
Provide only list of file names and paths, using methods in Docking_Set class. 
Example usage to perform docking and calculate rmsds: 

    docking_config = [{'folder':'absolute/path/lig1_to_struc1',
                       'name':'lig1_to_struc1',
                       'grid_file':'absolute/path/gridname_struc1.zip',
                       'prepped_ligand_file': 'absolute/path/ligname1.mae',
                       'glide_settings':{}},
                      {'folder': 'absolute/path/test_docking2',
                       'name': 'lig2_to_struc1',
                       'grid_file': 'absolute/path/gridname_struc1.zip',
                       'prepped_ligand_file': 'absolute/path/ligname2.mae',
                       'glide_settings': {}}
                      ]
    run_config = {'run_folder':'absolute/path/run',
                 'group_size':5,
                 'partition':'rondror',
                 'dry_run':False}
                 
    dock_set = Docking_Set()
    dock_set.run_docking_set(docking_config, run_config)
    #wait until docking is done to perform rmsd calculations
    for i in range(1,15):
        if (all(dock_set.check_docking_set_done(docking_config))):
            print("Docking Completed")
            dock_set.run_rmsd_set(docking_config, run_config)
    print("Docking did not complete in 15 minutes - possible error")
    
See tests and function comments for further details.
