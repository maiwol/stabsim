import sys
import numpy as np
import itertools as it


# total number of physical qubits
n_total = 17

stabs = [
            [0,1,2,3],
            [0,2,4,5],
            [4,5,8,9],
            [8,9,12,13],
            [2,3,5,6,9,10,13,14],
            [6,7,10,11],
            [10,11,14,15],
            [7,11,15,16]
        ]

logical_oper = range(n_total)


def convert_to_binary(stab, n_total=17):
    '''
    converts a stabilizer from human readable [1,2,3,4] to
    a binary list
    '''

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



def error_to_syndrome(bin_err):
    '''
    assumes err is in binary form
    '''

    syndrome = []
    for stab in stabs:
        bin_stab = convert_to_binary(stab)
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



def correct_until_in_codespace(err, lookuptable, num_corr=0):
    '''
    recursively corrects the err until the 
    resulting operators commutes with every
    stabilizer (no correction)
    '''

    syn = tuple(error_to_syndrome(err))
    corr = lookuptable[syn]
    # if we don't have to correct
    if 1 not in corr:
        return err, num_corr
    else:
        new_err = multiply_operators(err,corr)
        return correct_until_in_codespace(new_err, lookuptable, num_corr+1)




# Errors
errors_0 = [[]]
errors_1 = [[i] for i in range(n_total)]
errors_2 = []
for i in range(n_total):
    for j in range(i+1, n_total):
        errors_2 += [[i,j]]

total_errors = errors_0 + errors_1 + errors_2


##################################################### 
# Extra errors (hooks)

# hooks from 2 errors propagating from the octagon
#total_errors += [
#                    [2,14,3,13],
#                    [2,14,6,9],
#                    [2,14,5,10]
#                ]

# hooks from 1 error from the octagon and a single error somewhere else
#total_errors += [[2,14,i] for i in range(n_total) if (i!=2 and i!=14)]
#total_errors += [[3,13,i] for i in range(n_total) if (i!=3 and i!=13)]
#total_errors += [[6,9,i] for i in range(n_total) if (i!=6 and i!=9)]
#total_errors += [[5,10,i] for i in range(n_total) if (i!=5 and i!=10)]

##################################################### 


# Error to syndrome dictionary
error_to_syn_dict = {}
for err in total_errors:
    bin_err = tuple(convert_to_binary(err))
    error_to_syn_dict[bin_err] = tuple(error_to_syndrome(bin_err))



# Syndrome to number of errors dictionary
syn_to_num_errs_dict = {}
for err in error_to_syn_dict:
    syn = error_to_syn_dict[err]
    if syn not in syn_to_num_errs_dict:
        syn_to_num_errs_dict[syn] = 1
    else:
        syn_to_num_errs_dict[syn] += 1



# Syndrome to error dictionary
lookuptable = {}
for err in error_to_syn_dict:
    syn = error_to_syn_dict[err]
    if syn not in lookuptable:
        lookuptable[syn] = err


# Make sure all errors are correctable
for err in total_errors:
    bin_err = tuple(convert_to_binary(err))
    # correct recursively until we go back to the codespace
    after_corr, num_corr = correct_until_in_codespace(bin_err, lookuptable, 0)
    # check to see if resulting operator commutes with logical operator
    log_parity = overlapping_parity(after_corr, tuple(convert_to_binary(logical_oper)))
    #print err, log_parity, num_corr, lookuptable[error_to_syn_dict[bin_err]]


# All possible weight-3 error configurations on the octagon
#octagon = stabs[4]
#w3_errors = []
#for i in range(8):
#    for j in range(i+1,8):
#        for k in range(j+1,8):
#            w3_errors += [[octagon[i], octagon[j], octagon[k]]]
#for i in range(8):
#    for j in range(i+1,8):
#        for k in range(n_total):
#            if (k!=octagon[i] and k!=octagon[j]):
#                w3_errors += [[octagon[i], octagon[j], k]]


#new_lookuptable = {}
#for syn in lookuptable:
#    new_lookuptable[syn] = lookuptable[syn]
#for err in w3_errors:
#    bin_err = convert_to_binary(err)
#    syn = tuple(error_to_syndrome(bin_err))
#    if syn not in new_lookuptable:
#        new_lookuptable[syn] = bin_err

    
# See which w-3 errors on octagon are correctable
#for err in w3_errors:
#    bin_err = tuple(convert_to_binary(err))
    # correct recursively until we go back to the codespace
#    after_corr, num_corr = correct_until_in_codespace(bin_err, new_lookuptable, 0)
    # check to see if resulting operator commutes with logical operator
#    log_parity = overlapping_parity(after_corr, tuple(convert_to_binary(logical_oper)))
    #if log_parity == 1:
        #print err, log_parity, num_corr, new_lookuptable[tuple(error_to_syndrome(bin_err))]


# Which w-3 and w-4 errors on the octagon are correctable?
#w3_errors_octagon = []
#w4_errors_octagon = []
#for i in range(8):
#    for j in range(i+1,8):
#        for k in range(j+1,8):
#            w3_errors_octagon += [[octagon[i],octagon[j],octagon[k]]]
#            for l in range(k+1,8):
#                w4_errors_octagon += [[octagon[i],octagon[j],octagon[k],octagon[l]]]


#new_lookuptable = {}
#for syn in lookuptable:
#    new_lookuptable[syn] = lookuptable[syn]
#for err in w3_errors_octagon + w4_errors_octagon:
#    bin_err = convert_to_binary(err)
#    syn = tuple(error_to_syndrome(bin_err))
#    if syn not in new_lookuptable:
#        new_lookuptable[syn] = bin_err


#for err in w3_errors_octagon + w4_errors_octagon:
#    bin_err = tuple(convert_to_binary(err))
    # correct recursively until we go back to the codespace
#    after_corr, num_corr = correct_until_in_codespace(bin_err, new_lookuptable, 0)
    # check to see if resulting operator commutes with logical operator
#    log_parity = overlapping_parity(after_corr, tuple(convert_to_binary(logical_oper)))
#    if log_parity == 0:
#        print err, log_parity, num_corr, new_lookuptable[tuple(error_to_syndrome(bin_err))]


# Figuring out the valid schedules for the octagon with an 8-qubit cat state verified once
tricky_errors = [
                    [1,2,3],
                    [1,2,3,4],
                    [0,6,7],
                    [2,3,4],
                    [2,3,4,5],
                    [0,1,7],
                    [3,4,5],
                    [3,4,5,6],
                    [4,5,6]
                ]
tricky_meas_errors = [
                        [0,1,2],
                        [0,1,2,3],
                        [5,6,7]
                     ]
tricky_total_errors = tricky_errors + tricky_meas_errors

good_schedules = []
index = 0
octagon = stabs[4][:]
for sched in it.permutations(octagon):
    index += 1
    sched = list(sched)
    new_lookuptable = dict(lookuptable)
    log_parity = 0
    for err in tricky_total_errors:
        new_err = [sched[q] for q in err]
        bin_err = convert_to_binary(new_err)
        syn = tuple(error_to_syndrome(bin_err))
        if syn not in new_lookuptable:
            new_lookuptable[syn] = bin_err
        else:
            after_corr, num_corr = correct_until_in_codespace(bin_err, new_lookuptable, 0)
            log_parity = overlapping_parity(after_corr, tuple(convert_to_binary(logical_oper)))
            if log_parity == 1:
                break
    if log_parity == 0:
        good_schedules += [sched]


