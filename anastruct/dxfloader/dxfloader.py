import os
import ezdxf
import numpy as np

element_commands = ['add_element', 'add_multiple_elements', 'add_truss_element']
point_commands = ['add_support', 'point_load', 'moment_load']


class DxfLoader:
    def __init__(self):
        self.dxf_file_path = None
        self.dwg = None
        self.system = None
        self.dxf_lines = []
        self.dxf_texts_element_command = []
        self.dxf_texts_point_command = []

    def load_dxf_data_to_system(self, dxf_file_path, system):
        """
        Entry point for singleton object.
        :param dxf_file_path: (str) Path to dxf files.
        :param system: (SystemElements) object.
        """
        self.system = system
        if os.path.isfile(dxf_file_path):
            self._open_dxf(dxf_file_path)
            self._import_dxf_content()
            self._execute_command_from_dxf()
        else:
            raise FileNotFoundError('File {} not found'.format(dxf_file_path))
        self.system = None

    def _open_dxf(self, dxf_file_path):
        self.dxf_file_path = dxf_file_path
        self.dwg = ezdxf.readfile(self.dxf_file_path)

    def _import_dxf_content(self):
        self.dxf_lines = []
        self.dxf_texts_element_command = []
        self.dxf_texts_point_command = []
        for e in self.dwg.modelspace():
            if e.dxftype() == 'LINE':
                self.dxf_lines.append(e)
            elif e.dxftype() == 'TEXT':
                if any([i in e.dxf.text for i in element_commands]):
                    self.dxf_texts_element_command.append(e)
                elif any([i in e.dxf.text for i in point_commands]):
                    self.dxf_texts_point_command.append(e)

    def _execute_command_from_dxf(self):
        """
        Dynamically executes commands from dxf file.
        """
        # Add element to the system
        for line in self.dxf_lines:
            p1 = np.array(line.dxf.start[:2]).round(5)
            p2 = np.array(line.dxf.end[:2]).round(5)
            dxf_command_text = self._get_nearest_text_to_line(p1, p2)

            coordinates = [p1.tolist(), p2.tolist()]
            if dxf_command_text:
                command = 'self.system.' + dxf_command_text.replace('(', '(location={},'.format(coordinates))
                exec(command)
            else:
                self.system.add_element(coordinates)
        # Add point loads and supports
        for p in set([p for line in self.dxf_lines for p in [line.dxf.start[:2], line.dxf.end[:2]]]):
            p = np.array(p).round(5)
            dxf_command_text = self._get_nearest_text_to_point(p)
            if dxf_command_text:
                node_id = self.system.find_node_id(p)
                command = 'self.system.' + dxf_command_text.replace('(', '(node_id={},'.format(node_id))
                exec(command)

    def _get_nearest_text_to_line(self, p1, p2):
        """
        Get text commands from dxf file. Example: 'add_element(steelsection='IPE 300')
'
        :param p1: (array) 2d vector
        :param p2: (array) 2d vector
        :return: (str) Executable text command.
        """
        if not self.dxf_texts_element_command:
            return None

        # Find minimal perpendicular distance to line
        distances = np.empty(len(self.dxf_texts_element_command))
        for i, txt in enumerate(self.dxf_texts_element_command):
            p = np.array(txt.dxf.insert[:2])
            distances[i] = np.linalg.norm(np.cross(p2 - p1, p1 - p)) / np.linalg.norm(p2 - p1)

        t_entity = self.dxf_texts_element_command[np.argmin(distances)]  # the closest text entity

        # if the text is closer than it 2 * height it is the one we are looking for
        if np.min(distances) < t_entity.dxf.height * 2:
            return t_entity.dxf.text
        return None

    def _get_nearest_text_to_point(self, p):
        """
        Get text commands from dxf file. Example: 'point_load( Fy=-10000)'
'
        :param p: (array) 2d vector
        :return: (str) Executable text command.
        """
        if not self.dxf_texts_point_command:
            return None
        distances = np.empty(len(self.dxf_texts_point_command))
        for i, txt in enumerate(self.dxf_texts_point_command):
            p_t = np.array(txt.dxf.insert[:2])
            distances[i] = np.linalg.norm(p - p_t)

        t_entity = self.dxf_texts_point_command[np.argmin(distances)]  # the closest text entity

        # if the text is closer than it 2 * height it is the one we are looking for
        if np.min(distances) < t_entity.dxf.height * 2:
            return t_entity.dxf.text
        return None


dxf_loader = DxfLoader()
