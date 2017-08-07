'''
Script to generate the complete lookups for the surface-49 code: one for X and one for Z
'''

import sys
import os
import json
import itertools as it
import surface49 as surf49
import color_code_with_flags.schedule_functions as sched_fun


n_total = 25
n_stabs = 24
X_stabs = surf49.Code.stabilizers[:n_stabs/2]
Z_stabs = surf49.Code.stabilizers[n_stabs/2:]
X_stabs_num, Z_stabs_num = [], []
for i in range(n_stabs/2):
    X_stabs_num += [[oper[1] for oper in X_stabs[i]]]
    Z_stabs_num += [[oper[1] for oper in Z_stabs[i]]]

# Errors
errors_0 = [[]]

# Trivial lookuptable is the basis of every dictionary.
# It includes only the trivial syndrome.
trivial_lookup = {}
for err in errors_0:
    err_bin = sched_fun.convert_to_binary(err, n_total)
    syn = tuple(sched_fun.error_to_syndrome(err_bin, n_total, X_stabs_num))
    trivial_lookup[syn] = err_bin


lookup_Xstabs, wX = sched_fun.complete_lookup(dict(trivial_lookup), n_total, X_stabs_num)
lookup_Zstabs, wZ = sched_fun.complete_lookup(dict(trivial_lookup), n_total, Z_stabs_num)
#print wX
#print wZ
#print len(lookup_Xstabs)
#print len(lookup_Zstabs)

# Define and create output folder
output_folder = './lookup_tables_surface49/'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

stab_kinds = ['X','Z']
lookups = [lookup_Xstabs, lookup_Zstabs]
for i in range(2):
    json_filename = 'lookup_stabs%s.json'%stab_kinds[i]
    abs_filename = output_folder + json_filename
    json_file = open(abs_filename, 'w')
    converted_lookup = sched_fun.convert_keys_to_strings(lookups[i])
    json.dump(converted_lookup, json_file, indent=4, separators=(',', ':'), sort_keys=True)
    json_file.close()
