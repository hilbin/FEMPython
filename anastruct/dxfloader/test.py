import os
from anastruct.fem.system import SystemElements

DXF_FILE_PATH = os.path.join(os.path.dirname(__file__), 'data/test.dxf')

ss = SystemElements()

ss.load_dxf_data_to_system(DXF_FILE_PATH)
ss.show_structure(annotations=True)
