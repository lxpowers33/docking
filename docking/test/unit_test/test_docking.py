from unittest import TestCase
from docking.docking_class import Docking
import os 

dir_path = os.path.dirname(os.path.realpath(__file__))

class TestDocking(TestCase):

    def test_get_docking_rmsd_results_1(self):
        #test exception thrown for missing rmsd file
        with self.assertRaises(Exception) as context:
            test_docking = Docking(dir_path+'/test_data', 'test_data_noex')
            test_docking.get_docking_rmsd_results()
            self.assertTrue('Missing rmsd file:' in context.exception)

    def test_get_docking_rmsd_results_2(self):
        test_docking = Docking(dir_path+'/test_data', 'test_data')
        rmsd_list = test_docking.get_docking_rmsd_results()
        self.assertEqual(rmsd_list[0], 8.32327059894)
        self.assertEqual(rmsd_list[1], 1.99483243783)
        self.assertEqual(rmsd_list[222], 8.14962597727)
