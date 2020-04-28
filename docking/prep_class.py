import os
import docking.utilities

class Prep_Protein_Set:
    def run_prep_wizard_set(self, prep_set_info, run_config):
        """
        Prep Step 1:
        Combine protein raw structure with ligand from raw structure
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
            single_prep.save_merged_ligand_protein(single_prep_info['raw_protein_file'],  single_prep_info['raw_ligand_file'])
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

    def run_split_prepped_set(self, prep_set_info):
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
            single_prep.save_merged()

    def run_build_grids(self, prep_set_info, run_config):
        """
        Prep Step 4:
        Write the grid using the final protein structure
        Output grid.zip

        :param prep_set_info:
        :param run_config:
        :return:
        """
        return False

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
                f.write('cd {}\n'.format(run_config['run_folder']))


from schrodinger.structure import StructureReader, StructureWriter

class Protein_Prep:
    """
    Object to Carry out low level preparation steps on a single ligand/protein structure
    """
    def __init__(self, folder, docking_name):
        self.folder = folder
        os.makedirs(self.folder, exist_ok=True)
        self.name = docking_name

        self.raw_complex = '{}_raw_complex'.format(self.name)
        self.prepped_complex = '{}_prepped_complex'.format(self.name)
        self.prep_wizard_cmd = '$SCHRODINGER/utilities/prepwizard -WAIT -rehtreat -watdist 0 {}.mae {}.mae\n'.format(self.raw_complex, self.prepped_complex)

        self.align_cmd = '$SCHRODINGER/utilities/structalign \
                      -asl        "(not chain. L and not atom.element H) \
                                and (fillres within 15.0 chain. L)" \
                      -asl_mobile "(not chain. L and not atom.element H) \
                                and (fillres within 15.0 chain. L)" \
                      {} {}.mae\n'

        self.align_file = ''
        self.split_ligand = 'prepped_aligned_ligand.mae'
        self.split_protein = 'prepped_aligned_protein.mae'

    def get_folder(self):
        return self.folder

    def save_merged_ligand_protein(self, raw_protein_file, raw_ligand_file):
        """
        Merge structures from files and save to save directory
        :param raw_ligand_file: absolute paths
        :return:
        """
        prot_st = next(StructureReader(raw_protein_file))
        lig_st = next(StructureReader(raw_ligand_file))
        #standardize chain naming
        for c in lig_st.chain:
            c.name = 'L'
        alpha = 'ABCDEFGHIJKMNOPQRST'
        alpha_count = 0
        for c in prot_st.chain:
            if c.name.strip() == '': continue

            c.name = alpha[alpha_count]
            alpha_count += 1

        merged_st = lig_st.merge(prot_st)

        st_wr = StructureWriter(self.raw_complex)
        st_wr.append(merged_st)
        st_wr.close()

    def get_prep_wizard_cmd(self):
        return self.prep_wizard_cmd

    def add_template_complex(self, filename):
        self.template_complex = filename

    def get_alignment_cmd(self):
        return self.align_cmd.format(self.template_complex, self.prepped_complex)

    def save_merged(self):
        st = next(StructureReader(opt_complex))
        prot_st = st.extract([a.index for a in st.atom if a.chain != 'L'])
        prot_st.title = '{}_prot'.format(pdb_id)

        prot_wr = StructureWriter(self.split_protein)
        prot_wr.append(prot_st)
        prot_wr.close()



