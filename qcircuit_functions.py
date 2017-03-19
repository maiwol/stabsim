import sys
import circuit as c
import cross
import steane
import fivequbit
import correction as cor
from visualizer import browser_vis as brow




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
                    within_M=False):
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
    
    data_corr = code_class.stabilizer_syndrome_dict[tuple(data_error)]
    if code == 'Steane':
        data_corr = [i if i == 'I' else error for i in data_corr]   
    
    return data_corr, prop_corr



def stabs_QEC_bare_anc(dic, n_first_anc, code):
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
       
            

    if len(dic) != len_dic:
        raise IndexError('The dict does not have the right length.')
        

    
    return corr



def create_EC_subcircs(code, Is_after2q, initial_I=True,
                       initial_trans=False, perfect_EC=False):
    '''
    creates circuit for distance-3 QEC: Cross, Shor, 5-qubit for now
    '''

    redun = 3
    verify = False
    ancilla_parallel = True
    diVincenzo = True
    meas_errors = True


    # This option is only used to do perfect QEC at the end of a 
    # circuit to distinguish between correctable and uncorrectable
    # errors
    if perfect_EC:
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

        # Cross code uses bare ancillae
        if code == 'Cross':
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



def create_measure_2_logicals(Is_after2q, qubits, logicals='X',
                              meas_errors=True, FT_meas=True):
    '''
    '''

    redun = 3
    n_code = 7
    ent_gate = 'C' + logicals
    enc_gate_name = 'Partial_measurement'
    ancilla_parallel = True
    
    measure_circ = c.Circuit()
    
    if logicals == 'Z':
        #QEC_stabs = [steane.Code.stabilizer[3], steane.Code.stabilizer[5]]
        QEC_stabs = steane.Code.stabilizer[3:6]

    elif logicals == 'X':
        #QEC_stabs = [steane.Code.stabilizer[0], steane.Code.stabilizer[1]]
        QEC_stabs = steane.Code.stabilizer[:3]
       


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
            local_circ.add_gate_at([first_targ], 'I')
            
            local_circ.add_gate_at([n_code*3, sec_targ], ent_gate)
            #local_circ.add_gate_at([n_code*3], 'I')
            local_circ.add_gate_at([sec_targ], 'I')
            
            
            if len(qubit_pairs) >= 4:
                third_targ = n_code*qubit_pairs[2][0] + qubit_pairs[2][1]
                fourth_targ = n_code*qubit_pairs[3][0] + qubit_pairs[3][1]
                local_circ.add_gate_at([n_code*3, third_targ], ent_gate)
                #local_circ.add_gate_at([n_code*3], 'I')
                local_circ.add_gate_at([third_targ], 'I')
            
                local_circ.add_gate_at([n_code*3, fourth_targ], ent_gate)
                #local_circ.add_gate_at([n_code*3], 'I')
                local_circ.add_gate_at([fourth_targ], 'I')
            

            if len(qubit_pairs) == 6:
                fifth_targ = n_code*qubit_pairs[4][0] + qubit_pairs[4][1]
                sixth_targ = n_code*qubit_pairs[5][0] + qubit_pairs[5][1]
                local_circ.add_gate_at([n_code*3, fifth_targ], ent_gate)
                #local_circ.add_gate_at([n_code*3], 'I')
                local_circ.add_gate_at([fifth_targ], 'I')
                
                local_circ.add_gate_at([n_code*3, sixth_targ], ent_gate)
                #local_circ.add_gate_at([n_code*3], 'I')
                local_circ.add_gate_at([sixth_targ], 'I')
                
            if meas_errors:
                local_circ.add_gate_at([n_code*3], 'ImX')
                local_circ.add_gate_at([n_code*3], 'I')
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
                                                     True,
                                                     False,
                                                     'Steane',
                                                     meas_errors,
                                                     Is_after2q)

            if logicals == 'Z':
                measure_circ.join_circuit_at(range(n_code), EC_circ)
            elif logicals == 'X':
                measure_circ.join_circuit_at(range(n_code,2*n_code), EC_circ)


    full_gatename = 'Measure2logicals' + logicals
    measure_circ = c.Encoded_Gate(full_gatename, [measure_circ]).circuit_wrap()

    return measure_circ



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
                          EC_ctrl_targ=False):
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

    I_circuit = create_I_circuit(2*n_code)
    #I_circuit = create_I_circuit(n_code)
    CNOT_circ.join_circuit_at(range(2*n_code), I_circuit)

    # (2) Measure XX between target and ancilla
    #XX_qubits = [[[1,1], [2,1]], [[1,3], [1,5]]]
    #XX_qubits = [[[1,1], [2,1]], [[1,3], [2,3], [1,5], [2,5]]]
    #XX_qubits = [[[1,3], [2,3], [1,5], [2,5]], [[1,1], [2,1]]]
    XX_qubits = [[[1,1], [1,3], [1,5], [2,1], [2,3], [2,5]]]
    measureXX_circ = create_measure_2_logicals(Is_after2q, XX_qubits, 'X')
    CNOT_circ.join_circuit(measureXX_circ, anc_parallel)

    I_circuit = create_I_circuit(3*n_code)
    CNOT_circ.join_circuit_at(range(3*n_code), I_circuit)
    
    # (2.1) Do QEC on ancillary logical qubit
    #QEC_anc = create_EC_subcircs(code, Is_after2q, False)
    #CNOT_circ.join_circuit_at(range(2*n_code,3*n_code), QEC_anc)
    
    #I_circuit = create_I_circuit(n_code)
    #CNOT_circ.join_circuit_at(range(2*n_code,3*n_code), I_circuit)
    
    # (3) Measure ZZ between control and ancilla 
    #ZZ_qubits = [[[0,0], [0,4]], [[0,3], [2,3]]]
    ZZ_qubits = [[[0,0], [0,3], [0,4], [2,0], [2,3], [2,4]]]
    measureZZ_circ = create_measure_2_logicals(Is_after2q, ZZ_qubits, 'Z')
    CNOT_circ.join_circuit(measureZZ_circ, anc_parallel)

    I_circuit = create_I_circuit(3*n_code)
    CNOT_circ.join_circuit(I_circuit)
    
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
