import sys
import circuit as cir
import steane as st
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
                 - circuits: list of circuits that will be run
                             serially on chp.
        '''
        self.stabs = initial_state[0][:]
        self.destabs = initial_state[1][:]
        self.n_d_q = len(self.stabs)  
        # number of total data qubits in the whole "supra circuit", not
        # necessarily in this particular circuit.

        self.circuits = circuits[:]
        self.chp_loc = chp_location
        self.CHP_IO_files = CHP_IO_files



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
        print 'n_data =', self.n_d_q
        print 'n_anc =', n_a_q

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
        print 'dict =', dic

        return dic
       


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
       
        #brow.from_circuit(self.circuits[1])
        n_subcircs = len(self.circuits)
        #print n_subcircs
        #sys.exit(0)

        
        # (1) Measure M first time
        first_M = self.run_one_circ(0).values()[0][0]
        print 'First M =', first_M
        

        # (2) Measure stabilizers first time
        data_qs = self.circuits[1].data_qubits()
        data_q_ids = [q.qubit_id for q in data_qs]
        pre_ns = min(data_q_ids)
        pre_Is = ['I' for i in range(pre_ns)]
        post_ns = len(self.stabs) - max(data_q_ids) - 1
        post_Is = ['I' for i in range(post_ns)]
        
        output_dict = self.run_one_circ(1)
        n_first_anc = min(output_dict.keys())

        data_errors1, hook_errors = qfun.stabs_QEC_diVin(output_dict,
                                                        n_first_anc,
                                                        'Steane',
                                                        stab_kind)

        if hook_errors.count('I') != len(hook_errors):
            hook_errors = pre_Is + hook_errors + post_Is
            corr_state = qfun.update_stabs(self.stabs,
                                           self.destabs,
                                           hook_errors)
       
            self.stabs, self.destabs = corr_state[0][:], corr_state[1][:]


        print 'data errors 1 =', data_errors1



        # (3) Measure M second time
        second_M = self.run_one_circ(2).values()[0][0]
        print 'Second M =', second_M

        
        if data_errors1.count('I') == 7:
        
            if first_M == second_M:
                return first_M, 'normal'

            else:
                third_M = self.run_one_circ(4).values()[0][0]
                return third_M, 'normal'


        else:
            
            # (4) Measure stabilizers second time
            data_qs = self.circuits[3].data_qubits()
            data_q_ids = [q.qubit_id for q in data_qs]
            pre_ns = min(data_q_ids)
            pre_Is = ['I' for i in range(pre_ns)]
            post_ns = len(self.stabs) - max(data_q_ids) - 1
            post_Is = ['I' for i in range(post_ns)]
        
            output_dict = self.run_one_circ(3)
            n_first_anc = min(output_dict.keys())

            data_errors2, hook_errors = qfun.stabs_QEC_diVin(output_dict,
                                                            n_first_anc,
                                                            'Steane',
                                                            stab_kind)

            if hook_errors.count('I') != len(hook_errors):
                hook_errors = pre_Is + hook_errors + post_Is
                corr_state = qfun.update_stabs(self.stabs,
                                               self.destabs,
                                               hook_errors)
       
                self.stabs, self.destabs = corr_state[0][:], corr_state[1][:]

                print 'data errors 2 =', data_errors2

            
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
                    



        #first_outcomes = []
        #for i in range(2*n_subcircs/3):
            #print 'Round', i
            #print self.stabs
            #for g in self.circuits[i].gates:
                #print g.gate_name, [q.qubit_id for q in g.qubits] 
            #print self.run_one_circ(i).values()[0]
            #first_outcomes += [self.run_one_circ(i).values()[0][0]]
       
        #print first4outcomes
        #print self.stabs

        #outcomes_stab1 = [first4outcomes[0], first4outcomes[2]]
        #outcomes_stab2 = [first4outcomes[1], first4outcomes[3]]

        #if outcomes_stab1[0] != outcomes_stab1[1]:
        #    outcomes_stab1 += [self.run_one_circ(4).values()[0][0]]
            
        #if outcomes_stab2[0] != outcomes_stab2[1]:
        #    outcomes_stab2 += [self.run_one_circ(5).values()[0][0]]
       
        #if first_outcomes[0] != first_outcomes[1]:
            #first_outcomes += [self.run_one_circ(2).values()[0][0]]

        #print outcomes_stab1
        #print outcomes_stab2
        #parity = (outcomes_stab1[-1] + outcomes_stab2[-1])%2
        #print first_outcomes
        #parity = first_outcomes[-1]
        #print parity
        
        #return parity, len(outcomes_stab1), len(outcomes_stab2)
        #return parity, len(first_outcomes), len(first_outcomes)



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



    def run_one_diVincenzo(self, circuit, code, stab_kind=None):
        '''
        runs one round of X or Z stabilizers (for a CSS code)
        or the whole set of stabilizers (for a non-CSS code)
        assuming the ancillae are in an unverified cat state.
        circuit refers to the index of the circuit to be run.
        Based on "code", we then correct the hook errors and
        return the data errors.
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
                                                        stab_kind)

        if hook_errors.count('I') != len(hook_errors):
            hook_errors = pre_Is + hook_errors + post_Is
            corr_state = qfun.update_stabs(self.stabs,
                                           self.destabs,
                                           hook_errors)
       
            self.stabs, self.destabs = corr_state[0][:], corr_state[1][:]

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
        print 'pre =', pre_ns
        print 'post =', post_ns

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

            print 'X_errors =', X_data_errors
            print 'Z_errors =', Z_data_errors

            Z_corr, X_corr = Z_data_errors[-1], X_data_errors[-1]
        

        # update the final states only if a correction
        # is needed, to save some time
        if 'Z' in Z_corr:
            #print 'stabs =', self.stabs
            #print 'Z_corr =', Z_corr
            Z_corr = pre_Is[:] + Z_corr[:] + post_Is[:]
            print 'Z_corr =', Z_corr
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
            print 'X_corr =', X_corr
            self.stabs = corr_state[0][:]
            self.destabs = corr_state[1][:]

        return len(Z_data_errors), len(X_data_errors)



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
            parity, corr_type = q_oper.run_all(quant_gate.gate_name[16])

            print 'parity =', parity
            print 'corr type =', corr_type

            self.state = [q_oper.stabs[:], q_oper.destabs[:]]
            
            #return parity, (n_rep1, n_rep2)
            return parity, corr_type


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

        for q_oper in self.quant_opers:
            print q_oper.gate_name
            output = self.run_one_oper(q_oper)
            
            if q_oper.gate_name[-7:] == 'Correct':
                n_repEC += [output]
                print 'State after EC =', self.state[0]
            
            elif q_oper.gate_name == 'Measure2logicalsX':
                parX = output[0]
                corr_type = output[1]
                #n_rep1X, n_rep2X = output[1]
                print self.state[0]
                clause1 = corr_type == 'normal' and parX == 1
                clause2 = corr_type == 'alternative' and parX == 0
                if clause1 or clause2:
                    print 'Z correction after M_xx? Yes'
                    # Z logical on control
                    Z_corr = ['Z' for i in range(7)] + ['I' for i in range(7*2)]
                    corr_state = qfun.update_stabs(self.state[0][:],
                                                   self.state[1][:],
                                                   Z_corr)
                    self.state = [corr_state[0][:], corr_state[1][:]]
                    print 'State after corr:'
                    print self.state[0]


            elif q_oper.gate_name == 'Measure2logicalsZ':
                parZ = output[0]
                corr_type = output[1]
                #n_rep1Z, n_rep2Z = output[1]
                print self.state[0]
                clause1 = corr_type == 'normal' and parZ == 1
                clause2 = corr_type == 'alternative' and parZ == 0
                if clause1 or clause2:
                    print 'X correction after M_zz? Yes'
                    # X logical on target
                    X_corr = ['I' for i in range(7)]
                    X_corr += ['X' for i in range(7)]
                    X_corr += ['I' for i in range(7)]
                    corr_state = qfun.update_stabs(self.state[0][:],
                                                   self.state[1][:],
                                                   X_corr)
                    self.state = [corr_state[0][:], corr_state[1][:]]
                    print 'State after corr:'
                    print self.state[0]

            elif q_oper.gate_name == 'MeasureX':
                meas_dict = output
                meas_outcomes = [val[0] for val in meas_dict.values()]
                parXanc = st.Code.parity_meas_Steane_EC(meas_outcomes)
                print self.state[0]
                if parXanc == 1:
                    print 'Z correction after M_x?  Yes'
                    # Z logical on control
                    Z_corr = ['Z' for i in range(7)] + ['I' for i in range(7)]
                    corr_state = qfun.update_stabs(self.state[0][:],
                                                   self.state[1][:],
                                                   Z_corr)
                    self.state = [corr_state[0][:], corr_state[1][:]]
                    print 'State after corr:'
                    print self.state[0]

        return None

