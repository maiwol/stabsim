import steane
import fivequbit



def update_stabs(stabs, destabs, operation):
    '''
    This function is used exclusively when operation only has
    X or Z.  This means that the only thing we change is the 
    sign of the stabilizers and destabilizers.  Notice that
    changing the sign of the destabilizers is unnecessary,
    because either way D_i would anticommute with S_i and 
    commute with D_j and S_j:
    If {A,B} = 0, then {A,-B} = 0
    If [A,B] = 0, then [A,-B] = 0
    For this reason, and to save us some time, I have
    commented it out.
    '''
    if len(stabs) != len(destabs):
        raise IndexError('Check out the stabs and destabs.')

    n = len(stabs)
    for i in range(n):
        stabs[i] = update_one_stab(stabs[i], operation)
        #destabs[i] = update_one_stab(destabs[i], operation)

    return stabs, destabs
    


def update_one_stab(state, operator):
    '''
    Assumes state has sign, but operator doesn't, i.e.,
    it's always positive.
    For example: 
       - state:      '+XIXIXIX'  (can have X, Y, or Z)
       - operator:    'ZIIIIII'  (can only have X or Z)
    '''
    state = list(state)
    operator = list(operator)
    par = 0
    for i in range(len(operator)):
        if str(operator[i]) == 'X':
            if str(state[i+1]) == 'Y' or str(state[i+1]) == 'Z':
                par += 1
        elif str(operator[i]) == 'Z':
            if str(state[i+1]) == 'X' or str(state[i+1]) == 'Y':
                par += 1
        elif str(operator[i]) == 'Y':
            if str(state[i+1]) == 'X' or str(state[i+1]) == 'Z':
                par += 1

    if par%2 == 1:
        if   state[0] == '+':   state[0] = '-'
        elif state[0] == '-':   state[0] = '+'

    return ''.join(state)



def update_errors_anc(current_errors, stab):
    '''
    not error on ancilla, but errors that propagated
    from ancilla to data (hook errors)
    In this new implementation we don't need the input
    error, which was present in the old one.
    This is not the most elegant solution, but it works.
    MGA 6/29/16.
    
    Notice that this only works for weight-4 stabilizers.
    '''
    #print 'stab =', stab
    l = len(stab)   # should be 7 for Steane and 5 for 5qubit
    qubits_indexes = [i for i in range(l) if stab[i]!='I']
    qubits_to_correct = qubits_indexes[:2]
    for q in qubits_to_correct:
        error = stab[q]
        if current_errors[q] == 'I':
            current_errors[q] = error

        elif current_errors[q] == 'X':
            if error == 'X':
                current_errors[q] = 'I'
            elif error == 'Y':
                current_errors[q] = 'Z'
            elif error == 'Z':
                current_errors[q] = 'Y'

        elif current_errors[q] == 'Y':
            if error == 'X':
                current_errors[q] = 'Z'
            elif error == 'Y':
                current_errors[q] = 'I'
            elif error == 'Z':
                current_errors[q] = 'X'

        elif current_errors[q] == 'Z':
            if error == 'X':
                current_errors[q] = 'Y'
            elif error == 'Y':
                current_errors[q] = 'X'
            elif error == 'Z':
                current_errors[q] = 'I'

    return current_errors



def stabs_QEC_diVin(dic, n_first_anc, code, stab_kind=None):
    '''
    After one round of either X or Z stabs (for a CSS code)
    or the whole set of stabs (for a non-CSS code),
    with an unverified cat state, we first correct the hook 
    errors (errors that propagated from ancilla to data),
    and then return the correction for the data errors.
    '''
    
    # so far only Steane and 5qubit codes
    
    extra_s = 0  # little hack to get the stabilizer right

    if code == 'Steane':
        n_q, s, w = 7, 3, 4
        code_class = steane.Code
        if type(stab_kind) != type(''):
            raise TypeError('stab_kind either X or Z.')
        if stab_kind == 'Z':
            extra_s = 3
            error = 'X'
        elif stab_kind == 'X':
            error = 'Z'


    elif code == '5qubit':
        n_q, s, w = 5, 4, 4
        code_class = fivequbit.Code


    # 1 Raise exception if dictionary is not right length 
    if len(dic) != s*w:
        raise IndexError('Dictionary does not have right length.')

    # 2 Assign data_corr and prop_corr
    prop_corr = ['I' for i in range(n_q)]
    data_error = []

    for i in range(s):
        outcomes = [dic[n_first_anc + i*w + j][0]
                                for j in range(w)]
        data_error += [outcomes.pop(1)]
        if 0 not in outcomes:
            stab = code_class.stabilizer[i + extra_s]
            prop_corr = update_errors_anc(prop_corr,
                                          stab)
    
    data_corr = code_class.stabilizer_syndrome_dict[tuple(data_error)]
    if code == 'Steane':
        data_corr = [i if i == 'I' else error for i in data_corr]   
    
    return data_corr, prop_corr


