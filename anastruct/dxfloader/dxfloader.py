import os
import logging
import ezdxf
from anastruct.dxfloader.geo_utils import Point, Line


def round_coordinate(point, dig=5):
    point[0] = round(point[0], dig)
    point[1] = round(point[1], dig)


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
        self.system = system
        if os.path.isfile(dxf_file_path):
            self._open_dxf(dxf_file_path)
            self._import_dxf_content()
            self._execute_command_from_dxf()
        else:
            logging.error('File %s does not exist!!' % dxf_file_path)
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
        # executing element commands
        for line in self.dxf_lines:
            line_start_point = list(line.dxf.start[:2])
            round_coordinate(line_start_point)
            line_end_point = list(line.dxf.end[:2])
            round_coordinate(line_end_point)
            # --
            dxf_command_text = self._get_nearest_text_to_line(Line(Point(line_start_point), Point(line_end_point)))
            if dxf_command_text:
                command = 'self.system.' + dxf_command_text.replace('(', '(location=' + str(
                    [line_start_point, line_end_point]) + ',')
                exec(command)
            else:
                self.system.add_element([line_start_point, line_end_point])
        # executing point commands
        for point in self._get_model_points():
            dxf_command_text = self._get_nearest_text_to_point(Point(point))
            if dxf_command_text:
                id = self.system.find_node_id(point)
                command = 'self.system.' + dxf_command_text.replace('(', '(node_id=' + str(id) + ',')
                exec(command)

    def _get_nearest_text_to_line(self, line):
        if not self.dxf_texts_element_command:
            return None
        tdists = []
        for txt in self.dxf_texts_element_command:
            dxfinsert = txt.dxf.insert
            textp = Point([dxfinsert[0], dxfinsert[1]])
            txtdist = line.distance(textp)
            tdists.append(txtdist)
        mintdist = min(tdists)
        mintdistindex = tdists.index(mintdist)
        t_entity = self.dxf_texts_element_command[mintdistindex]  # the closest text entity
        maxdist = 2.0 * t_entity.dxf.height

        # and if the text is closer than it 2xheight it is the one we looking for
        if mintdist < maxdist:
            return t_entity.dxf.text
        else:
            return None

    def _get_nearest_text_to_point(self, point):
        if not self.dxf_texts_point_command:
            return None
        tdists = []
        for txt in self.dxf_texts_point_command:
            dxfinsert = txt.dxf.insert
            textp = Point([dxfinsert[0], dxfinsert[1]])
            txtdist = point.distance(textp)
            tdists.append(txtdist)
        mintdist = min(tdists)
        mintdistindex = tdists.index(mintdist)
        t_entity = self.dxf_texts_point_command[mintdistindex]  # the closest text entity
        maxdist = 2.0 * t_entity.dxf.height

        # and if the text is closer than it 2xheight it is the one we looking for
        if mintdist < maxdist:
            return t_entity.dxf.text
        else:
            return None

    def _get_model_points(self):
        points = []
        for line in self.dxf_lines:
            line_start_point = list(line.dxf.start[:2])
            round_coordinate(line_start_point)
            line_end_point = list(line.dxf.end[:2])
            round_coordinate(line_end_point)
            for point in [line_start_point, line_end_point]:
                if point not in points:
                    points.append(point)
        return points


dxfloader = DxfLoader()
