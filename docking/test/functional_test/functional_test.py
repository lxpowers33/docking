from unittest import TestCase
from docking.docking_class import Docking_Set
from docking.utilities import score_no_vdW
import os
import time


test_data_directory = os.path.dirname(os.path.realpath(__file__))+'/test_data'

class TestDocking_Set(TestCase):

    def test_dock_rmsd(self):
        self.run_docking_set()
        self.run_rmsd_set()

    def run_docking_set(self):
        test_directory = os.getcwd() + '/testrun1'
        docking_config = [{'folder':test_directory+'/test_docking1',
                           'name':'test_docking1',
                           'grid_file':test_data_directory+'/2B7A.zip',
                           'prepped_ligand_file':test_data_directory+'/2W1I_lig.mae',
                           'glide_settings': {'num_poses': 20}},
                          {'folder': test_directory + '/test_docking2',
                           'name': 'test_docking2',
                           'grid_file': test_data_directory+'/2B7A.zip',
                           'prepped_ligand_file': test_data_directory+'/2W1I_lig.mae',
                           'glide_settings': {'num_poses': 20}}
                          ]
        run_config = {'run_folder':test_directory+'/run',
                     'group_size':5,
                     'partition':'rondror',
                      'dry_run':False}

        dock_set = Docking_Set()
        dock_set.run_docking_set(docking_config, run_config)

        for i in range(1,15):
            done_list, log_list = dock_set.check_docking_set_done(docking_config)
            if (all(done_list)):
                print("Docking Completed")
                return
            else:
                print("Waiting for docking completion ...")
            time.sleep(60)
        self.fail("Test failed, did not output docking within 15 minutes")

    def run_rmsd_set(self):
        test_directory = os.getcwd() + '/testrun1'
        docking_config = [{'folder':test_directory+'/test_docking1',
                           'name':'test_docking1',
                           'grid_file':test_data_directory+'/2B7A.zip',
                           'prepped_ligand_file':test_data_directory+'/2W1I_lig.mae',
                           'ligand_file':test_data_directory+'/2W1I_lig_correct.mae',
                           'glide_settings': {'num_poses': 10}},
                          {'folder': test_directory + '/test_docking2',
                           'name': 'test_docking2',
                           'grid_file': test_data_directory+'/2B7A.zip',
                           'prepped_ligand_file': test_data_directory+'/2W1I_lig.mae',
                           'ligand_file':test_data_directory+'/2W1I_lig_correct.mae',
                           'glide_settings': {'num_poses': 10}}
                          ]

        run_config = {'run_folder':test_directory+'/run',
                     'group_size':1,
                     'partition':'rondror',
                      'dry_run':False}
        dock_set = Docking_Set()
        dock_set.run_rmsd_set(docking_config, run_config)

        for i in range(1,15):
            if (all(dock_set.check_rmsd_set_done(docking_config))):
                print("RMSD  Completed")
                return
            else:
                print("Waiting for rmsd calculation completion ...")
            time.sleep(60)
        self.fail("Test failed, did not output rmsd within 15 minutes")


    def test_docking_rmsd_delete(self):
        test_directory = os.getcwd() + '/testrun2'
        all_config = [{'folder': test_directory + '/test_docking1',
                       'name': 'test_docking1',
                       'grid_file': test_data_directory + '/2B7A.zip',
                       'prepped_ligand_file': test_data_directory + '/2W1I_lig.mae',
                       'ligand_file': test_data_directory + '/2W1I_lig_correct.mae',
                       'glide_settings': {'num_poses': 10}},
                      {'folder': test_directory + '/test_docking2',
                       'name': 'test_docking2',
                       'grid_file': test_data_directory + '/2B7A.zip',
                       'prepped_ligand_file': test_data_directory + '/2W1I_lig.mae',
                       'ligand_file': test_data_directory + '/2W1I_lig_correct.mae',
                       'glide_settings': {'num_poses': 10}}
                      ]

        run_config = {'run_folder': test_directory + '/run',
                      'group_size': 1,
                      'partition': 'rondror',
                      'dry_run': False}
        dock_set = Docking_Set()
        dock_set.run_docking_rmsd_delete(all_config, run_config)

        for i in range(1, 15):

            if all(dock_set.check_rmsd_set_done(all_config)):
                print("RMSD  Completed")
                # check that docking is not done
                done_list, log_list = dock_set.check_docking_set_done(all_config)
                if any(done_list):
                    self.fail('Test failed, pose viewers not deleted')
                return
            else:
                print("Waiting for rmsd calculation completion ...")
            time.sleep(60)

        self.fail("Test failed, did not output rmsd within 15 minutes")

    def test_docking_set_inplace(self):
      '''
      #will use a .mae containing multiple ligands some of which have clashes
      From top level directory 
      $SCHRODINGER/run python3 -m unittest docking.test.functional_test.functional_test.TestDocking_Set.test_docking_set_inplace
      '''
      
      test_directory = os.getcwd() + '/testrun3'

      #Note: docking method is set to inplace
      docking_config = [{'folder':test_directory+'/test_docking1',
                         'name':'test_docking1',
                         'grid_file':test_data_directory+'/2B7A.zip',
                         'prepped_ligand_file':test_data_directory+'/2W1I_3_poses.mae',
                         'glide_settings': {'num_poses': 1, 'docking_method': 'inplace'}},
                        ]
      run_config = {'run_folder':test_directory+'/run',
                   'group_size':5,
                   'partition':'rondror',
                      'dry_run':False}
      
      dock_set = Docking_Set()
      dock_set.run_docking_set(docking_config, run_config)

      for i in range(1,15):
          done_list, log_list = dock_set.check_docking_set_done(docking_config)
          if (all(done_list)):
              print("Docking Completed")

              #Note: get the scores, not that pose1 has purposeful clashes
              results = dock_set.get_docking_gscores(docking_config, mode='multi')
              results_by_ligand = results['test_docking1']
              self.assertEqual(results_by_ligand['2W1I_pose2'][0]['GScore'], -7.07)
              self.assertEqual(results_by_ligand['2W1I_pose1'][0]['GScore'], 10000.00)
              self.assertEqual(results_by_ligand['2W1I_pose1'][0]['vdW'], 14374956.0)
              #compute the score without vdW terms
              self.assertTrue(score_no_vdW(results_by_ligand['2W1I_pose1'][0]) - 4.89 < 0.0001 ) 

              return
          else:
              print("Waiting for docking completion ...")
          time.sleep(60)
      self.fail("Test failed, did not output docking within 15 minutes")

      
