import sys
import circuit as cir
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
        print 'n_anc =', n_a_q

        circ_chp = chper.Chper(circ=circuit,
                               num_d_qub=self.n_d_q,
                               num_a_qub=n_a_q,
                               stabs=self.stabs[:],
                               destabs=self.destabs[:],
                               anc_stabs=[],
                               anc_destabs=[],
                               input_output_files=self.CHP_IO_files)

        dic, self.stabs, self.destabs = circ_chp.run(self.chp_loc)

        return dic
       


class Measure_2_logicals(Quantum_Operation):
    '''
    Measurement of two logical operators for lattice surgery
    in the color code.
    Inherits from class Quantum_Operation.
    '''
    
    def run_all(self):
        '''
        Run the whole circuit.
        Currently just for a distance-3 code.
        
        Basic idea: we need to measure two operators in a FT way.
        We measured them twice.  If the outcomes coincide, we stop.
        If they're different we measured that operator again.
        The assumption is that there are 6 circuits.
        '''
        
        first4outcomes = []
        for i in range(4):
            #for g in self.circuits[i].gates:
                #print g.gate_name, [q.qubit_id for q in g.qubits] 
            #print self.run_one_circ(i).values()[0]
            first4outcomes += [self.run_one_circ(i).values()[0][0]]
       
        #print first4outcomes
        #print self.stabs

        outcomes_stab1 = [first4outcomes[0], first4outcomes[2]]
        outcomes_stab2 = [first4outcomes[1], first4outcomes[3]]

        if outcomes_stab1[0] != outcomes_stab1[1]:
            outcomes_stab1 += [self.run_one_circ(4).values()[0]]
            
        if outcomes_stab2[0] != outcomes_stab2[1]:
            outcomes_stab2 += [self.run_one_circ(5).values()[0]]
       
        print outcomes_stab1
        print outcomes_stab2
        parity = (outcomes_stab1[-1] + outcomes_stab2[-1])%2
        print parity

        return parity, len(outcomes_stab1), len(outcomes_stab2)



class QEC_d3(Quantum_Operation):
    '''
    Quantum Error Correction for a distance-3 code.
    Inherits from class Quantum_Operation
    '''

    def run_one_bare_anc(self, circuit, code):
        '''
        runs one round of QEC for the whole set of stabilizers
        assuming bare ancillae.
        circuit refers to the index of the circuit to be run.
        '''

        # need to add stab_kind to include surface-17 and
        # large-distance tological codes.

        output_dict = self.run_one_circ(circuit)
        n_first_anc = min(output_dict.keys())
        data_errors = qfun.stabs_QEC_bare_anc(output_dict,
                                              n_first_anc,
                                              code)
        
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
            print 'stabs =', self.stabs
            print 'Z_corr =', Z_corr
            Z_corr = pre_Is + Z_corr + post_Is
            print 'Z_corr =', Z_corr
            corr_state = qfun.update_stabs(self.stabs,
                                           self.destabs,
                                           Z_corr)
            self.stabs = corr_state[0][:]
            self.destabs = corr_state[1][:]
        
        if 'X' in X_corr:
            X_corr = pre_Is + X_corr + post_Is
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

        if quant_gate.gate_name == 'EC_CatCorrect':
            
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
            q_oper = Measure_2_logicals(self.state[:], quant_circs, self.chp_loc)
            parity, n_rep1, n_rep2 = q_oper.run_all()

            print parity, n_rep1, n_rep2

            self.state = [q_oper.stabs[:], q_oper.destabs[:]]
            
            return parity, (n_rep1, n_rep2)


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
        for q_oper in self.quant_opers:
            print q_oper.gate_name
            output = self.run_one_oper(q_oper)
            if q_oper.gate_name == 'EC_CatCorrect':
                n_repEC += [output]
            elif q_oper.gate_name == 'Measure2logicalsX':
                parX = output[0]
                n_rep1X, n_rep2X = output[1]
            elif q_oper.gate_name == 'Measure2logicalsZ':
                parZ = output[0]
                n_rep1Z, n_rep2Z = output[1]
            elif q_oper.gate_name == 'MeasureX':
                meas_dict = output
                print meas_dict

            print self.state[0], '\n'
