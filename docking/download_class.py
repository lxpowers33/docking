from schrodinger.protein.getpdb import download_file
from schrodinger.structure import StructureReader
import sys

class Download_Set:

    def run_get_pdb_set(self, structure_set_info):
        '''
        Setup and start running a set of docking task
        structure_set_info: (list of dicts) 
            [{'folder', 'pdb'}]
        :return: (None)
        '''
        for structure in structure_set_info:
            download_file(structure['pdb'], structure['folder']+'/'+structure['pdb']+'.pdb')

    def extract_prot_lig(self, structure_set_info):
        '''
        Setup and start running a set of docking task
        structure_set_info: (list of dicts) 
            [{'folder', 'pdb', 'prot':['A','B'], 'lig':'L'}]
        :return: (None)

        for structure in structure_set_info:
            with StructureReader(input_pdb) as st:
                        st = list(st)[0]
            
        '''
        print(structure_set_info)
        for task in structure_set_info:
            base = task['folder']+'/'+task['name']
            if task['method'] == 'by_chain':
                #extract specific chains
                with StructureReader(base+'.pdb') as st:
                    st = list(st)[0]
                    st_prot = st.chain[task['P']].extractStructure(copy_props=True)
                    st_prot.write(base+'_prot.mae')

                    st_lig = st.chain[task['L']].extractStructure(copy_props=True)
                    st_lig.write(base+'_lig.mae')
            if task['method'] == 'by_res':
                #extract specific chains
                with StructureReader(base+'.pdb') as st:
                    st = list(st)[0]
                    lig = [a.index for a in st.atom if a.getResidue().pdbres == task['L']]
                    print(lig)
                    st_lig = st.extract(lig)
                    st_lig.write(base+'_lig.mae')

                    st_prot = st.extract([a.index for a in st.atom if a.getResidue().pdbres != task['L']])
                    st_prot.write(base+'_prot.mae')
            if task['method'] == 'from_PDBBind':
                print(task['method'])
                name_lower = task['name'].lower()
                with StructureReader(task['folder']+'/'+name_lower+'_protein.pdb') as st:
                    st = list(st)[0]
                    st.write(base+'_prot.mae')
                with StructureReader(task['folder']+'/'+name_lower+'_ligand.mol2') as st:
                    st = list(st)[0]
                    st.write(base+'_lig.mae')




        return False
        


