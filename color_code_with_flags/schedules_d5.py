import sys
import numpy as np
import json
import itertools as it
import schedule_functions as sched_fun


# total number of physical qubits
n_total = 17

stabs = [
          [2,3,6,5,10,9,13,14],
          [0,1,2,3],
          [0,2,4,5],
          [4,5,8,9],
          [8,9,12,13],
          [6,7,10,11],
          [10,11,14,15],
          [7,11,15,16]
        ]

logical_oper = range(n_total)

# Errors
errors_0 = [[]]
errors_1 = [[i] for i in range(n_total)]
errors_2 = []
for i in range(n_total):
    for j in range(i+1, n_total):
        errors_2 += [[i,j]]

total_errors = errors_0 + errors_1 + errors_2




def basic_dict1(sched, flags=[1,3]):
    '''
    computes the basic dictionary when the stabilizer given by
    sched triggers a flag.  Basic dictionary means that we don't
    try to complete all the 2^8 syndromes, just the ones necessary
    to correct for 1-q and 2-q error events.  
    
    The second argument, flags, gives the location of the two-qubit 
    gates from the ancilla qubit to the flag qubit.  
    For example, [1,3] means that the first CNOT occurs before the 
    second gate and the second CNOT occurs before the third gate.
    
    returns True, dict1  if it's possible to construct the dict
            False, {}    if it's not possible.
    '''

    for i in range(flags[0], flags[1]+2):
        hook = sched[i : flags[1]+1]
        hook_bin = convert_to_binary(hook, n_total)
        for err in errors_0 + errors1:
            err_bin = sched_fun.convert_to_binary(err, n_total)
            comb_err = sched_fun.multiply_operators(hook_bin, err_bin)

