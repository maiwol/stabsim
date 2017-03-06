"""
steane.py

"""

import sys
import os
import time
from circuit import *
#from visualizer import Printer
import correction

class CircuitError(Exception): pass
class InvalidGateError(CircuitError): pass

class Code:

    """Defines constants and methods useful for dealing with the Steane Code"""

    code_name='Steane'

    """Gates that the code currently supports."""

    """Single qubit transversal gates."""
    single_qubit_unitaries = ["I","X","Y","Z","H","S"]
    """Single qubit non-clifford gates."""
    single_qubit_non_clifford_unitaries = ["T"]
    """Two qubit transversal gates."""
    two_qubit_unitaries = ["CX","XC","CZ","ZC","CS","SC"]
    """All transversal unitaries."""
    unitaries = single_qubit_unitaries + two_qubit_unitaries + single_qubit_non_clifford_unitaries
    """All preparations."""
    preparations =["PrepareZ", "PrepareX", "PrepareXPlus", "PrepareXMinus", 
                   "PrepareYPlus", "PrepareYMinus", "PrepareZPlus", "PrepareZMinus"]
    """All measurements."""
    measurements = ["MeasureX", "MeasureY", "MeasureZ",
                    "MeasureXDestroy", "MeasureYDestroy", "MeasureZDestroy"]

    """All error correcting routines."""
    error_corrections = ["EC_ShorCorrect","EC_SteaneCorrect","EC_KnillCorrect"]

    ecc_redundancy=3
    verify=False
    ancilla_parallel=True
    diVincenzo=True
    initial_I=False

    """Preparations and measurements have error correction built into them, so
    only gates to add error correction after are the unitaries."""
    error_corrected_gates = unitaries

    all_gates = unitaries + preparations + measurements + error_corrections

    stabilizer = [
            ["I","I","I","X","X","X","X"],
            ["I","X","X","I","I","X","X"],
            ["X","I","X","I","X","I","X"],
            ["I","I","I","Z","Z","Z","Z"],
            ["I","Z","Z","I","I","Z","Z"],
            ["Z","I","Z","I","Z","I","Z"]]

    stabilizer_alt = [
                        [('X',3), ('X',4), ('X',5), ('X',6)],
                        [('X',1), ('X',2), ('X',5), ('X',6)],
                        [('X',0), ('X',2), ('X',4), ('X',6)],
                        [('Z',3), ('Z',4), ('Z',5), ('Z',6)],
                        [('Z',1), ('Z',2), ('Z',5), ('Z',6)],
                        [('Z',0), ('Z',2), ('Z',4), ('Z',6)]]


    logical = {"X": ["X","X","X","I","I","I","I"],
           "Y": ["Y","Y","Y","I","I","I","I"],
               "Z": ["Z","Z","Z","I","I","I","I"]}

    Z_stabs = ['+XIXIXIX', '+IXXIIXX', '+IIIXXXX',
           '+ZZZIIII', '+IZZZZII', '+IIZIZZI', '+IIIZZZZ']
    Z_destabs = ['+ZIIIIII', '+IZIIIII', '+IIIZIII',
             '+IIXIXIX', '+IIIIXXI', '+IIIIIXX', '+IIIIIIX']
    X_stabs = ['+ZIZIZIZ', '+IZZIIZZ', '+IIIZZZZ',
           '+XXXIIII', '+IXXXXII', '+IIXIXXI', '+IIIXXXX']
    X_destabs = ['+XIIIIII', '+IXIIIII', '+IIIXIII',
             '+IIZIZIZ', '+IIIIZZI', '+IIIIIZZ', '+IIIIIIZ']

    stabs_dict = {'Z': (Z_stabs, Z_destabs),
                  'X': (X_stabs, X_destabs)}


    block_size = 7

    stabilizer_syndrome_dict = {
                    (0,0,0):["I","I","I","I","I","I","I"],
                    (0,0,1):["E","I","I","I","I","I","I"],
                    (0,1,0):["I","E","I","I","I","I","I"],
                    (0,1,1):["I","I","E","I","I","I","I"],
                    (1,0,0):["I","I","I","E","I","I","I"],
                    (1,0,1):["I","I","I","I","E","I","I"],
                    (1,1,0):["I","I","I","I","I","E","I"],
                    (1,1,1):["I","I","I","I","I","I","E"]}

    # stabilizers in CHP-friendly format
    stabilizer_CHP = [
                        '+XIXIXIX',
                        '+IXXIIXX',
                        '+IIIXXXX',
                        '+ZIZIZIZ',
                        '+IZZIIZZ',
                        '+IIIZZZZ'
                     ]

    destabilizer_CHP = [
                        '+ZIIIIII',
                        '+IZIIIII',
                        '+IIIZIII',
                        '+IIIIIXX',
                        '+IIIIXIX',
                        '+IIIIXXX'
                       ]

    stabilizer_logical_CHP = {'+Z': '+ZZZIIII',
                              '-Z': '-ZZZIIII',
                              '+X': '+XXXIIII',
                              '-X': '-XXXIIII'}

    destabilizer_logical_CHP = {'+Z': '+IIXIXXI',
                                '-Z': '+IIXIXXI',
                                '+X': '+IIZIZZI',
                                '-X': '+IIZIZZI'}




    @classmethod
    def decode_meas_Steane(cls, list_meas):
        '''
        returns the eigenvalues of the 3 stabilizers based on the measurement
        outcomes.
        list_meas is a list with 7 entries.
        s0 = c3 + c4 + c5 + c6
        s1 = c1 + c2 + c5 + c6
        s2 = c0 + c2 + c4 + c6
        '''
        s0 = (list_meas[3] + list_meas[4] + list_meas[5] + list_meas[6])%2
        s1 = (list_meas[1] + list_meas[2] + list_meas[5] + list_meas[6])%2
        s2 = (list_meas[0] + list_meas[2] + list_meas[4] + list_meas[6])%2

        return (s0, s1, s2)


    @classmethod
    def decode_syndrome_Steane_EC(cls, list_meas):
        '''
        '''
        s = cls.decode_meas_Steane(list_meas)
        return cls.stabilizer_syndrome_dict[s]



    @classmethod
    def parity_meas_Steane_EC(cls, list_meas):
        '''
        '''
        #print 'list meas =', list_meas
        b = sum(list_meas)%2
        s0, s1, s2 = cls.decode_meas_Steane(list_meas)
        if (s0 == 1) or (s1 == 1) or (s2 == 1):   
            return 1 - b
        else:                                     
            return b


    
    @classmethod
    def parity_check(cls, list_meas):
        '''
        '''
        s0, s1, s2 = cls.decode_meas_Steane(list_meas)
        if (s0 == 1) or (s1 == 1) or (s2 == 1):
            return 1
        else:
            return 0



    @classmethod
    def stabilizer_syndrome_to_error_circuits(cls, stab_type='X'):
        #given a syndrome of the form (+/-1,+/-1,+/-1), make a circuit with the correct error.

        corr_circ_list=[]
        for syndrome in stabilizer_syndrome_dict:
            corr_circ = Circuit()
            for index, err in enumerate(stabilizer_syndrome_dict[syndrome]):
                if err =='E':
                    corr_circ.add_gate_at([index],stab_type)
            corr_circ_list += [(syndrome,corr_circ)]
        return corr_circ_list


class Generator:
    """Steane code circuits
    """

    T_type='Nielsen and Chuang'

    @classmethod
    def create_encoded_circuit(cls, gate, parallel=True):
        """Creates an encoded circuit.  Valid circuits come from Code.
        """

        if type(gate) == str:
            gate_name = gate
        else:
            gate_name = gate.gate_name

        encoded_circ = None

        if (gate_name in Code.all_gates):
            if (gate_name in Code.single_qubit_unitaries):
                """Single qubit gates are transverse."""
                encoded_circ = Generator.single_qubit_gate(gate_name)
            elif (gate_name in Code.single_qubit_non_clifford_unitaries):
                """Single non-Clifford gate unitaries"""
                encoded_circ = Generator.non_clifford_single_gate(gate_name)
            elif (gate_name in Code.two_qubit_unitaries):
                """Two qubit gates are transverse."""
                encoded_circ = Generator.two_qubit_gate(gate_name)
            elif (gate_name=="EC_ShorCorrect"):
                """Cat based quantum error correction"""
                encoded_circ = Generator.shor_correct(parallel)
            elif (gate_name=="EC_SteaneCorrect"):
                """Steane based quantum error correction"""
                encoded_circ = Generator.steane_correct(parallel)
            elif (gate_name=="EC_KnillCorrect"):
                """Knill based quantum error correction"""
                encoded_circ = Generator.knill_correct()
            elif (gate_name[:7]=="Prepare"):
                """State preparations."""
                encoded_circ = Generator.pauli_prepare(gate_name[7])
            elif (gate_name[:7]=="Measure"):
                """Two types of measurements, destructive and non-desctructive."""
                if (gate_name[-7:]=="Destroy"):
                    encoded_circ = Generator.encoded_destructive_measurement(gate_name[7])
                else:
                    encoded_circ = Generator.encoded_pauli_measurement(gate_name[7])
            encoded_circ.parent_gate = gate
            return encoded_circ
        else:
            print gate.gate_name
            raise InvalidGateError

    @classmethod
    def single_qubit_gate(cls, gate_name=None):
        """Single qubit Steane code gates that are transversal.
        """
        circ = Circuit()
        for index in range(7):
            circ.add_gate_at([index],gate_name)
        return circ

    @classmethod
    def non_clifford_single_gate(cls, gate_name=None):

        if(gate_name=="T"):
            if cls.T_type == 'Nielsen and Chuang' :
                """
                From Nielsen and Chuang p485.
                The following is equivalent to a fault tolerant T gate:

                |phi>------------------------------------------O--_ _-------|SX|-----T|phi>
                                                               |  _X_        ||
                       |0>----|H|----|T|---|exp(-i pi/4)SX|----.--  -----|Measure|
                                                 |
                                         |+>-----.----|MeasureX|
                """
                redundancy = 1

                magic_state_circ =  cls._magic_state_prep_and_verify_Nielsen_and_Chuang(redundancy)

                measure_circ = Circuit()

                measure_circ.join_circuit_at(range(7,14),magic_state_circ)

                for i in range(7):
                    measure_circ.add_gate_at([i+7,i],'CX')
                    measure_circ.add_gate_at([i],"MeasureZDestroy")

                switching_qubits = measure_circ._get_qubits(range(14))
                permute_gate = Permute_Gate('permute',switching_qubits,switching_qubits[7:14]+switching_qubits[:7])

                correct_T_syndrome = Circuit()
                for i in range(7):
                    correct_T_syndrome.add_gate_at([7+i],"X")
                    correct_T_syndrome.add_gate_at([7+i],"S")
                correct_T_syndrome_gate = Correction_Gate(gate_name= "Tcorrect", circuit_list=[correct_T_syndrome])

                #Put it all together:

                T_circuit = Circuit()
                T_circuit.join_circuit(measure_circ)

                T_circuit.add_gate_at(range(14),permute_gate)

                T_circuit.to_ancilla(range(7,14))

                #Printer.circuit_console_drawing(T_circuit)

                return T_circuit

            elif T_Type== 'Aliferis Magic State':
                pass

            elif T_Type== 'ORAQL GFI':
                pass


        else:
            raise InvalidGateError

    @classmethod
    def _magic_state_prep_and_verify_Nielsen_and_Chuang(cls, redundancy=1):

        #create magic state:
        magic_prep_circ = Circuit()

        magic_prep_circ.join_circuit(Generator.FT_encoded_zero())

        for i in range(7):
            magic_prep_circ.add_gate_at([i],"H")

        for i in range(7):
            magic_prep_circ.add_gate_at([i],"T")

        #measure magic state
        controls = []
        for i_redund in range(redundancy):

            synd_circ= Circuit()

            enc_plus = Generator.create_encoded_plus()

            synd_circ.join_circuit_at(range(7,14),enc_plus)

            for i in range(7):
                synd_circ.add_gate_at([i,7+i],"CX")
                synd_circ.add_gate_at([i,7+i],"CS")
                synd_circ.add_gate_at([7+i],"T")
                synd_circ.add_gate_at([7+i],"S")
                synd_circ.add_gate_at([7+i],"Z")

            #(The operator ZST is T^dag and is meant to do the controlled-e^(-i pi/4) gate)

            for i in range(7):
                synd_circ.add_gate_at([7+i],'X')

            controls += [Classical_Control(function= 'parity', answer = 1,
                        syndrome_qubits= synd_circ._get_qubits(range(7,14)))]

            synd_circ.to_ancilla(range(7,14))

            magic_prep_circ.join_circuit(synd_circ)

        control = Classical_Control(function = 'redundancy', answer = 1, controls= controls)

        magic_gate = Verify_Gate(gate_name='MagicStateTheta', circuit_list=[magic_prep_circ])

        #return magic_gate.circuit_wrap()
        return magic_prep_circ

    @classmethod
    def two_qubit_gate(cls, gate=None):
        """Two qubit Steane code gates that are transversal.
        """
        circ = Circuit()
        for index in range(7):
            circ.add_gate_at([index,index+7],gate)
        return circ

    @classmethod
    def encoded_destructive_measurement(cls, gate_name=None):
        """This defines a destructive measurement circuit of an encoded pauli gate
        of a CSS code.
        Note that in order to make this fault-tolerant one must use this carefully.
        In particulary one should not rely on the product of the measurement gates.
        Instead one should run a simple redundancy code check on these outputs and
        then interpret the measurement as the product of the measurment gates. """

        if not (gate_name=='X' or gate_name == 'Z'):
            print 'Can only encode X or Z destructive measurements this way.'
            return False

        n_data = Code.block_size

        m_circ=Circuit()
        for index in range(n_data):
            m_circ.add_gate_at([index],'Measure'+gate_name+'Destroy')

        return m_circ


    # At the moment this is not implemented. When it is, the decoder will have to be
    # modified. -Lukas (12-4-2011)
    @classmethod
    def encoded_pauli_measurement(cls, gate_name=None, redundancy=1, return_gate = False):
        '''
        non-destructively measurement of the logical qubit using a 3-cat state.
        '''
        correct = correction.Cat_Correct.create_cat_3

        n_data = Code.block_size
        n_ancilla= len(correct().qubits())-n_data

        circ = Circuit()

        logical_gate=Code().logical[gate_name]

        for i_redund in range(redundancy-1):
            for index in range(n_data):

                anc_start=n_data+i_redund*n_ancilla
                anc_end=n_data+(i_redund+1)*n_ancilla

                corr_circ = correct()
                circ.join_circuit_at(range(anc_start,anc_end),corr)

                if(logical_gate==gate_name):
                    circ.add_gate_at([anc_start,index],'C'+gate_name)
                    circ.add_gate_at([index],'Measure'+gate_name+'Destroy')

        gate = Encoded_Gate(gate_name='Encoded Measure'+gate_name,circuit_list=[circ])

        if return_gate==False:  return gate.circuit_wrap()
        if return_gate==True:   return gate


    @classmethod
    def pauli_prepare(cls, basis):
        if basis == 'Z':
            return correction.Steane_Correct.FT_encoded_zero_Steane()[0]
        elif basis == 'X':
            return correction.Steane_Correct.FT_encoded_plus_Steane()[0]





    # Error correction methods

    @classmethod
    def shor_correct(cls, parallel):
        redundancy = Code.ecc_redundancy
        verify = Code.verify
        ancilla_parallel = parallel
        diVincenzo = Code.diVincenzo
        initial_I = Code.initial_I
        return correction.Cat_Correct.cat_syndrome_4(Code.stabilizer,redundancy,
                                                     verify, ancilla_parallel,
                                                     diVincenzo, initial_I)

    @classmethod
    def steane_correct(cls, parallel):
        #redundancy=Code.ecc_redundancy
        # For Steane EC, we don't need to repeat 3 times to make it FT.
        #redundancy = 1
        #steane_module=sys.modules[__name__]
        #return correction.Steane_Correct.steane_syndrome(ecc=steane_module,
        #                                                 redundancy=redundancy,
        ancilla_parallel = parallel
        return correction.Steane_Correct.steane_syndrome(ancilla_parallel)

    @classmethod
    def knill_correct(cls):
        steane_module=sys.modules[__name__]
        return correction.Knill_Correct.knill_syndrome(ecc=steane_module)



    # The following methods were moved to correction.Steane:

    #@classmethod
    #def create_encoded_zero(cls):
    #   """Creates an encoded zero for explicit use only in Steane."""
    #   enc_zero = Circuit()
    #   for index in [0,1,3]:
    #       enc_zero.add_gate_at([index],"PrepareXPlus")
    #   for index in [2,4,5,6]:
    #       enc_zero.add_gate_at([index],"PrepareZPlus")
    #   cnot_sequence=[[0,2],[3,5],[1,6],[0,4],[3,6],[1,5],[0,6],[1,2],[3,4]]
    #   for indexes in cnot_sequence:
    #       enc_zero.add_gate_at(indexes,"CX")

    #   return enc_zero


    #@classmethod
    #def create_encoded_plus(cls):
    #   """Creates an encoded plus for explicit use only in Steane code.
    #   Almost identical to create_econded_zero; the only difference being CNOTs
    #   are flipped, 0's are +'s, and +'s are 0's."""
    #   enc_plus = Circuit()
    #   for index in [0,1,3]:
    #       enc_plus.add_gate_at([index],"PrepareZPlus")
    #   for index in [2,4,5,6]:
    #       enc_plus.add_gate_at([index],"PrepareXPlus")
    #   cnot_sequence=[[2,0],[5,3],[6,1],[4,0],[6,3],[5,1],[6,0],[2,1],[4,3]]
    #   for indexes in cnot_sequence:
    #       enc_plus.add_gate_at(indexes,"CX")

    #   enc_plus2=Circuit()
    #   for i in range(7):
    #       enc_plus2.add_gate_at([i],'Z')

    #   return enc_plus


    #@classmethod
    #def FT_encoded_zero(cls):

    #   purify_circ = cls.create_encoded_zero()
    #   enc_zero_anc= cls.create_encoded_zero()
    #   purify_circ.join_circuit_at(range(7,14), enc_zero_anc)

    #   for i in range(7):
    #       purify_circ.add_gate_at([i,7+i],'CX')

        #purify_circ._get_qubits(range(7))
        #measure and correct:

    #   for i in range(7):
    #       purify_circ.add_gate_at([7+i],'MeasureZDestroy')

        #control = Classical_Control(function='parity',
        #       syndrome_qubits = purify_circ._get_qubits(range(7,14)),
        #       target_qubits   = purify_circ._get_qubits(range(7)))

        #corr_circ = Circuit()
        #for i in range(7):
        #   corr_circ.add_gate_at([i],'X')

        #gate = Correction_Gate('Correct_To_Logical_Zero', control, [corr_circ])

        #purify_circ.add_gate(gate)

    #   purify_circ.to_ancilla(range(7,14))

    #   return purify_circ


    #@classmethod
    #def FT_encoded_plus(cls):
    #   purify_circ = cls.create_encoded_plus()
    #   enc_plus_anc= cls.create_encoded_plus()
    #   purify_circ.join_circuit_at(range(7,14), enc_plus_anc)

    #   for i in range(7):
    #       purify_circ.add_gate_at([7+i,i],'CX')

        #measure and correct:

    #   for i in range(7):
    #       purify_circ.add_gate_at([7+i],'MeasureXDestroy')

        #control = Classical_Control(function='parity',
        #       syndrome_qubits = purify_circ._get_qubits(range(7,14)),
        #       target_qubits   = purify_circ._get_qubits(range(7)))

        #corr_circ = Circuit()
        #for i in range(7):
        #   corr_circ.add_gate_at([i],'Z')

        #gate = Correction_Gate('Correct_To_Logical_Zero', control, [corr_circ])

        #purify_circ.add_gate(gate)

        #purify_circ.to_ancilla(range(7,14))

    #   return purify_circ
