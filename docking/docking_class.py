import os
import docking.utilities
from schrodinger.structure import StructureReader, StructureWriter
from datetime import datetime, timedelta

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
    def run_docking_set(self, docking_set_info, run_config, incomplete_only=True, log_missing_only=True):
        '''
        Setup and start running a set of docking task
        :return: (None)
        '''
        all_docking = []
        now = datetime.utcnow()

        for docking_info in docking_set_info:
            Docking_Run = Docking(docking_info['folder'], docking_info['name'])

            result = Docking_Run.check_done_dock() and ((now - Docking_Run.dock_date()) < timedelta(2))
            if not (incomplete_only and result):

                result = Docking_Run.check_dock_log() and ((now - Docking_Run.dock_log_date()) < timedelta(2))
                if not (log_missing_only and result):
                    Docking_Run.write_glide_input_file(docking_info['grid_file'],docking_info['prepped_ligand_file'],docking_info['glide_settings'])
                    all_docking.append(Docking_Run)
        self._process(run_config, all_docking, type='dock')

    def check_docking_set_done(self, docking_set_info, after_date=False, datedelta=1):
        '''
        Check whether a set of docking tasks is finished
        :return: (list of booleans), whether each task in docking_set_info is done
        '''
        done_list = []
        log_list = []
        now = datetime.utcnow()

        for docking_info in docking_set_info:
            Docking_Run = Docking(docking_info['folder'], docking_info['name'])
            if (after_date):

                result = Docking_Run.check_done_dock() and ((now - Docking_Run.dock_date()) < timedelta(datedelta))
                done_list.append(result)

                result = Docking_Run.check_dock_log() and ((now - Docking_Run.dock_log_date()) < timedelta(datedelta))
                log_list.append(result)

            else:
                done_list.append(Docking_Run.check_done_dock())
                log_list.append(Docking_Run.check_dock_log())
            
        return done_list, log_list

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

    def check_rmsd_set_done(self, rmsd_set_info):
        '''
        Check whether a set of rmsd  tasks is finished
        :return: (list of booleans), whether each task in rmsd_set_info is done
        '''
        done_list = []
        for rmsd_info in rmsd_set_info:
            Docking_Run = Docking(rmsd_info['folder'], rmsd_info['name'])
            done_list.append(Docking_Run.check_done_rmsd())
        return done_list

    def run_docking_rmsd_delete(self, all_set_info, run_config, incomplete_only=False):
        '''
        Run docking then rmsd, then delete the docking poseviewer file to save space
        :param incomplete_only: (Boolean) whether to only run docking/rmsd for processes without rmsd output
        '''
        all_docking = []
        for docking_info in all_set_info:
            Docking_Run = Docking(docking_info['folder'], docking_info['name'])
            if not (incomplete_only and Docking_Run.check_done_rmsd()):
                Docking_Run.add_ligand_file(docking_info['ligand_file'])
                Docking_Run.write_glide_input_file(docking_info['grid_file'],docking_info['prepped_ligand_file'],docking_info['glide_settings'])
                all_docking.append(Docking_Run)
        self._process(run_config, all_docking, type='all')

    def get_docking_gscores(self, docking_set_info):
        scores = {}
        for docking_info in docking_set_info:
            Docking_Run = Docking(docking_info['folder'], docking_info['name'])
            if Docking_Run.check_done_dock():
                gscores, emodels = Docking_Run.get_gscores_emodels()
                scores[docking_info['name']] = {'gscores':gscores, 'emodels':emodels}
            else:
                scores[docking_info['name']] = None

        return scores

    def get_docking_results(self, rmsd_set_info):
        '''
        Get the rmsds for each list of poses for each ligand
        :return (list of list of ints)
        '''
        rmsds = {}
        for docking_info in rmsd_set_info:
            Docking_Run = Docking(docking_info['folder'], docking_info['name'])
            if Docking_Run.check_done_rmsd():
                rmsds[docking_info['name']] = Docking_Run.get_docking_rmsd_results()
            else:
                rmsds[docking_info['name']] = None

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
            if ('jobname_end' in run_config): 
                file_name = '{}_{}_{}'.format(type, i, run_config['jobname_end'])
            self._write_sh_file(file_name+'.sh', docks_group, run_config, type)
            if not run_config['dry_run']:
                os.system('sbatch -p {} -t 1:00:00 -o {}.out {}.sh'.format(run_config['partition'], file_name, file_name))
        os.chdir(top_wd) #change back to original working directory

    
    def _write_sh_file(self, name, docking_list, run_config, type):
        '''
        Internal method to write a sh file to run a set of commands
        '''
        with open(name, 'w') as f:
            f.write('#!/bin/bash\n')
            for dock in docking_list:
                f.write('cd {}\n'.format(dock.get_folder()))
                if type == 'rmsd':
                    f.write(dock.get_rmsd_cmd())
                if type == 'dock':
                    f.write(dock.get_dock_cmd())
                if type == 'all':
                    f.write(dock.get_dock_cmd())
                    f.write(dock.get_rmsd_cmd())
                    f.write(dock.delete_pose_file())

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
        self.docklog_file_name = '{}.log'.format(docking_name)
        self.rept_file_name = '{}.rept'.format(docking_name)
        self.rmsd_file_name = '{}_rmsd.csv'.format(docking_name)
        self.dock_cmd = '$SCHRODINGER/glide -WAIT {}\n'.format(self.glide_input_file_name)
        self.rmsd_cmd = '$SCHRODINGER/run rmsd.py -use_neutral_scaffold -pv second -c {} {} {}\n'

    def write_glide_input_file(self, grid_file, prepped_file, glide_settings):
        #check glide settings
        #check grid_file and prepped_file exists, otherwise return false + missing file
        with open(self.folder+'/'+self.glide_input_file_name, 'w') as f:
            f.write(commands.format(grid_file, prepped_file, glide_settings['num_poses']))
            if 'keywords' in glide_settings:
                for key, value in glide_settings['keywords'].items():
                    f.write('{} {}\n'.format(key, value))
        return True

    def get_folder(self):
        return self.folder

    def get_dock_cmd(self):
        return self.dock_cmd

    def validate_glide_settings(self, glide_settings):
        return False

    def check_done_dock(self):
        return os.path.isfile(self.folder+'/'+self.pose_viewer_file_name)

    def dock_date(self):
        return datetime.utcfromtimestamp(os.path.getmtime(self.folder+'/'+self.pose_viewer_file_name))

    def check_dock_log(self):
        return os.path.isfile(self.folder+'/'+self.docklog_file_name)

    def dock_log_date(self):
        return datetime.utcfromtimestamp(os.path.getmtime(self.folder+'/'+self.docklog_file_name))

    def delete_pose_file(self):
        return 'rm {}\n'.format(self.pose_viewer_file_name)

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
        rept_file = self.folder+'/'+self.rept_file_name
        
        gscores, emodels, rmsds = [], [], []
        with open(rept_file) as fp:
            for line in fp:
                line = line.strip().split()
                if len(line) < 19: continue
                rank, lig_name, lig_index, score = line[:4]
                emodel = line[13]

                if line[1]  == '1':
                    rank, lig_index, score = line[:3]
                    emodel = line[12]

                if not (docking.utilities.isfloat(emodel) and
                        docking.utilities.isfloat(score) and
                        docking.utilities.isfloat(rank)): continue

                gscores.append(float(score))
                emodels.append(float(emodel))

        return gscores, emodels

    def load_poses(self, maxposes=10):
        poses = []
        for i, st in enumerate(StructureReader(self.folder+'/'+self.pose_viewer_file_name)):
            if i > maxposes: break
            if i == 0:
                prot_st = st
                continue
            poses.append(st)  
        return prot_st, poses

commands = '''GRIDFILE   {}
LIGANDFILE   {}
DOCKING_METHOD   confgen
CANONICALIZE   True
POSES_PER_LIG   {}
POSTDOCK_NPOSE   200
WRITEREPT   True
PRECISION   SP
NENHANCED_SAMPLING   4\n'''
