from unittest import TestCase
from docking.docking_class import Docking_Set
import os
import shutil

test_directory = 'testrun'
test_data_directory = 'test_data'

class TestDocking_Set(TestCase):

    def test_run_docking_set(self):
        docking_config = [{'folder':test_directory+'/test_docking1',
                           'name':'test_docking1',
                           'grid_file':test_data_directory+'/2B7A.zip',
                           'prepped_ligand_file':test_data_directory+'/2W1I_lig.mae',
                           'glide_settings':{}},
                          {'folder': test_directory + '/test_docking2',
                           'name': 'test_docking2',
                           'grid_file': test_data_directory+'/2B7A.zip',
                           'prepped_ligand_file': test_data_directory+'/2W1I_lig.mae',
                           'glide_settings': {}}
                          ]

        run_config = {'run_folder':test_directory+'/run',
                     'group_size':5,
                     'partition':'rondor',
                      'dry_run':False}

        dock_set = Docking_Set()
        dock_set.run_docking_set(docking_config, run_config)

        #dock_set.check_docking_set_done(docking_config)
