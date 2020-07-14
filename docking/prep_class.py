import os
import docking.utilities
from schrodinger.structure import StructureReader, StructureWriter
from schrodinger.structutils.transform import get_centroid

class Prep_Protein_Set:
    """
       Prep for Proteins

            There might be a few prep situations that we want to account for:
            A) You have an unprepared protein with bound ligand (e.g. a pdb file)
                Seperate the protein and ligand into seperate files. The ligand will be used
                to figure out grid center.
                Start at Step 1
                Only do step 2 if you want to align multiple grids

            B) You have only an unprepared protein
                Start at Step 1, don't provide the ligand file
                Only do step 2 if you want to align multiple grids
                Skip step 3
                At step 4, use option 2 or 3 for providing grid center

            C) You have a prepared protein
                Skip to Prep Step 4, use option 2 or 3 for providing grid center

       Prep for Ligands

    """

    def report(self, prep_set_info):
        """
        Print out a report of what steps are complete for which grids
        :param prep_set_info:
        :return:
        """
        print('name', 'merge', 'Wizard', 'align', 'split', 'grid')
        for single_prep_info in prep_set_info:
            single_prep = Protein_Prep(single_prep_info['save_folder'], single_prep_info['name'])
            print(single_prep_info['name'],
                single_prep.done_merge(),
                single_prep.done_prepwizard(),  
                single_prep.done_align(), 
                single_prep.done_split_prepped(), 
                single_prep.done_grid(),
                single_prep_info['save_folder'])

    def run_prep_wizard_set(self, prep_set_info, run_config, incomplete_only=True):
        """
        Prep Step 1:
        Combine protein raw structure with ligand from raw structure
        If you don't provide the ligand structure, it will just prep the protein

        Run the prep wizard to add hydrogens to protein etc.

        Intermediate files: PDB_id_raw_complex.mae
        Output: PDB_id_prepped_complex.mae

        :param prep_set_info: list of dicts
            [{'raw_protein_file': 'absolute_path/file.mae',
              'raw_ligand_file':'absolute_path/file.mae',
              'save_folder':'absolute_path/save_folder',
              'name': 'PDB_id'}, ...]
        :param run_config:
        :return:
        """
        all_preps = []
        for single_prep_info in prep_set_info:
            single_prep = Protein_Prep(single_prep_info['save_folder'], single_prep_info['name'])

            if not (incomplete_only and single_prep.done_merge()):
                if ('raw_ligand_file' in single_prep_info):
                    single_prep.save_merged_ligand_protein(single_prep_info['raw_protein_file'], single_prep_info['raw_ligand_file'])
                else:
                    single_prep.save_merged_ligand_protein(single_prep_info['raw_protein_file'],
                                                           '')

            if not (incomplete_only and single_prep.done_prepwizard()):
                all_preps.append(single_prep)
                
        self._process(run_config, all_preps, type='step1')

    def run_align_set(self,  prep_set_info, run_config):
        """
        Prep Step 2:
        Need to align all structures of the same protein to create
        aligned ground truth ligand poses

        Output prepped_aligned_complex.mae

        :param prep_set_info:
        :param run_config:
        :return:
        """
        all_preps = []
        for single_prep_info in prep_set_info:
            single_prep = Protein_Prep(single_prep_info['save_folder'], single_prep_info['name'])
            single_prep.add_template_complex(single_prep_info['template_file'])
            all_preps.append(single_prep)
        self._process(run_config, all_preps, type='step2')

    def run_split_prepped_set(self, prep_set_info, incomplete_only=True):
        """
        Prep Step 3:
        Remove the ligand from the prepared, aligned structure
        Write the final protein structure file and ligand structure file
        Output prepped_aligned_protein.mae, prepped_aligned_ligand.mae

        :param prep_set_info:
        :param run_config:
        :return:
        """
        for single_prep_info in prep_set_info:
            single_prep = Protein_Prep(single_prep_info['save_folder'], single_prep_info['name'])
            if not (incomplete_only and single_prep.done_split_prepped()):
                single_prep.split()

    def run_build_grids(self, prep_set_info, run_config, incomplete_only=True):
        """
        Prep Step 4:
        Write the grid using the final protein structure
        There are 3 options for providing the center of the grid
            1) (default) use the ligand extracted in step3, assuming you ran step 3
            :param prep_set_info: list of dicts
            [{'save_folder':'absolute_path/save_folder',
              'name': 'PDB_id'}, ...]

            2) provide the path to a new ligand to use as center of grid, as 'grid_ligand' in info dict
            :param prep_set_info: list of dicts
            [{'save_folder':'absolute_path/save_folder',
              'name': 'PDB_id',
              'grid_ligand': 'absolute_path/save_folder/file.mae'}, ...]

            3) provide x,y,z coordinates as 'grid_ligand'
            :param prep_set_info: list of dicts
            [{'save_folder':'absolute_path/save_folder',
              'name': 'PDB_id',
              'grid_ligand': 'absolute_path/save_folder/file.mae'}, ...]

        Output grid.zip
        :param run_config:
        :return:
        """
        all_preps = []
        for single_prep_info in prep_set_info:
            single_prep = Protein_Prep(single_prep_info['save_folder'], single_prep_info['name'])
            if not (incomplete_only and single_prep.done_grid()):
                if 'grid_ligand' in single_prep_info:
                    single_prep.write_grid_in_file('other_ligand', grid_ligand=single_prep_info['grid_ligand'])
                elif 'grid_xyz' in single_prep_info:
                    single_prep.write_grid_in_file('xyz', xyz=single_prep_info['grid_xyz'])
                else:
                    single_prep.write_grid_in_file('default')
                all_preps.append(single_prep)
                
        self._process(run_config, all_preps, type='step4')

    def ligand_prep_report(self, prep_set_info):
        
        missing = []
        for single_prep_info in prep_set_info:
            single_prep = Ligand_Prep(single_prep_info['save_folder'], single_prep_info['name'])
            if (not single_prep.prep_done()):
                missing.append(single_prep_info['save_folder'])

        print('Missing {}/{}'.format(len(missing), len(prep_set_info)))
        print(missing)

    def run_prep_ligands(self, prep_set_info, run_config, incomplete_only=True):
        all_preps = []
        for single_prep_info in prep_set_info:
            single_prep = Ligand_Prep(single_prep_info['save_folder'], single_prep_info['name'])
            if not (incomplete_only and single_prep.prep_done()):
                single_prep.add_smiles_string(single_prep_info['SMILES'])
                if (not run_config['dry_run']):
                    single_prep.write_smiles_file()
                all_preps.append(single_prep)
                
        self._process(run_config, all_preps, type='smi_prep')

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
            f.write('#!/bin/bash\n')
            for dock in docking_list:
                f.write('cd {}\n'.format(dock.get_folder()))
                if type == 'step1':
                    f.write(dock.get_prep_wizard_cmd())
                if type == 'step2':
                    f.write(dock.get_alignment_cmd())
                if type == 'step4':
                    f.write(dock.get_grid_cmd())
                if type == 'smi_prep':
                    f.write(dock.get_prep_smiles_cmd())
                f.write('cd {}\n'.format(run_config['run_folder']))


class Ligand_Prep: 
    """
    Object to Carry out low level preparation steps on a single ligand
    """
    def __init__(self, folder, ligand_name):
        self.folder = folder
        self.path = folder + '/'
        self.name = ligand_name
        os.makedirs(self.folder, exist_ok=True)

        self.smiles_file = self.name + '.smi'
        self.prepped_file = self.name + '.mae'
        self.prep_smiles_cmd = '$SCHRODINGER/ligprep -WAIT -epik -ismi {} -omae {} \n'

    def get_folder(self):
        return self.folder

    def add_smiles_string(self, smiles):
        self.smiles = smiles

    def write_smiles_file(self):
        with open(self.path + self.smiles_file, 'w') as f:
            f.write(self.smiles)

    def get_prep_smiles_cmd(self):
        return self.prep_smiles_cmd.format(self.smiles_file, self.prepped_file)

    def prep_done(self):
        #check the mae file exists
        return os.path.isfile(self.path+self.prepped_file) 


class Protein_Prep:
    """
    Object to Carry out low level preparation steps on a single ligand/protein structure
    """
    def __init__(self, folder, docking_name):
        self.folder = folder
        self.path = folder + '/'
        os.makedirs(self.folder, exist_ok=True)
        self.name = docking_name

        self.raw_complex = '{}_raw_complex.mae'.format(self.name)
        self.prepped_complex = '{}_prepped_complex.mae'.format(self.name)
        self.prep_wizard_cmd = '$SCHRODINGER/utilities/prepwizard -WAIT -rehtreat -watdist 0 {} {}\n'.format(self.raw_complex, self.prepped_complex)

        self.align_cmd = '$SCHRODINGER/utilities/structalign \
                      -asl        "(not chain. L and not atom.element H) \
                                and (fillres within 15.0 chain. L)" \
                      -asl_mobile "(not chain. L and not atom.element H) \
                                and (fillres within 15.0 chain. L)" \
                      {} {}.mae\n'

        self.align_file = '{}_prepped_aligned_complex.mae'.format(self.name)
        self.split_ligand = '{}_prepped_aligned_ligand.mae'.format(self.name)
        self.split_protein = '{}_prepped_aligned_protein.mae'.format(self.name)

        self.grid_in = 'grid.in'
        self.grid_file = '{}_grid.zip'.format(self.name)
        self.grid_cmd = '$SCHRODINGER/glide -WAIT {}\n'

    def get_folder(self):
        return self.folder

    def save_merged_ligand_protein(self, raw_protein_file, raw_ligand_file):
        """
        Merge structures from files and save to save directory
        :param raw_ligand_file: absolute paths
        :return:
        """
        prot_st = next(StructureReader(raw_protein_file))
        alpha = 'ABCDEFGHIJKMNOPQRST'
        alpha_count = 0
        for c in prot_st.chain:
            if c.name.strip() == '': continue
            c.name = alpha[alpha_count]
            alpha_count += 1

        if raw_ligand_file != '':
            lig_st = next(StructureReader(raw_ligand_file))
            # standardize chain naming
            for c in lig_st.chain:
                c.name = 'L'
            merged_st = lig_st.merge(prot_st)
        else:
            merged_st = prot_st

        st_wr = StructureWriter(self.path+self.raw_complex)
        st_wr.append(merged_st)
        st_wr.close()

    def done_merge(self):
        return os.path.isfile(self.path+self.raw_complex) 

    def get_prep_wizard_cmd(self):
        return self.prep_wizard_cmd

    def done_prepwizard(self):
        return os.path.isfile(self.path+self.prepped_complex) 

    def add_template_complex(self, filename):
        self.template_complex = filename

    def get_alignment_cmd(self):
        return self.align_cmd.format(self.template_complex, self.prepped_complex)

    def done_align(self): 
        return False

    def split(self):
        #look for the opt_complex, if it doesn't exist, just use the prepped complex 
        
        usefile = ''
        if (os.path.isfile(self.path+self.align_file)):
            usefile = self.path+self.align_file
        else:
            usefile = self.path+self.prepped_complex

        st = next(StructureReader(usefile))
        prot_st = st.extract([a.index for a in st.atom if a.chain != 'L'])
        prot_st.title = '{}_prot'.format(self.name)

        lig_st = st.extract([a.index for a in st.atom if a.chain == 'L'])
        lig_st.title = '{}_lig'.format(self.name)

        prot_wr = StructureWriter(self.path+self.split_protein)
        prot_wr.append(prot_st)
        prot_wr.close()

        lig_wr = StructureWriter(self.path+self.split_ligand)
        lig_wr.append(lig_st)
        lig_wr.close()

    def done_split_prepped(self):
        return os.path.isfile(self.path+self.split_protein) and os.path.isfile(self.folder+'/'+self.split_ligand)

    def write_grid_in_file(self, mode, grid_ligand='', xyz=False):
        if mode == 'other_ligand':
            st_2 = next(StructureReader(grid_ligand))
            c2 = get_centroid(st_2)
            x, y, z = c2[:3]
        elif mode == 'xyz':
            x, y, z = xyz
        else:
            st_2 = next(StructureReader(self.path+self.split_ligand))
            c2 = get_centroid(st_2)
            x,y,z = c2[:3]

        with open(self.path+self.grid_in, 'w') as f:
            f.write('GRID_CENTER {},{},{}\n'.format(x,y,z))
            f.write('GRIDFILE {}\n'.format(self.grid_file))
            f.write('INNERBOX 15,15,15\n')
            f.write('OUTERBOX 30,30,30\n')
            f.write('RECEP_FILE {}\n'.format(self.split_protein))

    def get_grid_cmd(self):
        return self.grid_cmd.format(self.grid_in)

    def done_grid(self): 
        return os.path.isfile(self.path+self.grid_file)



