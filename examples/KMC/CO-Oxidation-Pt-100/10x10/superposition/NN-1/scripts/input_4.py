#!/bin/env/python

from kynetix.utilities.coordinate_utilities import CoordsGroup

coords_indices = [
    # NN-1
    ([-1.5, 1.0, 0.0], 1), ([-1.0, 1.0, 0.0], 0), ([1.0, 1.0, 0], 0), ([1.5, 1.0, 0.0], 1),
    ([1.5, 0.0, 0.0], 1), ([1.0, 0.0, 0.0], 0), ([-1.0, 0.0, 0.0], 0), ([-1.5, 0.0, 0.0], 1),
]

rxn_expression = "CO_b + O_b <-> OC-O_2b -> CO2_g + 2*_b"

# Coordinates of origin.
ori_coords = [[0.0, 0.0, 0.0], [0.5, 0.0, 0.0], [0.0, 0.5, 0.0]]

# Get fixed coord_groups.
c = [[0.0, 0.0, 0.0],
     [-0.5, 0.5, 0.0],
     [0.0, 1.0, 0.0],  
     [0.5, 0.5, 0.0],  
     [0.0, 0.5, 0.0]]
e = ["V", "V", "V", "V", "O_s"]
O_s = CoordsGroup(c, e)

c = [[0.0, 0.0, 0.0],
     [-0.5, 0.5, 0.0],
     [0.0, 1.0, 0.0],  
     [0.5, 0.5, 0.0],  
     [0.0, 0.5, 0.0]]
e = ["V", "V", "V", "V", "V"]
free1 = CoordsGroup(c, e).move([1, 0, 0])
free2 = CoordsGroup(c, e).move([-1, 0, 0])

coord_groups = [[O_s, free1], [O_s, free2]]

