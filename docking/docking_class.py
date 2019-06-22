import os
import docking.utilities

class Docking_Set:
    """
    Carry out operations for a set of docking runs
    These methods require the following inputs:

    docking_set_info: (list of dicts) [{'folder', 'name', 'grid_file', 'prepped_ligand_file', 'glide_settings'}]
        folder: (string)  absolute path to where to store/load the individual docking results
        name: (string) name of docking run to use for files
        grid_file: (string) absolute path to grid file
        prepped_ligand_file: (string) absolute path to ligand file
        glide_settings: {'num_poses'}

    run_config: (dict) {'run_folder', 'group_size', 'partition', 'dry_run'}
        folder: (string) folder to store .sh files, output files for running jobs in batches
        partition: (string) what partition to run on
        group_size: (int) for parallelizing on sherlock, how many tasks to group together, usually 5-10
        dry_run: (Boolean) whether to submit the files with sbatch or not

    rmsd_set_info: (list of dicts) [{'folder', 'name', 'ligand_file'}]
        folder: (string)  absolute path to where to store/load the individual docking results
        name: (string) name of docking run to use for files
        ligand_file: (string) absolute path to ligand file
    """
    def run_docking_set(self, docking_set_info, run_config):
        '''
        Setup and start running a set of docking task
        :return: (None)
        '''
        all_docking = []
        for docking_info in docking_set_info:
            Docking_Run = Docking(docking_info['folder'], docking_info['name'])
            Docking_Run.write_glide_input_file(docking_info['grid_file'],docking_info['prepped_ligand_file'],docking_info['glide_settings'])
            all_docking.append(Docking_Run)
        self._process(run_config, all_docking, type='dock')

    def check_docking_set_done(self, docking_set_info):
        '''
        Check whether a set of docking tasks is finished
        :return: (list of booleans), whether each task in docking_set_info is done
        '''
        done_list = []
        for docking_info in docking_set_info:
            Docking_Run = Docking(docking_info['folder'], docking_info['name'])
            done_list.append(Docking_Run.check_done_dock())
        return done_list

    def run_rmsd_set(self, rmsd_set_info, run_config):
        '''
        Setup and start running a set of rmsd calculation tasks
        This will calculate rmsd of each docked pose to a given pose
        :return: (None)
        '''
        all_docking = []
        for docking_info in rmsd_set_info:
            Docking_Run = Docking(docking_info['folder'], docking_info['name'])
            Docking_Run.add_ligand_file(docking_info['ligand_file'])
            all_docking.append(Docking_Run)
        self._process(run_config, all_docking, type='rmsd')

    def get_docking_results(self, rmsd_set_info):
        '''
        Get the rmsds for each list of poses for each ligand
        :return (list of list of ints)
        '''
        rmsds = []
        for docking_info in rmsd_set_info:
            Docking_Run = Docking(docking_info['folder'], docking_info['name'])
            rmsds.append(Docking_Run.get_docking_rmsd_results())
        return rmsds

    def _process(self, run_config, all_docking, type='dock'):
        '''
        Internal method to run a set of tasks
        '''
        docking_groups = docking.utilities.grouper(run_config['group_size'], all_docking)
        #make the folder if it doesn't exist
        os.makedirs(run_config['run_folder'], exist_ok=True)
        top_wd = os.getcwd() #get current working directory
        os.chdir(run_config['run_folder'])
        for i, docks_group in enumerate(docking_groups):
            file_name = '{}_{}'.format(type, i)
            self._write_sh_file(file_name+'.sh', docks_group, run_config, type)
            if not run_config['dry_run']:
                os.system('sbatch -p {} -t 1:00:00 -o {}.out {}.sh'.format(run_config['partition'], file_name, file_name))
        os.chdir(top_wd) #change back to original working directory

    def _write_sh_file(self, name, docking_list, run_config, type):
        '''
        Internal method to write a sh file to run a set of commands
        '''
        with open(name, 'w') as f:
            f.write('#!/bin/bash\nml load chemistry\nml load schrodinger\n')
            for dock in docking_list:
                f.write('cd {}\n'.format(dock.get_folder()))
                if type == 'rmsd':
                    f.write(dock.get_rmsd_cmd())
                if type == 'dock':
                    f.write(dock.get_dock_cmd())
                f.write('cd {}\n'.format(run_config['run_folder']))

class Docking:
    """
    Carry out low level operations on a single docking run
    """

    def __init__(self, folder, docking_name):
        '''
        :param folder: (string) absolute path to where to store/load the docking results
                        Note that each folder should be for ONE specific docking run
        :param docking_name: (string) name of docking run to use for files
        '''
        self.folder = folder
        os.makedirs(self.folder, exist_ok=True)
        #define all file name conventions here
        self.glide_input_file_name = '{}.in'.format(docking_name)
        self.pose_viewer_file_name = '{}_pv.maegz'.format(docking_name)
        self.rept_file_name = '{}.rept'.format(docking_name)
        self.rmsd_file_name = '{}_rmsd.csv'.format(docking_name)
        self.dock_cmd = '$SCHRODINGER/glide -WAIT {}\n'.format(self.glide_input_file_name)
        self.rmsd_cmd = '$SCHRODINGER/run rmsd.py -use_neutral_scaffold -pv second -c {} {} {}\n'

    def write_glide_input_file(self, grid_file, prepped_file, glide_settings):
        #check glide settings
        #check grid_file and prepped_file exists, otherwise return false + missing file
        with open(self.folder+'/'+self.glide_input_file_name, 'w') as f:
            f.write(commands.format(grid_file, prepped_file))
        return True

    def get_folder(self):
        return self.folder

    def get_dock_cmd(self):
        return self.dock_cmd

    def validate_glide_settings(self, glide_settings):
        return False

    def check_done_dock(self):
        return os.path.isfile(self.pose_viewer_file_name)

    def add_ligand_file(self, ligand_file_name):
        self.ligand_file_name = ligand_file_name

    def get_rmsd_cmd(self):
        return self.rmsd_cmd.format(self.rmsd_file_name, self.ligand_file_name, self.pose_viewer_file_name)

    def check_done_rmsd(self):
        return os.path.isfile(self.folder+'/'+self.rmsd_file_name)

    def get_docking_rmsd_results(self):
        '''
        Get list of rmsds
        Format of csv file:
        "Index","Title","Mode","RMSD","Max dist.","Max dist atom index pair","ASL"
        "1","2W1I_pdb.smi:1","In-place","8.38264277875","11.5320975551","10-20","not atom.element H"
        :return:
        '''
        all_rmsds = []
        rmsd_file_path = self.folder+'/'+self.rmsd_file_name
        assert self.check_done_rmsd(), "Missing rmsd file: " + rmsd_file_path
        with open(rmsd_file_path) as rmsd_file:
            for line in list(rmsd_file)[1:]:
                rmsd = line.split(',')[3].strip('"')
                all_rmsds.append(float(rmsd))
        return all_rmsds

    def get_gscores_emodels(self):
        #TODO
        gscores = []
        emodels = []
        return gscores, emodels

commands = '''GRIDFILE   {}
LIGANDFILE   {}
DOCKING_METHOD   confgen
CANONICALIZE   True
EXPANDED_SAMPLING   False
POSES_PER_LIG   200
POSTDOCK_NPOSE   200
WRITEREPT   True
PRECISION   SP
NENHANCED_SAMPLING   4'''