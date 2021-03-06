import sys
import numpy as np
import itertools as it



def convert_to_binary(stab, n_total=17):
    '''
    converts a stabilizer from human readable [1,2,3,4] to
    a binary list
    '''
    #print stab

    bin_list = [0 for i in range(n_total)]
    for index in stab:
        bin_list[index] = 1

    return bin_list



def overlapping_parity(oper1, oper2):
    '''
    computes the parity of the overlapping
    between two operators
    assumes operators are already in binary
    form.
    '''

    oper1 = np.array(oper1)
    oper2 = np.array(oper2)

    freq_overlap = np.sum((oper1+oper2)==2)

    return freq_overlap%2


################################################################
#
# old version of error_to_syndrome, which included
# flag as an "extra stabilizer".  Now, we're taking
# a different approach.  Every flag event has its 
# own lookuptable.

#def error_to_syndrome(bin_err, flag_octagon=0):
#    '''
#    assumes err is in binary form
#    '''

#    syndrome = []
#    for stab in stabs:
#        bin_stab = convert_to_binary(stab)
#        syndrome += [overlapping_parity(bin_err, bin_stab)]

#    syndrome += [flag_octagon]

#    return syndrome
#
################################################################



def error_to_syndrome(bin_err, n_total, stabs):
    '''
    assumes err is in binary form
    '''

    syndrome = []
    for stab in stabs:
        bin_stab = convert_to_binary(stab, n_total)
        syndrome += [overlapping_parity(bin_err, bin_stab)]

    return syndrome



def multiply_operators(oper0, oper1):
    '''
    multiplies two operators
    assumes operators are already in 
    binary form.
    '''
    
    product = []
    for i in range(len(oper0)):
        if oper0[i] == oper1[i]:
            product += [0]
        else:
            product += [1]

    return tuple(product)



def correct_until_in_codespace(err, lookuptable, n_total, stabs, num_corr=0):
    '''
    recursively corrects the err until the 
    resulting operators commutes with every
    stabilizer (no correction)
    '''

    syn = tuple(error_to_syndrome(err, n_total, stabs))
    # if we don't have to correct
    if 1 not in syn:
        return err, num_corr
    else:
        corr = lookuptable[syn]
        new_err = multiply_operators(err,corr)
        return correct_until_in_codespace(new_err, lookuptable, n_total, 
                                          stabs, num_corr+1)



def can_correct(err, lookup_dict, n_total, stabs):
    '''
    err:  error configuration (already in binary)
    lookup_dict:  the lookup table we have
    n_total: total number of qubits
    stabs:  the stabilizers

    returns a tuple: (1) whether the corresponding
                         syndrome was in the dict
                     (2) if it was, does the corrected
                         operator commute with the 
                         logical operator.

    '''
    log_bin = convert_to_binary(range(n_total), n_total)
    syn = tuple(error_to_syndrome(err[:], n_total, stabs[:]))
    if syn not in lookup_dict.keys():  
        return False, None, syn
    
    after_corr, num_corr = correct_until_in_codespace(err[:],
                                                      lookup_dict,
                                                      n_total,
                                                      stabs[:])
    log_parity = overlapping_parity(after_corr, tuple(log_bin))
    
    return True, log_parity, syn



def total_trig_comb_w(trig_comb):
    '''
    A flag combination is of the form ((0,1),0,1)
    The first element corresponds to the octagon,
    which will have two flags: (0,1) means that
    the first octagon flag did not get triggered,
    but the second one did.
    The second element means that the flag for the
    first square stabilizer did not get triggered
    and so on.
    Since for overlapping flag a single error can
    trigger both, then (1,1) counts as weight 1.
    '''

    w = 0
    for trig in trig_comb:
        if type(trig) == type((0,)):
            if trig.count(1) > 0:
                w += 1
        else:
            w += trig

    return w



def add_flags_to_sched(sched_bare, flags=[[1,3]]):
    '''
    adds the flags to a bare schedule and returns
    the schedule with flags
    '''
    sched_flags = sched_bare[:]
    for i in range(len(flags)):
        flag_name = 'f' + str(i+1)
        meas_name = 'm' + str(i+1)
        flag_qs = [sched_bare[j] for j in flags[i]]
        for q in flag_qs:
            anc_index = sched_flags.index(q)
            if type(sched_flags[anc_index-1]) == type(''):
                anc_index -= 1
            sched_flags.insert(anc_index, flag_name)
        sched_flags += [meas_name]

    return sched_flags



def complete_lookup(lookup, n_qubits, stabs, initial_w=1):
    '''
    Takes in an incomplete lookup table and loops over all w-1, w-2, w-3, ...
    data errors until it fills in all the syndromes.
    '''

    n_syndromes = 2**(len(stabs))
    
    current_w = initial_w
    # loop iteratively until all syndromes are covered
    while len(lookup) < n_syndromes:

        print 'current weight =', current_w
        #print len(lookup)
        #current_errors = lookup.values()[:]

        # Since we are not considering hook errors for surface-49,
        # we always start from the no-error configuration.
        current_errors = [[0 for i in range(n_qubits)]]
        data_errors = errors_n(n_qubits, current_w)
        print len(data_errors)

        for data_err in data_errors:
            #print data_err
            data_err_bin = convert_to_binary(data_err, n_qubits)
            #print data_err_bin
            for err in current_errors:
                comb_err = multiply_operators(data_err_bin[:], err[:])
                #print comb_err
                in_dict, log_par, syn = can_correct(comb_err[:],
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



def errors_n(n_qubits, weight):
    '''
    returns a list of all errors of weight "weight".
    '''
    errors_n = []
    for comb in it.combinations(range(n_qubits), weight):
        errors_n += [list(comb)]

    return errors_n

