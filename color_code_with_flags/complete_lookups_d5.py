'''
Script to complete all the basic lookup tables until all the syndromes are covered.
'''

import sys
import os
import json
import itertools as it
import schedule_functions as sched_fun
import schedules_d5 as scheds_d5


n_total = 17
stabs = scheds_d5.d5_stabs_good[:]


errors_0 = scheds_d5.errors_0[:]
errors_1 = scheds_d5.errors_1[:]
errors_2 = scheds_d5.errors_2[:]

def errors_n(n_qubits, weight):
    '''
    returns a list of all errors of weight "weight".
    '''
    errors_n = []
    for comb in it.combinations(range(n_qubits), weight):
        errors_n += [list(comb)]
    
    return errors_n



def complete_lookup(lookup, n_qubits, stabs, initial_w=1):
    '''
    Takes in an incomplete lookup table and loops over all w-1, w-2, w-3, ...
    data errors until it fills in all the syndromes.
    '''

    n_syndromes = 2**(len(stabs))
    
    current_w = initial_w
    # loop iteratively until all syndromes are covered
    while len(lookup) < n_syndromes:

        print current_w
        print len(lookup)
        current_errors = lookup.values()[:]
        data_errors = errors_n(n_qubits, current_w)
                
        for data_err in data_errors:
            data_err_bin = sched_fun.convert_to_binary(data_err, n_qubits)
            for err in current_errors:
                comb_err = sched_fun.multiply_operators(data_err_bin[:], err[:])
                in_dict, log_par, syn = sched_fun.can_correct(comb_err[:],
                                                              lookup,
                                                              n_qubits,
                                                              stabs[:])
                if not in_dict:
                    lookup[syn] = comb_err
                    
        current_w += 1

    return lookup, current_w


def convert_keys_to_strings(lookup):
    '''
    Converts the keys of a lookup table from tuples to strings
    '''
    new_lookup = {}
    for key in lookup:
        new_key = ''.join(map(str,key))
        new_lookup[new_key] = lookup[key]

    return new_lookup



# Define and create output folder
output_folder = './lookup_tables_color_d5/'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Loop over all lookup tables
lookups = scheds_d5.lookups
for comb_trig in lookups:
    print comb_trig
    lookup = lookups[comb_trig]
    total_lookup, w = complete_lookup(lookup, n_total, stabs[:])
    converted_lookup = convert_keys_to_strings(total_lookup)
    comb_list = list(comb_trig[0]) + [comb_trig[i] for i in range(1,8)] 
    json_filename = ''.join(map(str,comb_list)) + '.json'
    abs_filename = output_folder + json_filename
    json_file = open(abs_filename, 'w')
    json.dump(converted_lookup, json_file, indent=4, separators=(',', ':'), sort_keys=True)
    json_file.close()
