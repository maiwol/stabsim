import itertools as it



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



def error_to_syndrome(bin_err, n_total):
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



def correct_until_in_codespace(err, lookuptable, num_corr=0, flag_octagon=0):
    '''
    recursively corrects the err until the 
    resulting operators commutes with every
    stabilizer (no correction)
    '''

    syn = tuple(error_to_syndrome(err, flag_octagon))
    corr = lookuptable[syn]
    # if we don't have to correct
    if 1 not in corr:
        return err, num_corr
    else:
        new_err = multiply_operators(err,corr)
        return correct_until_in_codespace(new_err, lookuptable, num_corr+1)

