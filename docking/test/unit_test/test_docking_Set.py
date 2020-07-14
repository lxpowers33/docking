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
                           'glide_settings': {'num_poses': 10}},
                          {'folder': test_directory + '/test_docking2',
                           'name': 'test_docking2',
                           'grid_file': test_directory+'/testfile.zip',
                           'prepped_ligand_file': test_directory+'/testfile.mae',
                           'glide_settings': {'num_poses': 10}}
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
                             'cd {}'.format(test_directory+'/test_docking1'),
                             '$SCHRODINGER/glide -WAIT test_docking1.in',
                             'cd {}'.format(test_directory+'/run'),
                             'cd {}'.format(test_directory + '/test_docking2'),
                             '$SCHRODINGER/glide -WAIT test_docking2.in',
                             'cd {}'.format(test_directory + '/run')]
        with open(sh_file, "r") as f:
            for i, line in enumerate(f):
                self.assertEqual(line, correct_lines_sh[i]+'\n')

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
        #should write 1 file, a .in file within the dock folder
        sh_file = test_directory + '/run/rmsd_0.sh'
        self.assertTrue(os.path.isfile(sh_file))
        #check that sh file contains correct lines
        correct_lines_sh = ['#!/bin/bash',
                            'cd {}'.format(test_directory + '/test_docking1'),
                            '$SCHRODINGER/run rmsd.py -use_neutral_scaffold -pv second -c test_docking1_rmsd.csv {} test_docking1_pv.maegz'.format(test_directory + '/testfile.mae'),
                            'cd {}'.format(test_directory + '/run'),
                            'cd {}'.format(test_directory + '/test_docking2'),
                            '$SCHRODINGER/run rmsd.py -use_neutral_scaffold -pv second -c test_docking2_rmsd.csv {} test_docking2_pv.maegz'.format(test_directory + '/testfile.mae'),
                            'cd {}'.format(test_directory + '/run')]

        with open(sh_file, "r") as f:
            for i, line in enumerate(f):
                self.assertEqual(line, correct_lines_sh[i] + '\n')

    def test_run_docking_rmsd_delete_set(self):
        all_config = [{'folder':test_directory+'/test_docking1',
                           'name':'test_docking1',
                           'grid_file':test_directory+'/testfile.zip',
                           'prepped_ligand_file':test_directory+'/testfile.mae',
                           'ligand_file': test_directory + '/testfile.mae',
                           'glide_settings':{'num_poses': 10}},
                          {'folder': test_directory + '/test_docking2',
                           'name': 'test_docking2',
                           'grid_file': test_directory+'/testfile.zip',
                           'prepped_ligand_file': test_directory+'/testfile.mae',
                           'ligand_file': test_directory + '/testfile.mae',
                           'glide_settings': {'num_poses': 10}}]

        run_config = {'run_folder': test_directory + '/run',
                    'group_size': 5,
                    'partition': 'rondor',
                    'dry_run': True}

        dock_set = Docking_Set()
        dock_set.run_docking_rmsd_delete(all_config, run_config)
        sh_file = test_directory + '/run/all_0.sh'
        self.assertTrue(os.path.isfile(sh_file))
        # check that sh file contains correct lines
        correct_lines_sh = ['#!/bin/bash',
                            'cd {}'.format(test_directory + '/test_docking1'),
                            '$SCHRODINGER/glide -WAIT test_docking1.in',
                            '$SCHRODINGER/run rmsd.py -use_neutral_scaffold -pv second -c test_docking1_rmsd.csv {} test_docking1_pv.maegz'.format(
                                test_directory + '/testfile.mae'),
                            'rm test_docking1_pv.maegz',
                            'cd {}'.format(test_directory + '/run'),
                            'cd {}'.format(test_directory + '/test_docking2'),
                            '$SCHRODINGER/glide -WAIT test_docking2.in',
                            '$SCHRODINGER/run rmsd.py -use_neutral_scaffold -pv second -c test_docking2_rmsd.csv {} test_docking2_pv.maegz'.format(
                                test_directory + '/testfile.mae'),
                            'rm test_docking2_pv.maegz',
                            'cd {}'.format(test_directory + '/run')]
        with open(sh_file, "r") as f:
            for i, line in enumerate(f):
                self.assertEqual(line, correct_lines_sh[i] + '\n')
