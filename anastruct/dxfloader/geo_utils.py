import copy
from math import sqrt, sin, cos, atan, pi

"""
Code is extracted from DxfStructure project.
"""

checktolerance = 0.001

class Point():
    def __init__(self, xylist=[1.0, 2.0]):
        self.x = float(xylist[0])
        self.y = float(xylist[1])
    
    def distance(self, some_point):
        dist = sqrt((self.x - some_point.x)**2+(self.y - some_point.y)**2)
        return dist

