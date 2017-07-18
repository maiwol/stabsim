import sys
import copy
import circuit as cir
import steane as st
import d5color
import chper_extended as chper
import qcircuit_functions as qfun
from visualizer import browser_vis as brow



class Quantum_Operation(object):
    '''
    A quantum operation is a portion of a quantum circuit that
    consists of unitary operations and possibly measurements.
    Examples: - transversal logical gate
              - redundancy-3 QEC step for a distance-3 code
              - measurement of two logical operators for
                lattice surgery in the color code.
    '''

    def __init__(self, initial_state, circuits, chp_location, CHP_IO_files=False):
        '''
        Inputs:  - initial_state: generally without the ancilla;
                                  should be a list of lists:
                                  (1) stabs and (2) destabs.
                                  can also be an empty list in case the circuit
                                  already has prep gates.  This is the case for 
                                  the verification of the 8-qubit cat state.
                 - circuits: list of circuits that will be run
                             serially on chp.
        '''
            
        self.stabs = initial_state[0][:]
        self.destabs = initial_state[1][:]
        if len(self.stabs) == 0:
            self.n_d_q = len(circuits[0].data_qubits())
        else:
            self.n_d_q = len(self.stabs)  
            # number of total data qubits in the whole "supra circuit", not
            # necessarily in this particular circuit.

        self.circuits = circuits[:]
        self.chp_loc = chp_location
        self.CHP_IO_files = CHP_IO_files
        #print 'n_data =', self.n_d_q


    def run_one_circ(self, circuit): 
        '''
        - runs circuit on chp
        - updates the stabs and destabs
        - returns the dictionary of measurement outcomes
        Input: - circuit: either a circuit object or an index
        '''

        if type(circuit) == type(0):
            circuit = self.circuits[circuit]

        n_a_q = len(circuit.ancilla_qubits())
        #print 'n_data =', self.n_d_q
        #print 'n_anc =', n_a_q

        circ_chp = chper.Chper(circ=circuit,
                               num_d_qub=self.n_d_q,
                               num_a_qub=n_a_q,
                               stabs=self.stabs[:],
                               destabs=self.destabs[:],
                               anc_stabs=[],
                               anc_destabs=[],
                               input_output_files=self.CHP_IO_files)

        circ_chp_output = circ_chp.run(self.chp_loc)
        dic = circ_chp_output[0]
        self.stabs = circ_chp_output[1][:]
        self.destabs = circ_chp_output[2][:]
        #print 'dict =', dic

        return dic
       
    
    
    def run_one_diVincenzo(self, circuit, code, stab_kind=None,
                           parity_oct=0):
        '''
        runs one round of X or Z stabilizers (for a CSS code)
        or the whole set of stabilizers (for a non-CSS code)
        assuming the ancillae are in an unverified cat state.
        circuit refers to the index of the circuit to be run.
        Based on "code", we then correct the hook errors and
        return the data errors.
        
        parity_oct refers to the parity of the weight-8 
        stabilizer, which is measured at a previous step.
        '''

        data_qs = self.circuits[circuit].data_qubits()
        data_q_ids = [q.qubit_id for q in data_qs]
        pre_ns = min(data_q_ids)
        pre_Is = ['I' for i in range(pre_ns)]
        post_ns = len(self.stabs) - max(data_q_ids) - 1
        post_Is = ['I' for i in range(post_ns)]

        output_dict = self.run_one_circ(circuit)
        n_first_anc = min(output_dict.keys())
        data_errors, hook_errors = qfun.stabs_QEC_diVin(output_dict,
                                                        n_first_anc,
                                                        code,
                                                        stab_kind,
                                                        False,
                                                        parity_oct)

        if hook_errors.count('I') != len(hook_errors):
            hook_errors = pre_Is + hook_errors + post_Is
            corr_state = qfun.update_stabs(self.stabs,
                                           self.destabs,
                                           hook_errors)
       
            self.stabs, self.destabs = corr_state[0][:], corr_state[1][:]

        return data_errors





class Measure_2_logicals(Quantum_Operation):
    '''
    Measurement of two logical operators for lattice surgery
    in the color code.
    Inherits from class Quantum_Operation.
    '''
    
    def run_all(self, stab_kind):
        '''
        Run the whole circuit.
        Currently just for a distance-3 code.
        
        Basic idea: we need to measure two operators in a FT way.
        We measured them twice.  If the outcomes coincide, we stop.
        If they're different we measured that operator again.
        The assumption is that there are 6 circuits.
        '''
       
        QEC_func = self.run_one_diVincenzo
        code = 'Steane'

        #brow.from_circuit(self.circuits[1])
        n_subcircs = len(self.circuits)
        #print n_subcircs
        #sys.exit(0)


        
        # (1) Measure one time stabilizers to define them
        # (only used for Mxx if we start with anc in product state of |0>)
        if len(self.circuits) == 2:
            data_errors0 = QEC_func(0, code, stab_kind)
        
            data_qs = self.circuits[0].data_qubits()
            data_q_ids = [q.qubit_id for q in data_qs]
            pre_ns = min(data_q_ids)
            pre_Is = ['I' for i in range(pre_ns)]
            post_ns = len(self.stabs) - max(data_q_ids) - 1
            post_Is = ['I' for i in range(post_ns)]
            
            if data_errors0.count('I') != len(data_errors0):
                data_errors0 = pre_Is + data_errors0 + post_Is
                corr_state = qfun.update_stabs(self.stabs,
                                               self.destabs,
                                               data_errors0)
       
                self.stabs, self.destabs = corr_state[0][:], corr_state[1][:]
        
            
            # (2) Measure M one time
            only_M = self.run_one_circ(1).values()[0][0]
    
            return only_M, 'normal'

        elif len(self.circuits) == 1:
            
            return self.run_one_circ(0).values()[0][0], 'normal'



        # (1) Measure M first time
        first_M = self.run_one_circ(0).values()[0][0]
        #print 'First M =', first_M
        
        # (2) Measure stabilizers first time
        data_errors1 = QEC_func(1, code, stab_kind)
        #print 'data errors 1 =', data_errors1

        # (3) Measure M second time
        second_M = self.run_one_circ(2).values()[0][0]
        #print 'Second M =', second_M

        if data_errors1.count('I') == 7:
            if first_M == second_M:
                return first_M, 'normal'
            else:
                third_M = self.run_one_circ(4).values()[0][0]
                return third_M, 'normal'


        else:
            
            # (4) Measure stabilizers second time
            data_errors2 = QEC_func(3, code, stab_kind)
            #print 'data errors 2 =', data_errors2

            if data_errors1 == data_errors2:
                if first_M == second_M:
                    if stab_kind == 'X':
                        err_i = data_errors1.index('Z')
                        if err_i in [1,3,5]:  
                            corr_type = 'alternative'
                        else:  
                            corr_type = 'normal'

                    elif stab_kind == 'Z':
                        err_i = data_errors1.index('X')
                        if err_i in [0,3,4]:
                            corr_type = 'alternative'
                        else:
                            corr_type = 'normal'

                    return first_M, corr_type

                else:
                    third_M = self.run_one_circ(4).values()[0][0]
                    return third_M, 'normal'

            else:
                
                if first_M == second_M:
                    return first_M, 'normal'

                else:
                    third_M = self.run_one_circ(4).values()[0][0]
                    return third_M, 'normal'
                    
    
    
    def run_all_long(self, stab_kind):
        '''
        Run the whole circuit.
        Currently just for a distance-3 code.
        
        Basic idea: we need to measure two operators in a FT way.
        We measured them twice.  If the outcomes coincide, we stop.
        If they're different we measured that operator again.
        The assumption is that there are 6 circuits.
        '''
       
        code = 'Steane'
        QEC_func = self.run_one_diVincenzo
        if stab_kind == 'X':    
            tricky_indices = [1,3,5]
            Pauli_error = 'Z'
        elif stab_kind == 'Z':    
            tricky_indices = [0,3,4]
            Pauli_error = 'X'
        
        # default values
        corr_nonanc = 'normal'
        corr_anc = False

        #brow.from_circuit(self.circuits[0])
        #n_subcircs = len(self.circuits)
        #print n_subcircs
        #sys.exit(0)

        # list of outcomes of the low-weight and high-weight operators
        low_w, high_w = [], []

        first_subcirc_i = 0

        # (1) Measure one time stabilizers to define them
        # (only used for Mxx if we start with anc in product state of |0>)
        if len(self.circuits) > 12:
            data_errors0 = QEC_func(0, code, stab_kind)
        
            data_qs = self.circuits[0].data_qubits()
            data_q_ids = [q.qubit_id for q in data_qs]
            pre_ns = min(data_q_ids)
            pre_Is = ['I' for i in range(pre_ns)]
            post_ns = len(self.stabs) - max(data_q_ids) - 1
            post_Is = ['I' for i in range(post_ns)]
            
            if data_errors0.count('I') != len(data_errors0):
                data_errors0 = pre_Is + data_errors0 + post_Is
                corr_state = qfun.update_stabs(self.stabs,
                                               self.destabs,
                                               data_errors0)
       
                self.stabs, self.destabs = corr_state[0][:], corr_state[1][:]

            first_subcirc_i = 1


        #print 'State after first projection:'
        #print self.stabs

        # (2) Measure low-weight operator first time
        low_w += [self.run_one_circ(first_subcirc_i).values()[0][0]]
        #print 'low_w1 =', low_w[0]
        
        # (3) Measure high-weight operator first time
        high_w += [self.run_one_circ(first_subcirc_i+1).values()[0][0]]
        #print 'high_w1 =', high_w[0]

        #print 'State after high-w operator:'
        #print self.stabs

        # (4) Measure stabilizers for non-anc first time
        #print 'stab kind =', stab_kind
        data_errors_nonanc1 = QEC_func(first_subcirc_i+2, code, stab_kind)
        #print 'data errors non anc 1 =', data_errors_nonanc1

        # (5) Measure stabilizers for anc first time
        data_errors_anc1 = QEC_func(first_subcirc_i+3, code, stab_kind)
        #print 'data errors anc 1 =', data_errors_anc1

        #print 'State after QEC1:'
        #print self.stabs


        # (6) Measure low-weight operutor second time
        low_w += [self.run_one_circ(first_subcirc_i+4).values()[0][0]]
        #print 'low_w2 =', low_w[1]
        
        # (7) Measure high-weight operator second time
        high_w += [self.run_one_circ(first_subcirc_i+5).values()[0][0]]
        #print 'high_w2 =', high_w[1]

        #print 'State after second high-w operator:'
        #print self.stabs

        
        # if error on non-ancillary qubit
        if data_errors_nonanc1.count('I') != 7:
            
            # run QEC(non-anc) again
            data_errors_nonanc2 = QEC_func(first_subcirc_i+6, code, stab_kind)
            #print 'data errors nonanc 2 =', data_errors_nonanc2

            # if QEC(non-anc)(1) is equal to QEC(non-anc)(2)
            if data_errors_nonanc1 == data_errors_nonanc2:

                # if the operators are the same, then the error happened before
                if (low_w[0]==low_w[1] and high_w[0]==high_w[1]):
                    err_i = data_errors_nonanc1.index(Pauli_error)
                    # if the faulty qubit is on the boundary 
                    if err_i in tricky_indices:  corr_nonanc = 'alternative'


        # if error on ancillary qubit
        if data_errors_anc1.count('I') != 7:
                
            # run QEC(anc) again
            data_errors_anc2 = QEC_func(first_subcirc_i+7, code, stab_kind)
            #print 'data errors anc 2 =', data_errors_anc2

            # if QEC(anc)(1) is equal to QEC(anc)(2)
            if data_errors_anc1 == data_errors_anc2:
                    
                # if the operators are the same, then the error happened before
                if (low_w[0]==low_w[1] and high_w[0]==high_w[1]):
                    err_i = data_errors_anc1.index(Pauli_error)
                    # if the faulty qubit is on the boundary 
                    if err_i in tricky_indices:  corr_anc = True

        if low_w[0] != low_w[1]:
            low_w += [self.run_one_circ(first_subcirc_i+8).values()[0][0]]
            #print 'low_w3 =', low_w[2]
        if high_w[0] != high_w[1]:
            high_w += [self.run_one_circ(first_subcirc_i+9).values()[0][0]]
            #print 'high_w3 =', high_w[2]

        # for the parity, select the last outcome of each operator
        parity = (low_w[-1] + high_w[-1])%2
        return parity, (len(low_w), len(high_w)), corr_nonanc, corr_anc
          


class QEC_d3(Quantum_Operation):
    '''
    Quantum Error Correction for a distance-3 code.
    Inherits from class Quantum_Operation
    '''

    def run_one_bare_anc(self, circuit, code, stab_kind):
        '''
        runs one round of QEC for the whole set of stabilizers
        assuming bare ancillae.
        circuit refers to the index of the circuit to be run.
        '''

        # need to add stab_kind to include surface-17 and
        # large-distance tological codes.

        output_dict = self.run_one_circ(circuit)
        if stab_kind == 'both':
            anc_qubit_list = sorted(output_dict.keys())
            
            # X stabilizers come first by convention
            n_first_anc_X = min(anc_qubit_list)
            X_dict = {key: output_dict[key] 
                           for key in anc_qubit_list[:3]}
            Z_errors = qfun.stabs_QEC_bare_anc(X_dict,
                                               n_first_anc_X,
                                               code)
            Z_errors = ['Z' if oper=='E' else oper for oper in Z_errors]
            
            # Z stabilizers come second
            n_first_anc_Z = min(anc_qubit_list[3:])
            Z_dict = {key: output_dict[key] 
                           for key in anc_qubit_list[3:]} 
            
            X_errors = qfun.stabs_QEC_bare_anc(Z_dict,
                                               n_first_anc_Z,
                                               code)
            X_errors = ['X' if oper=='E' else oper for oper in X_errors]
       
            data_errors = Z_errors, X_errors


        return data_errors



    def run_fullQEC_nonCSS(self, code, bare=True):
        '''
        runs 2 or 3 rounds of QEC for a distance-3 non-CSS code,
        like the 5-qubit code or the Cross code.
        At the end, it applies a correction.
        It returns the number of QEC rounds.
        '''
        
        if bare:  QEC_func = self.run_one_bare_anc
        else:     QEC_func = self.run_one_diVincenzo
        
        data_qs = self.circuits[0].data_qubits()
        data_q_ids = [q.qubit_id for q in data_qs]
        pre_ns = min(data_q_ids)
        pre_Is = ['I' for i in range(pre_ns)]
        post_ns = len(self.stabs) - max(data_q_ids) - 1
        post_Is = ['I' for i in range(post_ns)]

        data_errors = []
        for i in range(2):
            #print 'stabs =', self.stabs
            data_errors += [QEC_func(i, code)]
            #print 'errors =', data_errors

        #print 'stabs after 2 =', self.stabs
        if data_errors[0] != data_errors[1]:
            data_errors += [QEC_func(2, code)]
            #print 'stabs after 3 =', self.stabs

        correction = data_errors[-1]
        #print 'correction =', correction

        # update the final states only if a correction
        # is needed, to save some time
        if correction.count('I') != len(correction):
            correction = pre_Is + correction + post_Is
            corr_state = qfun.update_stabs(self.stabs,
                                           self.destabs,
                                           correction)
            self.stabs = corr_state[0][:]
            self.destabs = corr_state[1][:]

        #print 'stabs after correction =', self.stabs
        
        return len(data_errors)



    def run_fullQEC_CSS(self, code, bare=True):
        '''
        runs 2 or 3 rounds of QEC for a distance-3 non-CSS code,
        like the Steane code or the surface-17.
        At the end, it applies a correction.
        It returns the number of QEC rounds.
        It assumes the X stabilizers come first.
        pre_n:  number of physical qubits before the physical
                qubits onto which this QEC is acting.
        post_n: number of physical qubits after the physical
                qubits onto which this QEC is acting.
        '''

        if bare:  QEC_func = self.run_one_bare_anc
        else:     QEC_func = self.run_one_diVincenzo

        data_qs = self.circuits[0].data_qubits()
        data_q_ids = [q.qubit_id for q in data_qs]
        pre_ns = min(data_q_ids)
        pre_Is = ['I' for i in range(pre_ns)]
        post_ns = len(self.stabs) - max(data_q_ids) - 1
        post_Is = ['I' for i in range(post_ns)]
        #print 'pre =', pre_ns
        #print 'post =', post_ns

        Z_data_errors, X_data_errors = [], []

        # this is the case if we are just trying to
        # perfect EC to distinguish between correctable
        # and uncorrectable errors.
        if len(self.circuits) == 1:
            Z_corr, X_corr = QEC_func(0, code, 'both')
            Z_data_errors = [Z_corr]
            X_data_errors = [X_corr]

        else:

            # run first 4 subcircuits (X stabs first)
            for i in range(2):
                #print 'stabs =', self.stabs
                Z_data_errors += [QEC_func(2*i, code, 'X')]
                #print 'Z errors =', Z_data_errors
                X_data_errors += [QEC_func(2*i+1, code, 'Z')]
                #print 'X errors =', X_data_errors

            #print 'stabs after 2 =', self.stabs

            # if the outcomes of the 2 X stabs measurements
            # don't coincide, do it a third time
            if Z_data_errors[0] != Z_data_errors[1]:
                Z_data_errors += [QEC_func(4, code, 'X')]
        
            # same for the Z stabs
            if X_data_errors[0] != X_data_errors[1]:
                X_data_errors += [QEC_func(5, code, 'Z')]

            #print 'X_errors =', X_data_errors
            #print 'Z_errors =', Z_data_errors

            Z_corr, X_corr = Z_data_errors[-1], X_data_errors[-1]
        

        # update the final states only if a correction
        # is needed, to save some time
        if 'Z' in Z_corr:
            #print 'stabs =', self.stabs
            #print 'Z_corr =', Z_corr
            Z_corr = pre_Is[:] + Z_corr[:] + post_Is[:]
            #print 'Z_corr =', Z_corr
            corr_state = qfun.update_stabs(self.stabs,
                                           self.destabs,
                                           Z_corr)
            self.stabs = corr_state[0][:]
            self.destabs = corr_state[1][:]
        
        if 'X' in X_corr:
            X_corr = pre_Is[:] + X_corr[:] + post_Is[:]
            corr_state = qfun.update_stabs(self.stabs,
                                           self.destabs,
                                           X_corr)
            #print 'X_corr =', X_corr
            self.stabs = corr_state[0][:]
            self.destabs = corr_state[1][:]

        return len(Z_data_errors), len(X_data_errors)



    def run_jointQEC(self, stab_kind):
        '''
        '''

        code = 'Steane'
        QEC_func = self.run_one_diVincenzo
        if stab_kind == 'X':  
            Pauli_error = 'Z'
            error_index = 3
        elif stab_kind == 'Z':  
            Pauli_error = 'X'
            error_index = 1

        data_errors1, data_errors2 = [], []

        for i in range(2):
        
            data_errors1 += [QEC_func(i, code, stab_kind)]
            #print 'errors1 =', data_errors1
            data_errors2 += [QEC_func(i+3, code, stab_kind)]
            #print 'errors2 =', data_errors2

        # if the outcomes of the 2 stabs measurements
        # don't coincide, do it a third time
        if data_errors1[0] != data_errors1[1]:
            data_errors1 += [QEC_func(2, code, stab_kind)]
        
        if data_errors2[0] != data_errors2[1]:
            data_errors2 += [QEC_func(5, code, stab_kind)]

        data_error1, data_error2 = data_errors1[-1], data_errors2[-1]
        w1 = 7 - data_error1.count('I')
        w2 = 7 - data_error2.count('I')

        if (w1+w2) == 2:
            data_error1 = ['I' for i in range(7)]
            data_error1[error_index] = Pauli_error
            data_error2 = ['I' for i in range(7)]
            data_error2[error_index] = Pauli_error

            if stab_kind == 'Z':
                log_corr = ['I' for i in range(7)] + data_error1 + data_error2
            elif stab_kind == 'X':
                log_corr = data_error1 + ['I' for i in range(7)] + data_error2

            #print 'State before JointQEC%s:' %stab_kind
            #print self.stabs

            corr_state = qfun.update_stabs(self.stabs,
                                           self.destabs,
                                           log_corr)
            #print 'log_corr =', log_corr
            self.stabs = corr_state[0][:]
            self.destabs = corr_state[1][:]

        return len(data_error1), len(data_error2)





class Verify_CatState(Quantum_Operation):
    '''
    '''

    def create_and_verify_8cat_state(self):
        '''
        rep_cat_gate should be a logical gate composed with
        n preps and verifications of an 8-qubit cat state
        '''

        for ver_i in range(len(self.circuits)):
            self.stabs, self.destabs = [], []
            #local_circ = copy.deepcopy(ver_gates[ver_i].circuit_list[0])
            #local_circ = local_circ.replace_qubit_ids(range(8))
            #local_circ.update_map()
            #brow.from_circuit(local_circ, True)
            output_dict = self.run_one_circ(ver_i)
            outcomes = [outcome[0] for outcome in output_dict.values()]
            if outcomes[0]==0 and outcomes[1]==0:
                break

        # number of times we had to prep the cat state
        n_cat = ver_i + 1

        return n_cat



class QEC_d5(Quantum_Operation):
    '''
    '''


    def measure_octagon(self, weight8_gate):
        '''
        measures the weight-8 stabilizer
        weight8_circ should be a gate with 2 logical gates:
        (1) the prep and verification of 8-qubit cat state
        (2) its coupling to the data qubits

        Outputs:  (1) the parity of the stabilizer measurement.
                  (2) the number of times the cat-state verf was done.
        '''
       
        prep_8cat = weight8_gate.circuit_list[0].gates[0]
        ver_circs = [g.circuit_list[0] for g in prep_8cat.circuit_list[0].gates]
        ver_oper = Verify_CatState([[],[]], ver_circs, self.chp_loc)
        n_cat = ver_oper.create_and_verify_8cat_state()
       
        # copy the circuit where we couple the cat state to the data
        couple_8cat = weight8_gate.circuit_list[0].gates[1]
        couple_circ = copy.deepcopy(couple_8cat.circuit_list[0])
        # convert the last 8 qubits to ancillary qubits (only on the copy)
        couple_circ.to_ancilla(range(17,17+8))

        self.stabs, self.destabs = qfun.combine_stabs(
                                            [self.stabs, ver_oper.stabs],
                                            [self.destabs, ver_oper.destabs])
        
        oct_dict = self.run_one_circ(couple_circ)
        oct_parity = sum([outcome[0] for outcome in oct_dict.values()])%2

        return oct_parity, n_cat
        


    def measure_stabilizers_one_kind(self, stab_gate, stab_kind):
        '''
        '''

        octagon_gate = stab_gate.circuit_list[0].gates[0]
        other_stabs_gate = stab_gate.circuit_list[0].gates[1]

        oct_par, n_cat = self.measure_octagon(octagon_gate)
        
        other_stabs_oper = Quantum_Operation([self.stabs[:], self.destabs[:]],
                                             other_stabs_gate.circuit_list[:],
                                             self.chp_loc)
        
        dat_err = other_stabs_oper.run_one_diVincenzo(0, 'd5color', 
                                                      stab_kind, oct_par)
        self.stabs = other_stabs_oper.stabs[:]
        self.destabs = other_stabs_oper.destabs[:]
            
        return dat_err


    
    def run_bare_anc(self, redun=3):
        '''
        with bare anc
        '''
        
        Z_data_errors, X_data_errors = [], []
        do_X, do_Z = True, True

        if redun==3:
            for circ_ind in range(2):
                if do_X:
                    Xcirc = self.circuits[0].gates[2*circ_ind].circuit_list[0]
                    Xcirc = Xcirc.gates[0].circuit_list[0].gates[0].circuit_list[0]
                    Xcirc_oper = Quantum_Operation([self.stabs[:], self.destabs[:]],
                                                   [Xcirc], self.chp_loc)
                    out_dict = Xcirc_oper.run_one_circ(0)
                    self.stabs, self.destabs = Xcirc_oper.stabs[:], Xcirc_oper.destabs[:]
                    X_stabs = [out_dict[i][0] for i in range(17,17+8)]
                    X_stabs_dec = qfun.binary_to_decimal(X_stabs)
                    Z_err = d5color.Code.lookuptable_str[str(X_stabs_dec)]
                    Z_err = [i if i=='I' else 'Z' for i in Z_err]
                    Z_data_errors += [Z_err]
                    if Z_err.count('Z') == 0:  do_X = False

                if do_Z:
                    Zcirc = self.circuits[0].gates[2*circ_ind+1].circuit_list[0]
                    Zcirc = Zcirc.gates[0].circuit_list[0].gates[0].circuit_list[0]
                    Zcirc_oper = Quantum_Operation([self.stabs[:], self.destabs[:]],
                                                   [Zcirc], self.chp_loc)
                    out_dict = Zcirc_oper.run_one_circ(0)
                    self.stabs, self.destabs = Zcirc_oper.stabs[:], Zcirc_oper.destabs[:]
                    Z_stabs = [out_dict[i][0] for i in range(17,17+8)]
                    Z_stabs_dec = qfun.binary_to_decimal(Z_stabs)
                    X_err = d5color.Code.lookuptable_str[str(Z_stabs_dec)]
                    X_err = [i if i=='I' else 'X' for i in X_err]
                    X_data_errors += [X_err]
                    if X_err.count('X') == 0:  do_Z = False
                


            # if the outcomes of the 2 X stabs measurements
            # don't coincide, do it a third time
            if (do_X) and (Z_data_errors[0] != Z_data_errors[1]):
                Xcirc = self.circuits[0].gates[4].circuit_list[0]
                Xcirc = Xcirc.gates[0].circuit_list[0].gates[0].circuit_list[0]
                Xcirc_oper = Quantum_Operation([self.stabs[:], self.destabs[:]],
                                               [Xcirc], self.chp_loc)
                out_dict = Xcirc_oper.run_one_circ(0)
                self.stabs, self.destabs = Xcirc_oper.stabs[:], Xcirc_oper.destabs[:]
                X_stabs = [out_dict[i][0] for i in range(17,17+8)]
                X_stabs_dec = qfun.binary_to_decimal(X_stabs)
                Z_err = d5color.Code.lookuptable_str[str(X_stabs_dec)]
                Z_err = [i if i=='I' else 'Z' for i in Z_err]
                Z_data_errors += [Z_err]
                                


            # same for the Z stabs
            if (do_Z) and (X_data_errors[0] != X_data_errors[1]):
                Zcirc = self.circuits[0].gates[5].circuit_list[0]
                Zcirc = Zcirc.gates[0].circuit_list[0].gates[0].circuit_list[0]
                Zcirc_oper = Quantum_Operation([self.stabs[:], self.destabs[:]],
                                               [Zcirc], self.chp_loc)
                out_dict = Zcirc_oper.run_one_circ(0)
                self.stabs, self.destabs = Zcirc_oper.stabs[:], Zcirc_oper.destabs[:]
                Z_stabs = [out_dict[i][0] for i in range(17,17+8)]
                Z_stabs_dec = qfun.binary_to_decimal(Z_stabs)
                X_err = d5color.Code.lookuptable_str[str(Z_stabs_dec)]
                X_err = [i if i=='I' else 'X' for i in X_err]
                X_data_errors += [X_err]

            #print 'X_errors =', X_data_errors
            #print 'Z_errors =', Z_data_errors

            Z_corr, X_corr = Z_data_errors[-1], X_data_errors[-1]
        

            # update the final states only if a correction
            # is needed, to save some time
            if 'Z' in Z_corr:
                #print 'stabs =', self.stabs
                #print 'Z_corr =', Z_corr
                #Z_corr = pre_Is[:] + Z_corr[:] + post_Is[:]
                #print 'Z_corr =', Z_corr
                corr_state = qfun.update_stabs(self.stabs,
                                               self.destabs,
                                               Z_corr)
                self.stabs = corr_state[0][:]
                self.destabs = corr_state[1][:]
        
            if 'X' in X_corr:
                #X_corr = pre_Is[:] + X_corr[:] + post_Is[:]
                corr_state = qfun.update_stabs(self.stabs,
                                               self.destabs,
                                               X_corr)
                #print 'X_corr =', X_corr
                self.stabs = corr_state[0][:]
                self.destabs = corr_state[1][:]

            return len(Z_data_errors), len(X_data_errors)




    def run_fullQEC_CSS(self):
        '''
        runs QEC for the distance-5 4.8.8 color code.
        At the end, it applies a correction.
        It returns the number of QEC rounds.
        It assumes the X stabilizers come first.
        pre_n:  number of physical qubits before the physical
                qubits onto which this QEC is acting.
        post_n: number of physical qubits after the physical
                qubits onto which this QEC is acting.
        '''

        circ_to_run = self.circuits[0].gates[0].circuit_list[0]
        QEC_func = self.measure_stabilizers_one_kind

        #data_qs = self.circuits[0].data_qubits()
        #data_q_ids = [q.qubit_id for q in data_qs]
        #pre_ns = min(data_q_ids)
        #pre_Is = ['I' for i in range(pre_ns)]
        #post_ns = len(self.stabs) - max(data_q_ids) - 1
        #post_Is = ['I' for i in range(post_ns)]
        #print 'pre =', pre_ns
        #print 'post =', post_ns
        
        # to make things quicker; change this later
        pre_Is, post_Is = [], []

        
        Z_data_errors, X_data_errors = [], []

        list_subs = range(10)
        while len(list_subs) > 0:
            next_sub = list_subs.pop(0)
            if next_sub%2 == 0:
                residue = 0
                stab_kind = 'X'
                data_errors = Z_data_errors
            else:
                residue = 1
                stab_kind = 'Z'
                data_errors = X_data_errors
        
            data_errors += [self.measure_stabilizers_one_kind(
                                    circ_to_run.gates[next_sub],
                                    stab_kind)]

            if len(data_errors) < 3:  continue

            if (data_errors[-3]==data_errors[-2]) and (data_errors[-2]==data_errors[-1]):
                list_subs = qfun.remove_given_parity(list_subs, residue)

        Z_corr = Z_data_errors[-1]
        X_corr = X_data_errors[-1]

        # update the final states only if a correction
        # is needed, to save some time
        if 'Z' in Z_corr:
            #print 'stabs =', self.stabs
            #print 'Z_corr =', Z_corr
            Z_corr = pre_Is[:] + Z_corr[:] + post_Is[:]
            #print 'Z_corr =', Z_corr
            corr_state = qfun.update_stabs(self.stabs,
                                           self.destabs,
                                           Z_corr)
            self.stabs = corr_state[0][:]
            self.destabs = corr_state[1][:]
        
        if 'X' in X_corr:
            X_corr = pre_Is[:] + X_corr[:] + post_Is[:]
            corr_state = qfun.update_stabs(self.stabs,
                                           self.destabs,
                                           X_corr)
            #print 'X_corr =', X_corr
            self.stabs = corr_state[0][:]
            self.destabs = corr_state[1][:]

        return len(Z_data_errors), len(X_data_errors)



class QEC_with_flags(Quantum_Operation):
    '''
    '''

    def run_one_roundCSS(self, circuit, previous_flag_outcomes,
                         n_flags=[1,1,1]):
        '''
        previous_flags_outcomes:  the triggering pattern 
        n_flags:  the number of flags for each stabilizer
        QEC d3:   [1,1,1]
        QEC d5:   [2,1,1,1,1,1,1,1]
        '''

        out_dict = self.run_one_circ(circuit)
        corr, flag_outcomes = qfun.get_syn_with_flags(out_dict,
                                                      previous_flag_outcomes,
                                                      n_flags)
        
        return corr, flag_outcomes

    def run_first_round_d5(self, init_state, QEC_circs):
        '''
        Makeshift function only to test that we can correct every hook error
        '''
        corrX, flags_outcomesX = self.run_one_roundCSS(0, ((0,0),0,0,0,0,0,0,0), 
                                                       [2,1,1,1,1,1,1,1])
        print corrX, flags_outcomesX
        corrZ, flags_outcomesZ = self.run_one_roundCSS(1, flags_outcomesX,
                                                       [2,1,1,1,1,1,1,1])
        print corrZ, flags_outcomesZ                   
        
        return corrX, flags_outcomesX, corrZ, flags_outcomesZ


    def run_one_round_Reichardt_d3(self, circuit, previous_flag_outcome,
                                   with_flag=True):
        '''
        One round of the circuit from Reichardt paper (Figure 8b) to measure
        the 3 stabilizers of the d3 color code with only one flag.
        '''

        out_dict = self.run_one_circ(circuit)
        out_keys = out_dict.keys()[:]
        out_keys.sort()
        if with_flag:
            syn = [out_dict[i][0] for i in out_keys[:-1]]
            flag = out_dict[out_keys[-1]][0]
        else:
            syn = [out_dict[i][0] for i in out_keys[:]]
            flag = None
            
        #print 'syn =', syn
        #print 'flag =', flag
        Steane_lookup = st.Code.total_lookup_table
        corr = Steane_lookup[previous_flag_outcome][tuple(syn)]
        #print 'corr = ', corr

        return corr, flag

   

    def run_all_Reichardt_d3(self, init_state):
        '''
        Makeshift function to make sure we can correct all the hook errors
        '''
        
        corrX, flagX = self.run_one_round_Reichardt_d3(0, 0)
        corrZ, flagZ = self.run_one_round_Reichardt_d3(1, flagX)
        n_errors = corrX.count('E') + corrZ.count('E') + flagX + flagZ
        
        if n_errors > 0:
            # flagX2 will always be None
            corrX2, flagX2 = self.run_one_round_Reichardt_d3(2, flagZ, False)
            # flagZ2 will always be None as well.
            corrZ2, flagZ2 = self.run_one_round_Reichardt_d3(3, flagX, False)
            
            corrX2 = [oper if oper=='I' else 'Z' for oper in corrX2]
            corrZ2 = [oper if oper=='I' else 'X' for oper in corrZ2]

            self.stabs, self.destabs = qfun.update_stabs(self.stabs[:],
                                                         self.destabs[:],
                                                         corrX2)
            self.stabs, self.destabs = qfun.update_stabs(self.stabs[:],
                                                         self.destabs[:],
                                                         corrZ2)
            #print corrX, flagX, corrZ, flagZ, corrX2, corrZ2

        return None
            



class Supra_Circuit(object):
    '''
    a supra-circuit is composed of several quantum operations.
    '''

    def __init__(self, initial_state, circuit, code, chp_location,
                 bare_ancilla=False):
        '''
        bare_ancilla refers to whether or not the ancillae are bare
        qubits.
        '''
   
        self.state = initial_state[:]
        self.quant_opers = circuit.gates[:]
        self.code = code
        self.chp_loc = chp_location
        self.bare = bare_ancilla

    

    def run_one_oper(self, quant_gate):
        '''
        runs one quantum operation and returns the final state
        quant_gate should be a Gate object with subcircuits.
        '''
   
        sub_circ = quant_gate.circuit_list[0]

        
        if quant_gate.gate_name[:8] == 'JointQEC':
            
            stab_kind = quant_gate.gate_name[-1]
        
            quant_circs = [g.circuit_list[0] for g in sub_circ.gates]
            quant_circs0 = [g.circuit_list[0] for g in quant_circs[0].gates]
            quant_circs1 = [g.circuit_list[0] for g in quant_circs[1].gates]
            reordered_quant_circs = quant_circs0 + quant_circs1

            q_oper = QEC_d3(self.state[:], reordered_quant_circs, self.chp_loc)
            n_rep1, n_rep2 = q_oper.run_jointQEC(stab_kind)
            
            self.state = [q_oper.stabs[:], q_oper.destabs[:]]
        
            return n_rep1, n_rep2 


        if quant_gate.gate_name[-7:] == 'Correct':
            
            quant_circs = [g.circuit_list[0] for g in sub_circ.gates]
            q_oper = QEC_d3(self.state[:], quant_circs, self.chp_loc)
            
            if self.code == 'Steane':
                n_rep = q_oper.run_fullQEC_CSS(self.code, self.bare)
            
            elif self.code=='Cross' or self.code=='5qubit':
                n_rep = q_oper.run_fullQEC_nonCSS(self.code, self.bare)
        
            self.state = [q_oper.stabs[:], q_oper.destabs[:]]

            return n_rep

        
        elif quant_gate.gate_name[:16] == 'Measure2logicals':
            
            quant_circs = [g.circuit_list[0] for g in sub_circ.gates]
            #faulty_gate = quant_circs[0].gates[2]
            #if faulty_gate.gate_name == 'CX':
                #faulty_qubit = faulty_gate.qubits[1]
                #err_g = quant_circs[0].insert_gate(faulty_gate, [faulty_qubit], '', 'Z', False)
                #brow.from_circuit(quant_circs[0], True)
            q_oper = Measure_2_logicals(self.state[:], quant_circs, self.chp_loc)
            #parity, n_rep1, n_rep2 = q_oper.run_all(quant_gate.gate_name[16])

            if len(quant_circs) < 10:
                parity, corr_type = q_oper.run_all(quant_gate.gate_name[-1])
                #print 'parity =', parity
                #print 'corr type =', corr_type

                self.state = [q_oper.stabs[:], q_oper.destabs[:]]
                return parity, corr_type
            
            else:
                parity, rep, corr_type, anc_corr = q_oper.run_all_long(quant_gate.gate_name[-1])
                #print 'parity =', parity
                #print 'corr type =', corr_type
                #print 'anc corr =', anc_corr

                self.state = [q_oper.stabs[:], q_oper.destabs[:]]

                #print self.state[0]
                #sys.exit(0)
                return parity, rep, corr_type, anc_corr




        else:
            # assume it's just transversal logical gate or something that
            # doesn't require feedback based on measurements.
            
            q_oper = Quantum_Operation(self.state[:], [sub_circ], self.chp_loc)
            if quant_gate.gate_name[:7] == 'Measure':
                sub_circ.to_ancilla([q.qubit_id for q in sub_circ.qubits()])
                q_oper.n_d_q = len(q_oper.stabs) - len(sub_circ.ancilla_qubits())
            output_dict = q_oper.run_one_circ(0)            

            self.state = [q_oper.stabs[:], q_oper.destabs[:]]
            
            return output_dict



class CNOT_latt_surg(Supra_Circuit):
    '''
    '''

    def run_all_gates(self):
        '''
        '''

        n_repEC = []
        
        gate_i = 0

        #print 'Initial state =', self.state[0]


        for q_oper in self.quant_opers:
            #print q_oper.gate_name
            output = self.run_one_oper(q_oper)
           

            if q_oper.gate_name[:8] == 'JointQEC':
                n_rep1, n_rep2 = output
                #print 'State after JoinQEC:'
                #print self.state[0]
                #sys.exit(0)


            if q_oper.gate_name[-7:] == 'Correct':
                n_repEC += [output]
                #print 'State after EC =', self.state[0]
            
            elif q_oper.gate_name == 'Measure2logicalsX':
                parX = output[0]
                corr_type = output[1]
                #n_rep1X, n_rep2X = output[1]
                #print self.state[0]
                clause1 = corr_type == 'normal' and parX == 1
                clause2 = corr_type == 'alternative' and parX == 0
                if clause1 or clause2:
                    #print 'Z correction after M_xx? Yes'
                    # Z logical on control
                    Z_corr = ['Z' for i in range(7)] + ['I' for i in range(7*2)]
                    corr_state = qfun.update_stabs(self.state[0][:],
                                                   self.state[1][:],
                                                   Z_corr)
                    self.state = [corr_state[0][:], corr_state[1][:]]
                    #print 'State after corr:'
                    #print self.state[0]


            elif q_oper.gate_name[:20] == 'Measure2logicalslong':
                stab = q_oper.gate_name[-1]
                parM = output[0]
                rep_low, rep_high = output[1]
                corr_type = output[2]
                anc_corr = output[3]
                #print self.state[0]
                
                # decide whether or not to apply the logical correction
                clause1 = corr_type == 'normal' and parM == 1
                clause2 = corr_type == 'alternative' and parM == 0
                if (clause1 or clause2):
                    #print 'Correction after M_%s%s? Yes' %(stab, stab)
                    
                    # if stab is X, we apply Z logical on control
                    if stab == 'X':
                        log_corr = ['Z' for i in range(7)] + ['I' for i in range(7*2)]
                    # if stab is Z, we apply X logical on target
                    elif stab == 'Z':
                        log_corr = ['I' for i in range(7)]
                        log_corr += ['X' for i in range(7)]
                        log_corr += ['I' for i in range(7)]
                        
                    corr_state = qfun.update_stabs(self.state[0][:],
                                                   self.state[1][:],
                                                   log_corr)
                    self.state = [corr_state[0][:], corr_state[1][:]]
                    #print 'State after corr:'
                    #print self.state[0]

                # decide whether or not to apply the logical operator on the ancilla
                if anc_corr:
                    #print 'Correction after M_%s%s on ancilla? Yes' %(stab, stab)
                    # if stab is X, Z logical on ancilla
                    if stab == 'X':
                        log_corr = ['I' for i in range(7*2)] + ['Z' for i in range(7)]
                    # if stab is Z, X logical on target
                    elif stab == 'Z':
                        log_corr = ['I' for i in range(7)]
                        log_corr += ['X' for i in range(7)]
                        log_corr += ['I' for i in range(7)]
                        
                    corr_state = qfun.update_stabs(self.state[0][:],
                                                   self.state[1][:],
                                                   log_corr)
                    self.state = [corr_state[0][:], corr_state[1][:]]
                    #print 'State after corr:'
                    #print self.state[0]



            elif q_oper.gate_name == 'Measure2logicalsZ':
                parZ = output[0]
                corr_type = output[1]
                #n_rep1Z, n_rep2Z = output[1]
                #print self.state[0]
                clause1 = corr_type == 'normal' and parZ == 1
                clause2 = corr_type == 'alternative' and parZ == 0
                if clause1 or clause2:
                    #print 'X correction after M_zz? Yes'
                    # X logical on target
                    X_corr = ['I' for i in range(7)]
                    X_corr += ['X' for i in range(7)]
                    X_corr += ['I' for i in range(7)]
                    corr_state = qfun.update_stabs(self.state[0][:],
                                                   self.state[1][:],
                                                   X_corr)
                    self.state = [corr_state[0][:], corr_state[1][:]]
                    #print 'State after corr:'
                    #print self.state[0]

            elif q_oper.gate_name == 'MeasureX':
                meas_dict = output
                meas_outcomes = [val[0] for val in meas_dict.values()]
                parXanc = st.Code.parity_meas_Steane_EC(meas_outcomes)
                #print self.state[0]
                if parXanc == 1:
                    #print 'Z correction after M_x?  Yes'
                    # Z logical on control
                    Z_corr = ['Z' for i in range(7)] + ['I' for i in range(7)]
                    corr_state = qfun.update_stabs(self.state[0][:],
                                                   self.state[1][:],
                                                   Z_corr)
                    self.state = [corr_state[0][:], corr_state[1][:]]
                    #print 'State after corr:'
                    #print self.state[0]

                #sys.exit(0)
        return None

