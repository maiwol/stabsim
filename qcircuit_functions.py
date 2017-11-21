import sys
import copy
import itertools as it
import circuit as c
import cross
import steane
import fivequbit
import surface17 as surf17
import surface49 as surf49
import d5color
import correction as cor
from visualizer import browser_vis as brow
import schedules_d5

QEC_lookuptable = schedules_d5.lookups




def initial_product_state(n_qubits, stab_kind='Z'):
    '''
    Returns the stabilizers and destabilizers corresponding to a product
    state |000...00> (Z) or |+++...++> (X).
    '''
    
    if stab_kind == 'Z':  destab_kind = 'X'
    elif stab_kind == 'X':  destab_kind = 'Z'
    prod_stabs, prod_destabs = [], []
    for i in range(n_qubits):
        prod_stab = [stab_kind if i==j else 'I' for j in range(n_qubits)]
        prod_stab.insert(0, '+')
        prod_destab = [destab_kind if i==j else 'I' for j in range(n_qubits)]
        prod_destab.insert(0, '+')
        prod_stabs += [''.join(prod_stab)]
        prod_destabs += [''.join(prod_destab)]
 
    return prod_stabs, prod_destabs



def combine_flags(flag_list):
    '''
    Takes in a list of flags (for several rounds of QEC) and adds them
    to return the total flags.  It returs a string to later be used as
    a key in the lookup table.      
    We assume that the first flag is always the octagon, so it has two digits.
    '''

    new_flag_list = []
    for flag_outcome in flag_list:
        new_flag_outcome = [flag_outcome[0][0], flag_outcome[0][1]]
        new_flag_outcome += flag_outcome[1:]
        new_flag_list += [new_flag_outcome]

    n_flags = len(new_flag_list[0])
    combined_flags = []
    for i in range(n_flags):
        combined_flag = 0
        for new_flag_outcome in new_flag_list:
            combined_flag += new_flag_outcome[i]
        combined_flag %= 2
        combined_flags += [combined_flag]

    combined_flags_string = ''.join(map(str,combined_flags))

    return combined_flags_string



def get_syn_with_flags(out_dict,
                       previous_flag_outcomes=((0,0),0,0,0,0,0,0,0),
                       n_flags=[1,1,1]):

    out_keys = out_dict.keys()[:]
    out_keys.sort()

    syn = []
    flag_outcomes = []
    stab_i = 0
    for flag in n_flags:
        stab_i_old = stab_i
        stab_key = out_keys[stab_i]
        syn += [out_dict[stab_key][0]]

        stab_i += 1
        stab_i += flag

        flag_keys = out_keys[stab_i_old+1:stab_i]
        flag_outcome = [out_dict[key][0] for key in flag_keys]
        if len(flag_outcome) == 1:
            flag_outcomes += [flag_outcome[0]]
        else:                   
            flag_outcomes += [tuple(flag_outcome)]

    flag_outcomes = tuple(flag_outcomes)
    syn = tuple(syn)
    corr = QEC_lookuptable[previous_flag_outcomes][syn]

    return corr, flag_outcomes



def add_errors_after_gates(circ, gates_indexes, errors_to_add=['XX'], print_circ=False):
    '''
    Inserts specific errors after specific gates.
    circ:  the circuit onto which we want to add the errors.
    gates_indexes:  the indexes of the gates after which we want to 
                    add the errors (a list).
    errors_to_add:  the errors to add (a list of same length)
    '''

    #print 'gates indexes =', gates_indexes
    if print_circ:
        brow.from_circuit(circ, True)

    # Instead of gates_indexes.sort(), we apply a conditional sorting.
    if gates_indexes[0] > gates_indexes[-1]:
        gate_indexes.reverse()
        errors_to_add.reverse()

    for j in gates_indexes[::-1]:
        g = circ.gates[j]
        i = gates_indexes.index(j)
        if len(errors_to_add[i]) == 1:
            new_g = circ.insert_gate(g, g.qubits, '', errors_to_add[i], False)
            new_g.is_error = True
        else:
            new_g = circ.insert_gate(g, [g.qubits[1]], '', errors_to_add[i][1], False)
            new_g.is_error = True
            new_g = circ.insert_gate(g, [g.qubits[0]], '', errors_to_add[i][0], False)
            new_g.is_error = True

    return



def get_total_indexes_one_circ(subset, one_q_gates, two_q_gates,
                               one_q_errors_type=['X'],
                               two_q_errors_type=['IX','XI','XX']):
    '''
    Returns the total list of indexes for all the error configurations
    in an error subset (n1, n2)
    subset:  for example, (1,1):  1 1-q error + 1 2-q error.
    one_q_gates:  the list of all the indexes corresponding to the 
                  locations of 1-q gates.
    two_q_gates:  the list of all the indexes corresponding to the
                  locations of 2-q gates.
    Currently, one_q_errors_type can only have 1 element, but it's
    easy to generalize.
    '''

    n_one_q_errors = subset[0]
    n_two_q_errors = subset[1]
    
    total_indexes, total_errors = [], []
    for comb1 in it.combinations(one_q_gates, n_one_q_errors):
        for comb2 in it.combinations(two_q_gates, n_two_q_errors):
            for two_err in it.product(two_q_errors_type, repeat=n_two_q_errors):
                local_indexes, local_errors = [], []
                for g_index in comb1:
                    local_indexes += [g_index]
                    local_errors += [one_q_errors_type[0]]
                for g_index in comb2:
                    local_indexes += [g_index]
                    local_errors += [two_err[comb2.index(g_index)]]

                total_indexes += [local_indexes]
                total_errors += [local_errors]

    return total_indexes, total_errors

    


def change_operators(stab_list):
    '''
    takes in a list of Pauli operators (either all X or all Z)
    and returns "the opposite".  The operators themselves are
    in a string.
    '''
    out_list = []
    for stab in stab_list:
        new_stab = ''
        for oper in stab:
            if oper == 'X':    new_stab += 'Z'
            elif oper == 'Z':  new_stab += 'X'
            else:              new_stab += oper
        out_list += [new_stab]
    
    return out_list



def remove_given_parity(list_elements, parity):
    '''
    Removes the elements of a given parity from the list
    '''
    new_list = []
    for elem in list_elements:
        if elem%2 != parity:
            new_list += [elem] 

    return new_list



def binary_to_decimal(string):
    '''
    '''
    num = 0
    max_power = len(string) - 1
    for i in range(len(string)):
        num += int(string[i])*2**(max_power - i)
    return num



def decimal_to_binary(num, length_list=6):
    '''
    Binary representation of a number
    Taken from functions.py'''
    binary = []
    for i in range(length_list):
        binary.insert(0, num&1)
        num = num >> 1
    return binary




def combine_stabs(list_stabs, list_destabs):
    '''
    takes a list of lists of stabilizers and
    a list of lists of destabilizers and 
    combine them.
    Should be able to do this faster directly
    in CHP, but it's OK.  MGA 02/20/2017.
    '''

    stab_dict = {}
    for i in range(len(list_stabs)):
        stab_dict[i] = {'n_stabs': len(list_stabs[i]),
                        'len_stabs': len(list_stabs[i][0]) - 1}

    combined_stabs = []
    combined_destabs = []
    for stab_index in stab_dict:
        if stab_index == 0:
            pre_n = 0
        else:
            pre_n = sum([stab_dict[i]['len_stabs']
                         for i in range(stab_index)])
        if stab_index == len(stab_dict) - 1:
            post_n = 0
        else:
            post_n = sum([stab_dict[i]['len_stabs']
                          for i in range(stab_index+1, len(stab_dict))])
    
        pre_Is = ''.join(['I' for i in range(pre_n)])
        post_Is = ''.join(['I' for i in range(post_n)])

        new_stabs, new_destabs = [], []
        for i in range(len(list_stabs[stab_index])):
            stab = list_stabs[stab_index][i]
            destab = list_destabs[stab_index][i]
            new_stab = stab[0] + pre_Is + stab[1:] + post_Is
            new_destab = destab[0] + pre_Is + destab[1:] + post_Is
            new_stabs += [new_stab]
            new_destabs += [new_destab]

        combined_stabs += new_stabs
        combined_destabs += new_destabs

    return combined_stabs, combined_destabs    




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



def stabs_QEC_diVin(dic, n_first_anc, code, stab_kind=None,
                    within_M=False, parity_oct=0):
    '''
    After one round of either X or Z stabs (for a CSS code)
    or the whole set of stabs (for a non-CSS code),
    with an unverified cat state, we first correct the hook 
    errors (errors that propagated from ancilla to data),
    and then return the correction for the data errors.
    
    parity_oct refers to the parity of the weight-8 stabilizer
    in the d5 color code, which is measured at a previous
    step.
    '''
    
    # so far only Steane and 5qubit codes
    
    extra_s = 0  # little hack to get the stabilizer right

    
    if code == 'd5color':
        # Notice the s=7 because we omit the first stab (octagon)
        n_q, s, w = 17, 7, 4
        # What was within_M?
        code_class = d5color.Code
        if type(stab_kind) != type(''):
            raise TypeError('stab_kind either X or Z.')
        if stab_kind == 'Z':
            extra_s = 8 + 1
            error = 'X'
        else:
            extra_s = 1
            error = 'Z'

    
    elif code == 'Steane':
        n_q, s, w = 7, 3, 4
        if within_M:  s = 2
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

    if code == 'd5color':
        data_error.insert(0, parity_oct)
        data_error_int = binary_to_decimal(data_error)
        data_corr = code_class.lookuptable_str[str(data_error_int)]
    
    else:
        data_corr = code_class.stabilizer_syndrome_dict[tuple(data_error)]
    
    if code == 'Steane' or code == 'd5color':
        data_corr = [i if i == 'I' else error for i in data_corr]   
    
    return data_corr, prop_corr



def stabs_QEC_bare_anc(dic, n_first_anc, code, stab_kind='X'):
    '''
    After one round of either X or Z stabs (for a CSS code)
    or the whole set of stabs (for a non-CSS code),
    with bare ancillae, we return the correction for the
    data errors.
    '''

    # so far only for Cross and Steane (need to implement it for surface-17)

    if code == 'Cross':
        n_q = 7
        len_dic = 6
        code_class = cross.Code
    
        outcome = [dic[n_first_anc + i][0] for i in range(len_dic)]
        outcome_integer = 0
        for i in range(len(outcome)):
            outcome_integer += outcome[i]*2**(5-i)
    
        corr = code_class.complete_lookup_table[outcome_integer]

    elif code == 'Steane':
        n_q = 7
        len_dic = 3
        code_class = steane.Code

        outcome = [dic[n_first_anc + i][0] for i in range(len_dic)]
        corr = code_class.stabilizer_syndrome_dict[tuple(outcome)]
       
    elif code == 'surface17':
        n_q = 9
        len_dic = 4
        code_class = surf17.Code
        corr_kind = stab_kind + 'stabs'

        outcome = [dic[n_first_anc + i][0] for i in range(len_dic)]
        outcome_string = ''.join(map(str,outcome))
        qubits_corr = code_class.lookuptable[corr_kind][outcome_string]
        corr = ['E' if i in qubits_corr else 'I' for i in range(n_q)]

    elif code == 'surface49':
        n_q = 25
        len_dic = 12
        code_class = surf49.Code
        corr_kind = stab_kind + 'stabs'

        outcome = [dic[n_first_anc + i][0] for i in range(len_dic)]
        outcome_string = ''.join(map(str,outcome))
        qubits_corr = code_class.lookuptable[corr_kind][outcome_string]
        corr = ['E' if i==1 else 'I' for i in qubits_corr]



    if len(dic) != len_dic:
        raise IndexError('The dict does not have the right length.')
        

    
    return corr



def create_EC_subcircs(code, Is_after2q, initial_I=True,
                       initial_trans=False, perfect_EC=False,
                       redun=3):
    '''
    creates circuit for distance-3 QEC: Cross, Shor, 5-qubit for now
    '''

    #redun = 3
    verify = False
    ancilla_parallel = True
    diVincenzo = True
    meas_errors = True


    # This option is only used to do perfect QEC at the end of a 
    # circuit to distinguish between correctable and uncorrectable
    # errors
    if perfect_EC:
        if code == 'd5color':
            n_data = 17
            code_stabs = d5color.Code.stabilizer_alt[:]
        if code == 'Cross':
            n_data = 7
            code_stabs = cross.Code.stabilizer_alt[:]
        elif code == 'Steane':
            code_stabs = steane.Code.stabilizer_alt[:]
            n_data = 7
        elif code == 'fivequbit':
            code_stabs = fivequbit.Code.stabilizer[:]
            n_data = 5

        EC_circ = cor.Bare_Correct.generate_rep_bare_meas(n_data,
                                                          code_stabs,
                                                          1,
                                                          False,
                                                          False,
                                                          False,
                                                          False,
                                                          True)
        
    else:

        if code == 'd5color':
            total_circ = c.Circuit()
            n_data = 17
            X_stabs = d5color.Code.stabilizer_alt[:8]
            Z_stabs = d5color.Code.stabilizer_alt[8:]
            for red in range(redun):
                EC_circ = cor.Bare_Correct.generate_rep_bare_meas(n_data,
                                                                  X_stabs,
                                                                  1,
                                                                  False,
                                                                  meas_errors,
                                                                  Is_after2q,
                                                                  initial_trans,
                                                                  ancilla_parallel)
                EC_circ = c.Encoded_Gate('Sx%i'%(red+1), [EC_circ]).circuit_wrap()
                total_circ.join_circuit(EC_circ)
                EC_circ = cor.Bare_Correct.generate_rep_bare_meas(n_data,
                                                                  Z_stabs,
                                                                  1,
                                                                  False,
                                                                  meas_errors,
                                                                  Is_after2q,
                                                                  initial_trans,
                                                                  ancilla_parallel)
                EC_circ = c.Encoded_Gate('Sz%i'%(red+1), [EC_circ]).circuit_wrap()
                total_circ.join_circuit(EC_circ)

            return total_circ


        # Cross code uses bare ancillae
        elif code == 'Cross':
            Cross_stabs = cross.Code.stabilizer_alt[:]
            n_subcircs = 3
            EC_circ = cor.Bare_Correct.generate_rep_bare_meas(7, Cross_stabs,
                                                              redun, initial_I,
                                                              meas_errors,
                                                              Is_after2q,
                                                              initial_trans,
                                                              ancilla_parallel)
        else:
            if code == 'Steane':
                code_stabs = steane.Code.stabilizer[:]
                n_subcircs = 6
            elif code == 'fivequbit':
                code_stabs = fivequbit.Code.stabilizer[:]
                n_subcircs = 3

            EC_circ = cor.Cat_Correct.cat_syndrome_4(code_stabs,
                                                     redun,
                                                     verify,
                                                     ancilla_parallel,
                                                     diVincenzo,
                                                     initial_I,
                                                     initial_trans,
                                                     code,
                                                     meas_errors,
                                                     Is_after2q)

    return EC_circ





def create_measure_2_logicals_ion(logicals='X', meas_errors=True,
                                  FT_meas=True, QEC_before=False):
    '''
    '''

    n_code = 7
    measure_circ = c.Circuit()

    if QEC_before:
        pass

    else:

        if logicals == 'X':
            
            # This means we will measure X_t X_a
            # 1.  Measure X7_t X7_a.  In our convention 7 -> 1.
            qubit_pairs = [[1,1], [2,1]]

            






def create_measure_2_logicals(Is_after2q, qubits, logicals='X',
                              meas_errors=True, FT_meas=True,
                              QEC_before=False, redun=3):
    '''
    QEC_before: adds a single QEC step on the ancillary logical
    qubit just to ensure that the X stabilizers are defined
    (in case we start with a product state of |0>).
    '''

    n_code = 7
    ent_gate = 'C' + logicals
    enc_gate_name = 'Partial_measurement'
    ancilla_parallel = True
    initial_I = False

    if len(qubits) == 1:  extra_name = ''
    elif len(qubits) == 2:  extra_name = 'long'
    
    measure_circ = c.Circuit()
    
    if logicals == 'Z':
        #QEC_stabs = [steane.Code.stabilizer[3], steane.Code.stabilizer[5]]
        QEC_stabs = steane.Code.stabilizer[3:6]

    elif logicals == 'X':
        #QEC_stabs = [steane.Code.stabilizer[0], steane.Code.stabilizer[1]]
        QEC_stabs = steane.Code.stabilizer[:3]
       
            
    if QEC_before:        
            
        EC_circ = cor.Cat_Correct.cat_syndrome_4(QEC_stabs,
                                                 1,
                                                 False,
                                                 ancilla_parallel,
                                                 True,
                                                 initial_I,
                                                 False,
                                                 'Steane',
                                                 meas_errors,
                                                 Is_after2q)

        # add QEC on ancillary logical qubit
        measure_circ.join_circuit_at(range(2*n_code,3*n_code), EC_circ)

    for i in range(redun):
        for qubit_pairs in qubits:
           
            # add I gates
            #I_circuit = create_I_circuit(n_code)
            #measure_circ.join_circuit_at(range(n_code), I_circuit)
            
            local_circ = c.Circuit()
            local_circ.add_gate_at([n_code*3], 'PrepareXPlus')
            
            #local_circ.add_gate_at([n_code*3], 'I')
            
            first_targ = n_code*qubit_pairs[0][0] + qubit_pairs[0][1]
            sec_targ = n_code*qubit_pairs[1][0] + qubit_pairs[1][1]
            
            local_circ.add_gate_at([n_code*3, first_targ], ent_gate)
            #local_circ.add_gate_at([n_code*3], 'I')
            #local_circ.add_gate_at([first_targ], 'I')
            
            local_circ.add_gate_at([n_code*3, sec_targ], ent_gate)
            #local_circ.add_gate_at([n_code*3], 'I')
            #local_circ.add_gate_at([sec_targ], 'I')
            
            
            if len(qubit_pairs) >= 4:
                third_targ = n_code*qubit_pairs[2][0] + qubit_pairs[2][1]
                fourth_targ = n_code*qubit_pairs[3][0] + qubit_pairs[3][1]
                local_circ.add_gate_at([n_code*3, third_targ], ent_gate)
                #local_circ.add_gate_at([n_code*3], 'I')
                #local_circ.add_gate_at([third_targ], 'I')
            
                local_circ.add_gate_at([n_code*3, fourth_targ], ent_gate)
                #local_circ.add_gate_at([n_code*3], 'I')
                #local_circ.add_gate_at([fourth_targ], 'I')
            

            if len(qubit_pairs) == 6:
                fifth_targ = n_code*qubit_pairs[4][0] + qubit_pairs[4][1]
                sixth_targ = n_code*qubit_pairs[5][0] + qubit_pairs[5][1]
                local_circ.add_gate_at([n_code*3, fifth_targ], ent_gate)
                #local_circ.add_gate_at([n_code*3], 'I')
                #local_circ.add_gate_at([fifth_targ], 'I')
                
                local_circ.add_gate_at([n_code*3, sixth_targ], ent_gate)
                #local_circ.add_gate_at([n_code*3], 'I')
                #local_circ.add_gate_at([sixth_targ], 'I')
                
            if meas_errors:
                local_circ.add_gate_at([n_code*3], 'ImX')
                #local_circ.add_gate_at([n_code*3], 'I')
            local_circ.add_gate_at([n_code*3], 'MeasureX')

            #for q_index in range(3*n_code):
            #    local_circ.add_gate_at([q_index], 'I')

            local_circ.to_ancilla([n_code*3])
            local_circ = c.Encoded_Gate(enc_gate_name, [local_circ]).circuit_wrap()
            measure_circ.join_circuit(local_circ, ancilla_parallel)
                
        if FT_meas:    

            # add I gates
            #I_circuit = create_I_circuit(n_code)
            #measure_circ.join_circuit_at(range(n_code), I_circuit)

            EC_circ = cor.Cat_Correct.cat_syndrome_4(QEC_stabs,
                                                     1,
                                                     False,
                                                     ancilla_parallel,
                                                     True,
                                                     initial_I,
                                                     False,
                                                     'Steane',
                                                     meas_errors,
                                                     Is_after2q)

            # QEC on ancillary logical qubit
            EC_circ_anc = copy.deepcopy(EC_circ)

            if logicals == 'Z':
                measure_circ.join_circuit_at(range(n_code), EC_circ)
            elif logicals == 'X':
                measure_circ.join_circuit_at(range(n_code,2*n_code), EC_circ)
            
            # add QEC on ancillary logical qubit
            measure_circ.join_circuit_at(range(2*n_code,3*n_code), EC_circ_anc)
            

            ####################### TEMPORARY
            # add QEC on ancillary logical qubit
            #measure_circ.join_circuit_at(range(2*n_code,3*n_code), EC_circ_anc)


    full_gatename = 'Measure2logicals' + extra_name + logicals
    measure_circ = c.Encoded_Gate(full_gatename, [measure_circ]).circuit_wrap()

    return measure_circ



def create_joint_EC(Is_after2q, logicals, non_anc_qubit='targ'):
    '''
    creates a supra-gate with two QEC steps: one on the ancillary
    logical qubit and the other on the qubit given as an input.
    '''
    
    n_code = 7
    ancilla_parallel = True
    meas_errors = True
    initial_I = False

    if logicals == 'Z':
        QEC_stabs = steane.Code.stabilizer[3:6]
    elif logicals == 'X':
        QEC_stabs = steane.Code.stabilizer[:3]

    
    if non_anc_qubit == 'ctrl':
        non_anc_range = range(n_code)
    elif non_anc_qubit == 'targ':
        non_anc_range = range(n_code, 2*n_code)
    
    
    QEC_circ = c.Circuit()

    EC_circ = cor.Cat_Correct.cat_syndrome_4(QEC_stabs,
                                             3,
                                             False,
                                             ancilla_parallel,
                                             True,
                                             initial_I,
                                             False,
                                             'Steane',
                                             meas_errors,
                                             Is_after2q)

    # QEC on ancillary logical qubit
    EC_circ_anc = copy.deepcopy(EC_circ)

    QEC_circ.join_circuit_at(non_anc_range, EC_circ)
            
    # add QEC on ancillary logical qubit
    QEC_circ.join_circuit_at(range(2*n_code,3*n_code), EC_circ_anc)
    
    full_gatename = 'JointQEC' + logicals
    QEC_circ = c.Encoded_Gate(full_gatename, [QEC_circ]).circuit_wrap()

    return QEC_circ



def create_I_circuit(n_qubits):
    '''
    creates a gate with only physical Identities
    Only function is to sample certain error configurations more easily.
    '''

    I_circuit = c.Circuit()
    for i in range(n_qubits):
        I_circuit.add_gate_at([i], 'I')
    I_circuit = c.Encoded_Gate('Logical_I', [I_circuit]).circuit_wrap()

    return I_circuit



def create_latt_surg_CNOT(Is_after2q, initial_I=True, anc_parallel=True,
                          EC_ctrl_targ=False, FT=True, flag=False):
    '''
    creates the whole supra-circuit for the lattice-surgery CNOT
    exclusive for the Steane code (distance-3 color code)
    
    EC_ctrl_targ: True if we want to add QEC on the control and the 
                  target qubits after the whole procedure.
    '''
    
    code = 'Steane'
    n_code = 7

    CNOT_circ = c.Circuit()
    #for i in range(3*n_code):
    #    CNOT_circ.add_gate_at([i], 'I')

    # (1) Preparation of the ancilla
    #CNOT_circ.add_gate_at([2*n_code+5], 'H')
    #CNOT_circ.add_gate_at([2*n_code+5, 2*n_code+3], 'CX')
    #CNOT_circ = c.Encoded_Gate('Preparation', [CNOT_circ]).circuit_wrap()

    if initial_I:
        I_circuit = create_I_circuit(3*n_code)
        #I_circuit = create_I_circuit(n_code)
        CNOT_circ.join_circuit_at(range(3*n_code), I_circuit)


    if FT == False:
        XX_qubits = [[[1,1], [1,3], [1,5], [2,1], [2,3], [2,5]]]
        measureXX_circ = create_measure_2_logicals(Is_after2q, XX_qubits, 'X', True, False, True, 1)
        in_range = [8,10,12] + range(14,21)
        CNOT_circ.join_circuit_at(in_range, measureXX_circ)
    
        ZZ_qubits = [[[0,0], [0,3], [0,4], [2,0], [2,3], [2,4]]]
        measureZZ_circ = create_measure_2_logicals(Is_after2q, ZZ_qubits, 'Z', True, False, False, 1)
        in_range = [0,3,4,14,17,18]
        CNOT_circ.join_circuit_at(in_range, measureZZ_circ)
    
        meas_circ = steane.Generator.create_encoded_circuit('MeasureXDestroy')
        meas_circ = c.Encoded_Gate('MeasureX', [meas_circ]).circuit_wrap()
        CNOT_circ.join_circuit_at(range(2*n_code, 3*n_code), meas_circ)

        return CNOT_circ

    
    if flag:
        measureXX_circ = cor.Flag_Correct.measure_logical_boundary('X')
        jointQEC_circ1 = cor.Flag_Correct.joint_QEC_split_qubits('Z', [1,2])
        measureZZ_circ = cor.Flag_Correct.measure_logical_boundary('Z')
        jointQEC_circ2 = cor.Flag_Correct.joint_QEC_split_qubits('X', [0,2])

    else:
        # (2) Measure XX between target and ancilla
        #XX_qubits = [[[1,1], [2,1]], [[1,3], [1,5]]]
        XX_qubits = [[[1,1], [2,1]], [[1,3], [2,3], [1,5], [2,5]]]
        #XX_qubits = [[[1,3], [2,3], [1,5], [2,5]], [[1,1], [2,1]]]
        #XX_qubits = [[[1,1], [1,3], [1,5], [2,1], [2,3], [2,5]]]
        #measureXX_circ = create_measure_2_logicals(Is_after2q, XX_qubits, 'X', True, True, True)
        measureXX_circ = create_measure_2_logicals(Is_after2q, XX_qubits, 'X', True, True, True)
        jointQEC_circ1 = create_joint_EC(Is_after2q, 'Z', non_anc_qubit='targ')
    
        #I_circuit = create_I_circuit(3*n_code)
        #CNOT_circ.join_circuit_at(range(3*n_code), I_circuit)
        # (2.1) Do QEC on ancillary logical qubit
        #QEC_anc = create_EC_subcircs(code, Is_after2q, False)
        #CNOT_circ.join_circuit_at(range(2*n_code,3*n_code), QEC_anc)
        # (3) Perform joint QEC on target and ancilla 
        # (only if XX and XXXX were measured) 
        #jointQEC_circ = create_joint_EC(Is_after2q, 'Z', non_anc_qubit='targ')
        #CNOT_circ.join_circuit_at(range(n_code, 3*n_code), jointQEC_circ)
    
        #I_circuit = create_I_circuit(3*n_code)
        #CNOT_circ.join_circuit_at(range(3*n_code), I_circuit)
    
        # (3) Measure ZZ between control and ancilla 
        #ZZ_qubits = [[[0,0], [0,4]], [[0,3], [2,3]]]
        ZZ_qubits = [[[0,3],[2,3]], [[0,0], [2,0], [0,4], [2,4]]]
        #ZZ_qubits = [[[0,0], [0,3], [0,4], [2,0], [2,3], [2,4]]]
        measureZZ_circ = create_measure_2_logicals(Is_after2q, ZZ_qubits, 'Z')
    
        # (4) Perform joint QEC on control and ancilla 
        # (only if ZZ and ZZZZ were measured) 
        jointQEC_circ2 = create_joint_EC(Is_after2q, 'X', non_anc_qubit='ctrl')
    
    CNOT_circ.join_circuit_at(range(n_code, 3*n_code), measureXX_circ)   
    # (3) Perform joint QEC on target and ancilla 
    # (only if XX and XXXX were measured) 
    #jointQEC_circ = create_joint_EC(Is_after2q, 'Z', non_anc_qubit='targ')
    CNOT_circ.join_circuit_at(range(n_code, 3*n_code), jointQEC_circ1)
    CNOT_circ.join_circuit(measureZZ_circ, anc_parallel)

    #I_circuit = create_I_circuit(3*n_code)
    #CNOT_circ.join_circuit(I_circuit)
    CNOT_circ.join_circuit_at(range(n_code)+range(2*n_code,3*n_code), jointQEC_circ2)
    
    # (4) Do QEC on ancillary logical qubit
    #QEC_anc = create_EC_subcircs(code, Is_after2q, False)
    #CNOT_circ.join_circuit_at(range(2*n_code,3*n_code), QEC_anc)

    #I_circuit = create_I_circuit(n_code)
    #CNOT_circ.join_circuit_at(range(2*n_code,3*n_code), I_circuit)
    
    # (5) Do QEC on control and target qubits
    if EC_ctrl_targ:
        QEC_ctrl = create_EC_subcircs(code, Is_after2q, False)
        QEC_targ = create_EC_subcircs(code, Is_after2q, False)
        CNOT_circ.join_circuit(QEC_ctrl, anc_parallel)
        CNOT_circ.join_circuit_at(range(n_code,2*n_code), QEC_targ)
    
    # (6) Measure the ancilla in the X basis
    meas_circ = steane.Generator.create_encoded_circuit('MeasureXDestroy')
    meas_circ = c.Encoded_Gate('MeasureX', [meas_circ]).circuit_wrap()
    CNOT_circ.join_circuit_at(range(2*n_code, 3*n_code), meas_circ)

    return CNOT_circ



def add_specific_error_config_CNOT(CNOT_circ, errors_to_add, gates_indexes):
    '''
    '''

    for i in range(len(errors_to_add)):
        error_event = errors_to_add[i]
        gate_index = gates_indexes[i]

        #print 'error event =', error_event
        #print 'gate index =', gate_index

        # Very non-elegant, but I'm in a hurry.  MGA: 10/30/17.
        if len(gate_index) == 2:
            error_circ = CNOT_circ.gates[gate_index[0]].circuit_list[0]
        elif len(gate_index) == 3:
            circ1 = CNOT_circ.gates[gate_index[0]].circuit_list[0]
            error_circ = circ1.gates[gate_index[1]].circuit_list[0]
        elif len(gate_index) == 4:
            circ1 = CNOT_circ.gates[gate_index[0]].circuit_list[0]
            circ2 = circ1.gates[gate_index[1]].circuit_list[0]
            error_circ = circ2.gates[gate_index[2]].circuit_list[0]

        print_circ = False
        #if gate_index == (1,3,0,8):  print_circ = True
        
        add_errors_after_gates(error_circ, [gate_index[-1]], [error_event], print_circ)

    return



def exhaustive_search_subset_latt_surg(subset, one_q_gates, two_q_gates,
                                       one_q_errors_type=['X'],
                                       two_q_errors_type=['IX','IX','XX']):
    '''
    At the end I decided not to implement this as a separate function.
    It would be nice to implement it as an iterator.
    '''

    n_one_q_errors = subset[0]
    n_two_q_errors = subset[1]

    total_indexes, total_errors = get_total_indexes_one_circ(subset,
                                                             one_q_gates,
                                                             two_q_gates,
                                                             one_q_errors_type,
                                                             two_q_errors_type)
    
    final_error_count, final_failure_count = 0, 0
    for i in range(len(total_indexes)):
        print total_errors[i], total_indexes[i]
        CNOT_circ_copy = create_latt_surg_CNOT(False,True,True,False,True,True)
        add_specific_error_config_CNOT(CNOT_circ_copy, total_errors[i], total_indexes[i])

        #if i==0:
        #    brow.from_circuit(CNOT_circ_copy, True)
        
        
