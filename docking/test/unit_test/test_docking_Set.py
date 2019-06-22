from unittest import TestCase
from docking.docking_class import Docking_Set
import os
import shutil

test_directory = 'testrun'

class TestDocking_Set(TestCase):

    def tearDown(self):
        if os.path.isdir(test_directory):
            shutil.rmtree(test_directory)

    def test_run_docking_set(self):
        docking_config = [{'folder':test_directory+'/test_docking1',
                           'name':'test_docking1',
                           'grid_file':test_directory+'/testfile.zip',
                           'prepped_ligand_file':test_directory+'/testfile.mae',
                           'glide_settings':{}},
                          {'folder': test_directory + '/test_docking2',
                           'name': 'test_docking2',
                           'grid_file': test_directory+'/testfile.zip',
                           'prepped_ligand_file': test_directory+'/testfile.mae',
                           'glide_settings': {}}
                          ]

        run_config = {'run_folder':test_directory+'/run',
                     'group_size':5,
                     'partition':'rondor',
                      'dry_run':True}

        dock_set = Docking_Set()
        dock_set.run_docking_set(docking_config, run_config)
        #should write 2 files, a .sh run file within the run folder and a .in file within the dock folder
        self.assertTrue(os.path.isfile(test_directory + '/test_docking1/test_docking1.in'))
        self.assertTrue(os.path.isfile(test_directory + '/test_docking2/test_docking2.in'))
        #check the lines on sh file
        sh_file = test_directory + '/run/dock_0.sh'
        self.assertTrue(os.path.isfile(sh_file))
        correct_lines_sh = ['#!/bin/bash',
                            'ml load chemistry',
                            'ml load schrodinger',
                             'cd {}'.format(test_directory+'/test_docking1'),
                             '$SCHRODINGER/glide -WAIT test_docking1.in',
                             'cd {}'.format(test_directory+'/run'),
                             'cd {}'.format(test_directory + '/test_docking2'),
                             '$SCHRODINGER/glide -WAIT test_docking2.in',
                             'cd {}'.format(test_directory + '/run')]
        f = open(sh_file, "r")
        for i, line in enumerate(f):
            self.assertEqual(line, correct_lines_sh[i]+'\n')
        f.close()

    def test_run_rmsd_set(self):
        rmsd_config = [{'folder': test_directory + '/test_docking1',
                           'name': 'test_docking1',
                           'ligand_file': test_directory + '/testfile.mae'},
                          {'folder': test_directory + '/test_docking2',
                           'name': 'test_docking2',
                           'ligand_file': test_directory + '/testfile.mae'}
                          ]
        run_config = {'run_folder': test_directory + '/run',
                      'group_size': 5,
                      'partition': 'rondor',
                      'dry_run': True}
        dock_set = Docking_Set()
        dock_set.run_rmsd_set(rmsd_config, run_config)

    def test_process(self):
        pass

    def test_write_sh_file(self):
        pass
