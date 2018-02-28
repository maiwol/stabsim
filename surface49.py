'''
surface49.py
'''

import sys
import os
import json
from circuit import *
import correction



class Code:
    '''
    Defines constants and methods useful for dealing with the Surface-49 code.
    '''

    code_name = 'Surface49'

    stabilizers = [
                    [('X',1), ('X',2)],
                    [('X',3), ('X',4)],
                    [('X',0), ('X',1), ('X',5), ('X',6)],
                    [('X',2), ('X',3), ('X',7), ('X',8)],
                    [('X',6), ('X',7), ('X',11), ('X',12)],
                    [('X',8), ('X',9), ('X',13), ('X',14)],
                    [('X',10), ('X',11), ('X',15), ('X',16)],
                    [('X',12), ('X',13), ('X',17), ('X',18)],
                    [('X',16), ('X',17), ('X',21), ('X',22)],
                    [('X',18), ('X',19), ('X',23), ('X',24)],
                    [('X',20), ('X',21)],
                    [('X',22), ('X',23)],
                    [('Z',0), ('Z',5)],
                    [('Z',1), ('Z',6), ('Z',2), ('Z',7)],
                    [('Z',3), ('Z',8), ('Z',4), ('Z',9)],
                    [('Z',5), ('Z',10), ('Z',6), ('Z',11)],
                    [('Z',7), ('Z',12), ('Z',8), ('Z',13)],
                    [('Z',9), ('Z',14)],
                    [('Z',10), ('Z',15)],
                    [('Z',11), ('Z',16), ('Z',12), ('Z',17)],
                    [('Z',13), ('Z',18), ('Z',14), ('Z',19)],
                    [('Z',15), ('Z',20), ('Z',16), ('Z',21)],
                    [('Z',17), ('Z',22), ('Z',18), ('Z',23)],
                    [('Z',19), ('Z',24)]]


    logical_opers = {'X': [('X',0), ('X',5), ('X',10), ('X',15), ('X',20)],
                     'Z': [('Z',0), ('Z',1), ('Z',2), ('Z',3), ('Z',4)],
                     'Y': [('Y',0), ('Z',1), ('Z',2), ('Z',3), ('Z',4),
                           ('X',5), ('X',10), ('X',15), ('X',20)]
                    }


    # The complete lookup table is imported from the json file.
    # The json file was generated with the script 'complete_lookups_surface49.py'.
    # The idea is to add all the errors in the basic lookup table
    # until we have obtained the 2**12 = 4096 possible syndromes. 
    # Just like for surface17, we have 2 lookup tables, one for the X stabilizers
    # and another one for the Z stabilizers

    lookup_folder = './lookup_tables_surface49/'
    lookuptable = {}
    stab_kinds = ['X','Z']
    for stab_kind in stab_kinds:
        json_filename = 'lookup_stabs%s.json'%stab_kind
        abs_filename = lookup_folder + json_filename
        json_file = open(abs_filename, 'r')
        local_table = json.load(json_file)
        json_file.close()
        lookuptable['%sstabs'%stab_kind] = local_table


