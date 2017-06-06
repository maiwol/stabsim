import sys
import numpy as np
import json
import itertools as it
import schedule_functions as sched_fun


# total number of physical qubits
n_total = 17

d5_stabs = [
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
log_bin = sched_fun.convert_to_binary(logical_oper)

# Errors
errors_0 = [[]]
errors_1 = [[i] for i in range(n_total)]
errors_2 = []
for i in range(n_total):
    for j in range(i+1, n_total):
        errors_2 += [[i,j]]

total_errors = errors_0 + errors_1 + errors_2
        
# Basic lookuptable is the basis of every dictionary.
# It includes the trivial syndrome and all 1-q errors.
basic_lookup = {}
for err in errors_0 + errors_1:
    err_bin = sched_fun.convert_to_binary(err, n_total)
    syn = tuple(sched_fun.error_to_syndrome(err_bin, n_total, d5_stabs[:]))
    basic_lookup[syn] = err_bin




def basic_dict1(sched, flags=[1,3], n_total=17, stabs=d5_stabs[:]):
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

    dict1 = dict(basic_lookup)
    for i in range(flags[0], flags[1]+1):
        hook = sched[i : ]
        hook_bin = sched_fun.convert_to_binary(hook, n_total)
        for err in errors_0 + errors_1:
            err_bin = sched_fun.convert_to_binary(err, n_total)
            comb_err = sched_fun.multiply_operators(hook_bin, err_bin)
            syn = tuple(sched_fun.error_to_syndrome(comb_err, n_total, stabs[:]))
            if syn not in dict1:
                dict1[syn] = comb_err
            else:
                after_corr, num_corr = sched_fun.correct_until_in_codespace(comb_err,
                                                                            dict1,
                                                                            n_total,
                                                                            stabs[:])
                log_parity = sched_fun.overlapping_parity(after_corr, tuple(log_bin))
                if log_parity == 1:
                    return False, {}
    
    return True, dict1



def basic_dict2(sched1, flags1, sched2, flags2, n_total=17, stabs=d5_stabs[:]):
    '''
    '''

    # (no hook)1 (no hook)2
    dict2 = {tuple([0 for i in range(len(stabs))]): tuple([0 for i in range(n_total)])}

    # (no hook)1 (hook)2  and  (hook)1 (no hook)2
    for combo in [[sched1, flags1], [sched2, flags2]]:
        flags = combo[1]
        for i in range(flags[0], flags[1]+1):
            hook = combo[0][i : ]
            hook_bin = sched_fun.convert_to_binary(hook, n_total)
            syn = tuple(sched_fun.error_to_syndrome(hook_bin, n_total, stabs[:]))
            if syn not in dict2:
                dict2[syn] = hook_bin
            else:
                after_corr, num_corr = sched_fun.correct_until_in_codespace(hook_bin,
                                                                            dict2,
                                                                            n_total,
                                                                            stabs[:])
                log_parity = sched_fun.overlapping_parity(after_corr, tuple(log_bin))
                if log_parity == 1:
                    return False, {}
    
    # (hook)1 (hook)2
    for i in range(flags1[0], flags1[1]+1):
        hook1 = sched1[i : ]
        hook1_bin = sched_fun.convert_to_binary(hook1, n_total)
        for j in range(flags2[0], flags2[1]+1):
            hook2 = sched2[j : ]
            hook2_bin = sched_fun.convert_to_binary(hook2, n_total)
            comb_err = sched_fun.multiply_operators(hook1_bin, hook2_bin)
            syn = tuple(sched_fun.error_to_syndrome(comb_err, n_total, stabs[:]))
            if syn not in dict2:
                dict2[syn] = comb_err
            else:
                after_corr, num_corr = sched_fun.correct_until_in_codespace(comb_err,
                                                                            dict2,
                                                                            n_total,
                                                                            stabs[:])
                log_parity = sched_fun.overlapping_parity(after_corr, tuple(log_bin))
                if log_parity == 1:
                    return False, {}

    return True, dict2



def dict2_for_every_sched(good_scheds, flags_good, schedn, flagn, 
                          n_total=17, stabs=d5_stabs[:]):
    '''
    good_scheds is a list of schedules that are already confirmed to be good.
    They are schedules for n stabilizers.
    flags_good is the list of the corresponding flags (the flags for those n
    stabilizers).
    schedn is a possible schedule for the n stabilizer.  
    flagn i the flags for that stabilizer.
    
    Output:  if schedn is good, then:  True
             else:                     False
    '''

    for i in len(good_scheds):
        exists2, dict2 = basic_dict2(good_scheds[i][:], flags_good[i][:],
                                     schedn[:], flagn[:],
                                     n_total, stabs)
        if not exists2:
            return False

    return True



def add_next_sched(list_good_scheds, flags_good, stabn, flagn,
                   n_total=17, stabs=d5_stabs[:]):
    '''
    list_good_scheds is a list of all the good schedules found so far:
    [[sched1, sched2, ...], [sched1, sched2, ...], ...]
    '''

    for schedn in it.permutations(stabn):
        schedn = list(schedn)
        
        # First compute dict1 for the new schedule
        exists1, dict1 = basic_dict1(schedn[:], flagsn[:], n_total, stabs)
        if exists1:
            # if dict1 exists, then check that there's a dict2 between the
            # new schedule and every schedule in the list of good schedules
            for good_scheds in list_good_scheds:
                exists2 = dict2_for_every_sched(good_scheds[:], flags_good[:],
                                                schedn[:], flagn[:],
                                                n_total, stabs)
    
                if exists2:
                    new_good_scheds += [good_scheds + schedn] 

    return new_good_scheds


#infile_name = 'schedules_octagon.json'
#infile = open(infile_name, 'r')
#good_schedules = json.load(infile).values()
#infile.close()

n_good = 0
sched_dict = {}
for perm in it.permutations(d5_stabs[0]):
    perm = list(perm)
    exists, dict1 = basic_dict1(perm, [2,7])
    if exists:
        sched_dict[n_good] = perm
        n_good += 1

#outfile_name = 'schedules_octagon2.json'
#outfile = open(outfile_name, 'w')
#json.dump(sched_dict, outfile, indent=4, separators=(',', ':'),
#          sort_keys=True)
#outfile.close()


print n_good
