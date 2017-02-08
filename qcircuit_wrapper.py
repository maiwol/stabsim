import circuit as cir
import chper_extended as chper



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
        self.circuits = circuits[:]
        self.chp_loc = chp_location
        self.CHP_IO_files = CHP_IO_files



    def run_one_circ(circuit): 
        '''
        - runs circuit on chp
        - updates the stabs and destabs
        - returns the dictionary of measurement outcomes
        Input: - circuit: either a circuit object or an index
        '''

        if type(circuit) == type(0):
            circuit = self.circuits[circuit]

        n_d_q = len(circuit.ancilla_qubits())
        n_a_q = len(circuit.ancilla_qubits())

        circ_chp = chper.Chper(circ=circuit,
                               num_d_qub=n_d_q,
                               num_a_qub=n_a_q,
                               stabs=self.stabs[:],
                               destabs=self.destabs[:],
                               anc_stabs=[],
                               anc_destabs=[],
                               input_output_files=self.CHP_IO_files)

        dic, self.stabs, self.destabs = circ_chp.run(self.chp_loc)

        return dic
        
