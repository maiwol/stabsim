import sys
import os
import json
from circuit import *
import correction


class Code:

    code_name = 'd5color'

    # The weight-8 stabilizer always comes first by convention
    stabilizer = [
    ['I', 'I', 'X', 'X', 'I', 'X', 'X', 'I', 'I', 'X', 'X', 'I', 'I', 'X', 'X', 'I', 'I'],
    ['X', 'X', 'X', 'X', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I'],
    ['X', 'I', 'X', 'I', 'X', 'X', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I'],
    ['I', 'I', 'I', 'I', 'X', 'X', 'I', 'I', 'X', 'X', 'I', 'I', 'I', 'I', 'I', 'I', 'I'],
    ['I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'X', 'X', 'I', 'I', 'X', 'X', 'I', 'I', 'I'],
    ['I', 'I', 'I', 'I', 'I', 'I', 'X', 'X', 'I', 'I', 'X', 'X', 'I', 'I', 'I', 'I', 'I'],
    ['I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'X', 'X', 'I', 'I', 'X', 'X', 'I'],
    ['I', 'I', 'I', 'I', 'I', 'I', 'I', 'X', 'I', 'I', 'I', 'X', 'I', 'I', 'I', 'X', 'X'],
    ['I', 'I', 'Z', 'Z', 'I', 'Z', 'Z', 'I', 'I', 'Z', 'Z', 'I', 'I', 'Z', 'Z', 'I', 'I'],
    ['Z', 'Z', 'Z', 'Z', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I'],
    ['Z', 'I', 'Z', 'I', 'Z', 'Z', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I'],
    ['I', 'I', 'I', 'I', 'Z', 'Z', 'I', 'I', 'Z', 'Z', 'I', 'I', 'I', 'I', 'I', 'I', 'I'],
    ['I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'Z', 'Z', 'I', 'I', 'Z', 'Z', 'I', 'I', 'I'],
    ['I', 'I', 'I', 'I', 'I', 'I', 'Z', 'Z', 'I', 'I', 'Z', 'Z', 'I', 'I', 'I', 'I', 'I'],
    ['I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'Z', 'Z', 'I', 'I', 'Z', 'Z', 'I'],
    ['I', 'I', 'I', 'I', 'I', 'I', 'I', 'Z', 'I', 'I', 'I', 'Z', 'I', 'I', 'I', 'Z', 'Z']
        ]


    # The lookup table is imported from the json file.
    table_json_filename = 'complete_lookup_table_d5.json'
    table_json = open(table_json_filename, 'r')
    lookuptable_str = json.load(table_json)
    table_json.close()


    stabilizer_CHP_X = [
                        '+XXXXIIIIIIIIIIIII'
                        '+IXIXXXIIIIIIIIIII',
                        '+IIXXXIIIIXIIIXIII',
                        '+IIIIXXIIXXIIIIIII',
                        '+IIIIIIXXIIXXIIIII',
                        '+IIIIIIIXXXIXIIXII',
                        '+IIIIIIIIXXIIXXIII',
                        '+IIIIIIIIIIXXIIXXI',
                        '+IIIIIIIIIIIIXXXXX',
                        '+ZZZZIIIIIIIIIIIII',
                        '+IZIZZZIIIIIIIIIII',
                        '+IIZZIZZIIZZIIZZII',
                        '+IIIIZZIIZZIIIIIII',
                        '+IIIIIIZZIIZZIIIII',
                        '+IIIIIIIZIIIZIIIZZ',
                        '+IIIIIIIIZZIIZZIII',
                        '+IIIIIIIIIIZZIIZZI'
                        ]

    destabilizer_CHP_X = [
                            '+IIZIIIIIIIIIZZIII',
                            '+IIZZIIZIZZZIZZIZZ',
                            '+IIIIIIIIIIIIZZIII',
                            '+IIIIIIIIZIIIZIZZZ',
                            '+IIIIIIIIIIIZIIZIZ',
                            '+IIIIIIIIIIIIIIZZI',
                            '+IIIIIIIIIIIIZIIIZ',
                            '+IIIIIIIIIIIIIIIZZ',
                            '+IIIIIIIIIIIIIIIIZ',
                            '+XIIIIIIIIIIIIIIII',
                            '+XXIIIIIIIIIIIIIII',
                            '+IIIIXXIIIIIIIIIII',
                            '+XXIIXIIIIIIIIIIII',
                            '+IXIXIIXIIIIIIIIII',
                            '+IXIXIIXXIIIIIIIII',
                            '+XIIXXIIIIXIIIIIII',
                            '+IIIIIIXIIIXIIIIII'
                          ]

