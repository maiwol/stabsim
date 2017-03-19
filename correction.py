import sys
import os
from circuit import *
from visualizer import browser_vis as brow



class Surface_Code_ion_trap:
    '''
    Measure stabilizers with a bare ancilla for each stabilizer, no cat states.
    Class defined to implement surface-17 code.
    The gates are already compiled to the primitve gates for ion traps.
    '''


    @classmethod
    def insert_I_errors_to_circ(cls, whole_circ, Is_after_2q,
                                Is_after_1q, MS_heating,
                                Stark, qubit_assignment,
                                time_MS, time_1q):
        '''
        '''
        if Is_after_1q:
            for g in whole_circ.gates[::-1]:
                if (len(g.qubits) == 1) and (g.gate_name[0] != 'I'):
                    new_g = whole_circ.insert_gate(g, g.qubits, '', 'I', False)

        if Is_after_2q:
            for g in whole_circ.gates[::-1]:
                if (len(g.qubits) == 2) and (g.gate_name[:2] != 'II'):
                    new_g = whole_circ.insert_gate(g, [g.qubits[0]], '', 'I', False)
                    new_g = whole_circ.insert_gate(g, [g.qubits[1]], '', 'I', False)

        if MS_heating:
            for g in whole_circ.gates[::-1]:
                if g.gate_name[:2] == 'MS':
                    x_ion1 = qubit_assignment.index(g.qubits[0].qubit_id)  # ion1 position
                    x_ion2 = qubit_assignment.index(g.qubits[1].qubit_id)  # ion2 position
                    ion_distance = abs(x_ion1 - x_ion2)   # distance between ions
                    MS_duration = time_MS(ion_distance)   # duration of MS gate
                    new_g = whole_circ.insert_gate(g, g.qubits, '', 'II_heat', False)
                    new_g.duration = MS_duration 

        if Stark:
            for g in whole_circ.gates[::-1]:
                if g.gate_name[:2] == 'MS':
                    x_ion1 = qubit_assignment.index(g.qubits[0].qubit_id)  # ion1 position
                    x_ion2 = qubit_assignment.index(g.qubits[1].qubit_id)  # ion2 position
                    ion_distance = abs(x_ion1 - x_ion2)   # distance between ions
                    MS_duration = time_MS(ion_distance)   # duration of MS gate
                    new_g1 = whole_circ.insert_gate(g, [g.qubits[0]], '', 'I_stark', False)
                    new_g1.duration = MS_duration
                    new_g2 = whole_circ.insert_gate(g, [g.qubits[1]], '', 'I_stark', False)
                    new_g2.duration = MS_duration
                elif (len(g.qubits) == 1) and (g.gate_name[0] != 'I') and (g.gate_name[0] != 'P'):
                    new_g = whole_circ.insert_gate(g, [g.qubits[0]], '', 'I_stark', False)
                    new_g.duration = time_1q

        return whole_circ
                    
                    


    @classmethod
    def generate_one_stab_ion_trap(cls, stabilizer, n_total, 
                                   i_ancilla, meas_errors=True):
        '''
        generates the circuit corresponding to 1 stabilizer
        measurement with ion-trap gates.
        The only I-like errors are measurements.
        '''
        stab_kind = stabilizer[0][0]    # 'X' or 'Z'
        stab_weight = len(stabilizer)

        stab_circ = Circuit()
        if len(stabilizer) == 2:
            stab_circ.add_gate_at([i_ancilla], 'PrepareZMinus')
        elif len(stabilizer) == 4:
            stab_circ.add_gate_at([i_ancilla], 'PrepareZPlus')
           
        if stab_kind == 'Z':
            for oper in stabilizer:
                stab_circ.add_gate_at([oper[1]], 'RY +')
                stab_circ.add_gate_at([oper[1]], 'RX -')
                stab_circ.add_gate_at([oper[1], i_ancilla], 'MS')
                stab_circ.add_gate_at([oper[1]], 'RY -')

        elif stab_kind == 'X':
            for oper in stabilizer:
                stab_circ.add_gate_at([oper[1]], 'RX +')
                stab_circ.add_gate_at([oper[1], i_ancilla], 'MS')

        if meas_errors:
            stab_circ.add_gate_at([i_ancilla], 'ImZ')
        stab_circ.add_gate_at([i_ancilla], 'MeasureZ')
        
        return stab_circ
        


    @classmethod
    def generate_one_stab_abstract(cls, stabilizer, n_total,
                                   i_ancilla, meas_errors=True,
                                   Is_after_two=False):
        '''
        '''
        stab_kind = stabilizer[0][0]    # 'X' or 'Z'
        stab_weight = len(stabilizer)

        stab_circ = Circuit()
        stab_circ.add_gate_at([i_ancilla], 'PrepareZPlus')
        
        if stab_kind == 'Z':
            for oper in stabilizer:
                stab_circ.add_gate_at([oper[1], i_ancilla], 'CX')
                if Is_after_two:
                    stab_circ.add_gate_at([oper[1]], 'I')
                    stab_circ.add_gate_at([i_ancilla], 'I')
                 
        elif stab_kind == 'X':
            stab_circ.add_gate_at([i_ancilla], 'H')
            for oper in stabilizer:
                stab_circ.add_gate_at([i_ancilla, oper[1]], 'CX')
                if Is_after_two:
                    stab_circ.add_gate_at([oper[1]], 'I')
                    stab_circ.add_gate_at([i_ancilla], 'I')
            stab_circ.add_gate_at([i_ancilla], 'H')

        if meas_errors:
            stab_circ.add_gate_at([i_ancilla], 'ImZ')
        stab_circ.add_gate_at([i_ancilla], 'MeasureZ')

        return stab_circ

   
 
    @classmethod
    def generate_stabs_meas(cls, stabilizer_list, ancillae_indexes,
                            input_I_round=False, meas_errors=True,
                            ion_trap=False, add_errors=False,
                            Is_after_2q=False, Is_after_1q=False,
                            MS_heating=False, Stark=False,
                            qubit_assignment=None, time_MS=None,
                            time_1q=None): 
        '''
        add_errors should only be True for debugging purposes.
        if ion_trap == True:  the circuit uses MS gates
        else:                 the circuit uses CXs and CZs.
        Is_after_2q:  whether or not to add I gates after 2-qubit gates.
        Is_after_1q:  whether or not to add I gates after 1-qubit gaets.
        This makes the addition of depolarizing Pauli noise easier.
        MS_heating:  whether or not we will include heating after MS gaets.
        Stark:  whether or not we will include Stark shifts.
        qubit_assignment:  a list of integers indicating the qubit to ion
                           assignment.  This is needed to calculate the 
                           duration of each MS gate.
        time_MS:  a function of the duration of the MS gate in terms of the
                  distance between the two ions.  Muyuan's fit of Luming's 
                  data.
        time_1q:  the duration of 1-qubit rotations in microseconds (float).
        '''
       
        n_data = 9
        n_stabs = len(stabilizer_list)
        n_steps = n_stabs/2
        if ion_trap:
            stab_func = Surface_Code_ion_trap.generate_one_stab_ion_trap
        else:
            stab_func = Surface_Code_ion_trap.generate_one_stab_abstract
            
        n_total = n_data + n_stabs
        
        stabs_circ = Circuit()
        if input_I_round:
            for i in range(n_data):
                stabs_circ.add_gate_at([i], 'I')
        
        #if add_errors:
            #stabs_circ.add_gate_at([3], 'Y')
            #new_g = stabs_circ.gates[0]
            #new_g.is_error = True      
            #stabs_circ.add_gate_at([1], 'X')
            #new_g = stabs_circ.gates[1]
            #new_g.is_error = True      
 
        gate_name = 'Two_parallel_stabilizers'
        for i in range(n_steps):
            circ1 = stab_func(stabilizer_list[2*i], n_total, 
                              ancillae_indexes[2*i],
                              meas_errors)
            #circ1.to_ancilla([ancillae_indexes[2*i]])
            circ2 = stab_func(stabilizer_list[2*i+1], n_total, 
                              ancillae_indexes[2*i+1],
                              meas_errors)
            #circ2.to_ancilla([ancillae_indexes[2*i+1]])
            circ1.join_circuit(circ2, True)
            circ1 = Surface_Code_ion_trap.insert_I_errors_to_circ(
                                            circ1, Is_after_2q, Is_after_1q, 
                                            MS_heating, Stark, qubit_assignment,
                                            time_MS, time_1q)
            #if i == 0:
            #    for g in circ1.gates:
            #        print g.gate_name, [q.qubit_id for q in g.qubits], g.duration

            two_stab_circ = Encoded_Gate(gate_name,[circ1]).circuit_wrap()
            stabs_circ.join_circuit(two_stab_circ, True)

            

        # if we set the last qubits to be ancillae at this point
        # we get an error.  Need to do it early.
        #stabs_circ.to_ancilla(range(n_data, n_total))

        #brow.from_circuit(stabs_circ, True)
        #sys.exit(0)        
        
        return stabs_circ
            


    @classmethod
    def generate_logical_state_surf17(cls, stabilizer_list, ancillae_indexes,
                                      logical_oper):
        '''
        Generates circuit to measure the stabilizers and the logical operator.
        '''

        stabs_circ = Surface_Code_ion_trap.generate_stabs_meas(stabilizer_list, 
                                                               ancillae_indexes)
        last_anc = max(ancillae_indexes) + 1
        log_circ = Circuit()
        log_circ.add_gate_at([last_anc], 'PrepareZPlus')
        log_circ.add_gate_at([last_anc], 'H')
        
        for oper in logical_oper:
            log_circ.add_gate_at([last_anc, oper[1]], 'C%s' %oper[0])
        
        log_circ.add_gate_at([last_anc], 'MeasureX')
        stabs_circ.join_circuit(log_circ, True)
        stabs_circ = stabs_circ.unpack()
        stabs_circ.to_ancilla(range(9,18))       
 
        return stabs_circ 
        
                                        
        


class Bare_Correct:
    '''
    Measure stabilizers with a bare ancilla for each stabilizer, no cat states.
    Class defined to implement Cross's [[7,1,3]] code.
    '''
    
    @classmethod
    def generate_bare_meas(cls, n_data, stabilizer_list, input_I_round=False, 
                           meas_errors=True, Is_after_two=False,
                           parallel=True, inputcirc=False):
        '''
        Generates stabilizer measurements with bare ancilla, no cat states.
        parallel = True means that we don't recicle the ancilla

        stabilizer_list is assumed to have the following format:
            [
              [('X',0), ('X',4)], ... 

            ]

        '''
        n_ancilla = len(stabilizer_list)
        bare_meas_circ = Circuit()
        if input_I_round:
            for i in range(n_data):
                bare_meas_circ.add_gate_at([i], 'I')

        if parallel:
            for i in range(n_data, n_data+n_ancilla):
	            bare_meas_circ.add_gate_at([i], 'PrepareXPlus')
        
            for i in range(len(stabilizer_list)):
                gateprefix = 'C'
                for gate in stabilizer_list[i]:
                    bare_meas_circ.add_gate_at([n_data+i,gate[1]], gateprefix+gate[0])
                    if Is_after_two:
                        bare_meas_circ.add_gate_at([gate[1]], 'I')
                        bare_meas_circ.add_gate_at([n_data+i], 'I')
        

            for i in range(n_data, n_data+n_ancilla):
                if meas_errors:
                    bare_meas_circ.add_gate_at([i], 'ImX')
                bare_meas_circ.add_gate_at([i], 'MeasureX')
                
            bare_meas_circ.to_ancilla(range(n_data, n_data+n_ancilla))

        else:
            pass

        return bare_meas_circ


    @classmethod
    def generate_rep_bare_meas(cls, n_data, stabilizer_list, n_rounds, input_I_round, 
                               meas_errors, Is_after_two_qubit, initial_trans=False,
                               ancilla_parallel=False):
        '''
        Is_after_two_qubits:  whether or not we want to add Is after 2-qubit gates,
                              to add errors on the Cross code.
        '''
        n = n_data
        n_ancilla = len(stabilizer_list)
        s_l = stabilizer_list[:]
        i_I = input_I_round
        m_e = meas_errors
        i_t = Is_after_two_qubit
        rep_meas_circ = Circuit()

        if initial_trans != False:
            for i in range(n_data):
                rep_meas_circ.add_gate_at([i], initial_trans)

        bare_meas_circ = Bare_Correct.generate_bare_meas

        for i in range(n_rounds):
            gate_name = 'Bare_Measurement_'+str(i+1)
            if i==0:
                stab_circ = Encoded_Gate(gate_name,[bare_meas_circ(n,s_l,i_I,m_e,i_t)]).circuit_wrap()
            else:
                stab_circ = Encoded_Gate(gate_name,[bare_meas_circ(n,s_l,False,m_e,i_t)]).circuit_wrap()
                
            rep_meas_circ.join_circuit(stab_circ, ancilla_parallel)
        
        rep_meas_circ = Encoded_Gate('EC_BareCorrect',
                        [rep_meas_circ]).circuit_wrap()

        #brow.from_circuit(rep_meas_circ, True)

        return rep_meas_circ



class Cat_Correct:
    '''
    Methods that employ Shor's ancilla to perform EC.
    ''' 

    @classmethod
    def cat_syndrome_4_old(cls, stabilizer_list, redundancy=1, 
            verify=False, ancilla_parallel=True):
        '''
        This method is not used anymore.
        '''
        
        #set method syndrome extraction
        if verify==True:
            cat_circ=Cat_Correct.create_4_cat_verify
            corr_circ=Cat_Correct.create_4_cat_verify_correction
        else:
            cat_circ=Cat_Correct.create_4_cat_no_verify
            corr_circ=Cat_Correct.create_4_cat_no_verify_correction
            
        #important constants
        n_data = len(stabilizer_list[0])
        n_stab = len(stabilizer_list)

        cat_synd_circ=Circuit()
        cat_corr_circ=Circuit()
        
        for i_stab,stabilizer in enumerate(stabilizer_list):
        
            # Redundancy is needed for fault tolearance of syndrome
            # measurments.
            
            redundancy_circ=Circuit()

            non_identity_index=[]
            for i_pauli,pauli in enumerate(stabilizer):
                if (pauli!='I'):
                    non_identity_index.append(i_pauli)
            
            for i_redund in range(redundancy):
                stab_circ=cat_circ(stabilizer)
                redundancy_circ.join_circuit_at(non_identity_index, 
                                stab_circ)
                
            cat_synd_circ.join_circuit(redundancy_circ, ancilla_parallel)

            cat_synd_circ = Encoded_Gate('EC_Cat4Syndrome',
                        [cat_synd_circ]).circuit_wrap()
            
            #cat_corr_circ = corr_circ(stabilizer)
            
            #cat_synd_circ.join_circuit_at(non_identity_index, cat_corr_circ)

        return cat_synd_circ
    


    @classmethod
    def cat_syndrome_4_test(cls, stabilizer_list, redundancy=1, 
            verify=False, ancilla_parallel=True,
            diVincenzo=True, initial_I=False):
        '''
        Method to be employed temporarily while we change all the 
        functions that used to call the cat_syndrome_4_test.
        '''

        return Cat_Correct.cat_syndrome_4(stabilizer_list, redundancy,
                                        verify, ancilla_parallel,
                                        diVincenzo, initial_I)    


    @classmethod
    def cat_syndrome_4(cls, stabilizer_list, redundancy=1, 
                        verify=False, ancilla_parallel=True,
                        diVincenzo=True, initial_I=False,
                        initial_trans=False, code='Steane',
                        meas_errors=True, Is_after_two=False):
        '''
        Method to do Shor's ancilla EC.
        The method is designed for a code with weight-4
        stabilizers.
        Right now, we have only implemented the Steane
        and 5-qubit codes.   
        It can be generalized to other codes.
        MGA 6/16/2016.
        '''     

        #set method syndrome extraction
        if verify==True:
            cat_circ=Cat_Correct.create_4_cat_verify
            corr_circ=Cat_Correct.create_4_cat_verify_correction
        else:
            if diVincenzo == True:
                cat_circ = Cat_Correct.create_4_cat_diVincenzo
            else:
                cat_circ=Cat_Correct.create_4_cat_no_verify
            corr_circ=Cat_Correct.create_4_cat_no_verify_correction
            
        #important constants
        n_data = len(stabilizer_list[0])
        n_stab = len(stabilizer_list)
        
        cat_synd_circ=Circuit()
        if initial_trans != False:
            for i in range(n_data):
                cat_synd_circ.add_gate_at([i], initial_trans)

        if code == 'Steane':

            if n_stab < 6:
                stabs = stabilizer_list[:]
                for i in range(redundancy):
                    stab_circ = Cat_Correct.create_4_cat_stabilizer(n_data, initial_I, 
                                                                    stabs, cat_circ, 
                                                                    'stabs_Steane_', 
                                                                    i+1, meas_errors,
                                                                    Is_after_two)
                    cat_synd_circ.join_circuit(stab_circ, ancilla_parallel)
                

            else:
                X_stabs = stabilizer_list[:3]
                Z_stabs = stabilizer_list[3:]
                for i in range(redundancy):
                    stab_circX = Cat_Correct.create_4_cat_stabilizer(n_data, initial_I, 
                                                                     X_stabs, cat_circ, 
                                                                    'X_stabs_Steane_', 
                                                                     i+1, meas_errors,
                                                                     Is_after_two)
                    cat_synd_circ.join_circuit(stab_circX, ancilla_parallel)
                    initial_I = False
                    stab_circZ = Cat_Correct.create_4_cat_stabilizer(n_data, initial_I, 
                                                                     Z_stabs, cat_circ, 
                                                                    'Z_stabs_Steane_', 
                                                                     i+1, meas_errors,
                                                                     Is_after_two)
                    cat_synd_circ.join_circuit(stab_circZ, ancilla_parallel)


        elif code == '5qubit':
            for i in range(redundancy):
                stab_circ = Cat_Correct.create_4_cat_stabilizer(n_data, initial_I, 
                                                                stabilizer_list[:], 
                                                                cat_circ, 
                                                               'stabs_5qubit_', 
                                                                i+1, meas_errors,
                                                                Is_after_two)
                cat_synd_circ.join_circuit(stab_circ, ancilla_parallel)
                initial_I = False
       
 
        cat_synd_circ = Encoded_Gate('EC_CatCorrect',
                        [cat_synd_circ]).circuit_wrap()

        return cat_synd_circ



    @classmethod
    def create_4_cat_stabilizer(cls, n_q, initial_I, stabs, cat_circ_method, 
				                gate_name, rep, meas_errors, Is_after_two):
        '''
        
        '''
        total_circ = Circuit()
        if initial_I:
            for i in range(n_q):
                total_circ.add_gate_at([i], 'I')
        for i_stab, stab in enumerate(stabs):
            non_iden_index = []
            for i_pauli, pauli in enumerate(stab):
                if pauli != 'I':
                    non_iden_index.append(i_pauli)
            stab_circ = cat_circ_method(stab, meas_errors, Is_after_two)
            total_circ.join_circuit_at(non_iden_index, stab_circ)            

        full_gate_name = gate_name + str(rep)
        total_circ = Encoded_Gate(full_gate_name, [total_circ]).circuit_wrap()
        
        return total_circ



    @classmethod
    def create_4_cat_verify(cls,stabilizer=['X','X','X','X']):
        """A helper method for creating a 4 qubit cat state and verify it.
        """
        cat_circuit = Circuit()
        for index in range(4,9):
            if index!=5:
                cat_circuit.add_gate_at([index],'PrepareZPlus')
            else:
                cat_circuit.add_gate_at([index],'PrepareXPlus')
        cat_circuit.add_gate_at([5,6],'CX')
        cat_circuit.add_gate_at([5,4],'CX')
        cat_circuit.add_gate_at([6,7],'CX')
        cat_circuit.add_gate_at([4,8],'CX')
        cat_circuit.add_gate_at([7,8],'CX')
        verify_gate = cat_circuit.add_gate_at([8],'MeasureZDestroy')
        
        final_gate = Verify_Gate(gate_name='4_cat_with_verify',
                                circuit_list=[cat_circuit])

        #create circuit with this final gate
        final_circ = Circuit()
        final_circ.add_gate_at(range(4,9),final_gate)
        
        non_identity_iter = 0
                
        for i_pauli,pauli in enumerate(stabilizer):
            if (pauli!='I'):
                gate_name = 'C' + pauli
                i1 = non_identity_iter+4
                final_circ.add_gate_at([i1+4, i1],gate_name)        
                non_identity_iter += 1

        if non_identity_iter>4:
            print ('Error!! stabilizer doesn\'t have four non-identity'+
                ' pauli operators.') 

        m_gates_cat=[]
        for i in range(4,8):
            m_gates_cat+=[final_circ.add_gate_at([i],'MeasureXDestroy')]
        
        final_circ.to_ancilla(range(4,9))

        return final_circ

    
    @classmethod    
    def create_4_cat_verify_correction(cls,stabilizer=['X','X','X','X']):
        #specify correction circuit
        corr_circ = Circuit()
        for i_pauli,pauli in enumerate(stabilizer):
            if (pauli!='I'):
                corr_circ.add_gate_at([i_pauli],pauli)
            
        #make correction gate
            
        corr_gate = Correction_Gate(gate_name='Cat_correction',
                circuit_list=[corr_circ])

        return corr_gate.circuit_wrap()
        
            
    @classmethod
    def create_4_cat_no_verify(cls,stabilizer):
        """A helper method for creating a 4 qubit cat state without a
        verification step. 
        
        This is specific for the Steane code, where the stabilizers contain
        either 4 X's or 4 Z's.  This could easily be generalized to other CSS
        codes.
        """     
        cat_circuit = Circuit()
        for index in range(4,8):
            if index==5:
                cat_circuit.add_gate_at([index],'PrepareXPlus')
            else:
                cat_circuit.add_gate_at([index],'PrepareZPlus')
        cat_circuit.add_gate_at([5,6],'CX')
        cat_circuit.add_gate_at([5,4],'CX')
        cat_circuit.add_gate_at([6,7],'CX')
                
        if stabilizer.count('X')==0:
            """Z stabilizers"""
            for index in range(4):
                cat_circuit.add_gate_at([index+4], 'H')
                cat_circuit.add_gate_at([index,index+4], 'CX')
        
        
        elif stabilizer.count('Z')==0:
            """X stabilizers"""
            for index in range(4):
                cat_circuit.add_gate_at([index+4,index], 'CX')

        m_gates_cat=[]
        

        if stabilizer.count('X')==0:
            """Z stabilizers"""
            for index in range(4,8):
                m_gates_cat += [cat_circuit.add_gate_at([index], 'MeasureZ')]

        elif stabilizer.count('Z')==0:
            """X stabilizers"""
            for index in range(4,8):
                m_gates_cat += [cat_circuit.add_gate_at([index], 'MeasureX')]


        cat_circuit.to_ancilla(range(4,8))

        return cat_circuit

    

    @classmethod
    def create_4_cat_diVincenzo(cls,stabilizer, meas_errors=True,
                                Is_after_two=False):
        """A helper method for creating a 4 qubit cat state without a
        verification step. 
        This is specific for a code where the stabilizers have weight 4.
        So far it's used for the Steane and the 5-qubit codes, but it
        is easily generalizable.
        if meas_errors == True: the measurements are faulty.
        if Is_after_two == True: we add I gates after 2-qubit gates.
                                 this is used on the ion_trap_simple
                                 error model.
        """ 
        cat_circuit = Circuit()
        for index in range(4,8):
            if index==5:
                cat_circuit.add_gate_at([index],'PrepareXPlus')
            else:
                cat_circuit.add_gate_at([index],'PrepareZPlus')
        cat_circuit.add_gate_at([5,6],'CX')
        if Is_after_two:
            cat_circuit.add_gate_at([5], 'I')
            cat_circuit.add_gate_at([6], 'I')
        cat_circuit.add_gate_at([5,4],'CX')
        if Is_after_two:
            cat_circuit.add_gate_at([5], 'I')
            cat_circuit.add_gate_at([4], 'I')
        cat_circuit.add_gate_at([6,7],'CX')
        if Is_after_two:
            cat_circuit.add_gate_at([6], 'I')
            cat_circuit.add_gate_at([7], 'I')
               
        #if stabilizer.count('X')==0:
        #    """Z stabilizers"""
        #    for index in range(4):
                #cat_circuit.add_gate_at([index+4], 'H')
                #cat_circuit.add_gate_at([index,index+4], 'CX')
        #        cat_circuit.add_gate_at([index+4,index], 'CZ')
            
        #elif stabilizer.count('Z')==0:
        #    """X stabilizers"""
        #    for index in range(4):
        #        cat_circuit.add_gate_at([index+4,index], 'CX')

        # More concise way to do the same thing: MGA 6/16/2016.
        index = 0
        for pauli in stabilizer:
            if pauli != 'I':
                cat_circuit.add_gate_at([index+4,index], 'C'+pauli)
                if Is_after_two:
                    cat_circuit.add_gate_at([index+4], 'I')
                    cat_circuit.add_gate_at([index], 'I')
                index += 1

        cat_circuit.add_gate_at([5,7], 'CX')
        if Is_after_two:
            cat_circuit.add_gate_at([5], 'I')
            cat_circuit.add_gate_at([7], 'I')
        cat_circuit.add_gate_at([6,4], 'CX')
        if Is_after_two:
            cat_circuit.add_gate_at([6], 'I')
            cat_circuit.add_gate_at([4], 'I')
        cat_circuit.add_gate_at([5,6], 'CX')    
        if Is_after_two:
            cat_circuit.add_gate_at([5], 'I')
            cat_circuit.add_gate_at([6], 'I')
        
        m_gates_cat=[]
        for index in range(4,8):
            if index == 5:
                if meas_errors:
                    cat_circuit.add_gate_at([index], 'ImX')
                m_gates_cat += [cat_circuit.add_gate_at([index], 'MeasureX')]
            else:
                if meas_errors:
                    cat_circuit.add_gate_at([index], 'ImZ')
                m_gates_cat += [cat_circuit.add_gate_at([index], 'MeasureZ')]   
            
        cat_circuit.to_ancilla(range(4,8))

        return cat_circuit

        
    
    @classmethod    
    def create_4_cat_no_verify_correction(cls,stabilizer=['X','X','X','X']):
        #specify correction circuit
        corr_circ = Circuit()
        for i_pauli,pauli in enumerate(stabilizer):
            if (pauli!='I'):
                corr_circ.add_gate_at([i_pauli],pauli)
            
        #make correction gate
            
        corr_gate = Correction_Gate(gate_name='Cat_correction',
                            circuit_list=[corr_circ])
        
        return corr_gate.circuit_wrap()
        
    @classmethod
    def create_cat_3(cls):
        """The great thing about three qubit cat states is that you don't have 
        to  verify them!--Dave Bacon"""
        cat_circuit = Circuit()
        for index in [0,2]:
            cat_circuit.add_gate_at([index],'PrepareZPlus')
        cat_circuit.add_gate_at([1],'PrepareXPlus')
        cat_circuit.add_gate_at([1,0],'CX')
        cat_circuit.add_gate_at([1,2],'CX')
        return cat_circuit
    
    @classmethod    
    def create_cat_n(cls, n):
        """Create a cat state on n qubits where n>3.
        """
        
        if n<=3:
            return 'Use a CNOT gate for n=2 or create_cat_3 for n=3.'
        
        circ = Circuit()
        for i in range(n):
            if not i == int(n/2):
                circ.add_gate_at([i],'PrepareZPlus')
            else:
                circ.add_gate_at([i],'PrepareXPlus')
                
        for i in range(n):
            if i < int(n/2):
                circ.add_gate_at([i+1,i],'CX')
            if i >= int(n/2):
                circ.add_gate_at([i,i+1],'CX')
                
        circ.add_gate_at([0,n],'CX')
        circ.add_gate_at([n-1,n],'CX')
        
        circ.add_gate_at([n],'MeasureZDestroy')

        #if MeasureZ gives -1, prepare again.

        gate = Prepare_Gate(gate_name=str(n)+' cat with verify', 
                            circuit_list = [circ])
        
        return gate.circuit_wrap()
        
#---------------#
#---------------#
        
class Steane_Correct:
    
    @classmethod
    def steane_syndrome(cls,ecc, redundancy =1, FT=True, kind='GFI'):
        """Steane syndrome measurement requires the creation of encoded zero and plus states in that code."""
        
        n_data = ecc.Code().block_size #number of data qubits in the code  
        n_ancilla = n_data #this code uses the same number of ancillas as data qubits
        # total data + ancilla qubits
        
        ###
        #Z syndrome
        ###
        
        #Create FT Encoded Zero
        synd_z_circ = Circuit()
        z_plus_circ, nothing = Steane_Correct.FT_encoded_zero_Steane()
        #brow.from_circuit(z_plus_circ, True)
        synd_z_circ.join_circuit_start_id(n_data,z_plus_circ)
        
        #kick phase down and measure    
        for i in range(n_data): 
            synd_z_circ.add_gate_at([n_data+i,i],'CX')
            synd_z_circ.add_gate_at([n_data+i],'MeasureX')
        
        synd_z_circ.to_ancilla(range(n_data, 2*n_data))
        synd_z_circ = Encoded_Gate('Steane_Syndrome_Z', [synd_z_circ]).circuit_wrap()
        
        #brow.from_circuit(synd_z_circ, True)
                
        ###
        #X syndrome
        ###
        
        #Create FT Encoded Plus
        synd_x_circ = Circuit()
        x_plus_circ, nothing = Steane_Correct.FT_encoded_plus_Steane()
        synd_x_circ.join_circuit_start_id(n_data,x_plus_circ)
        
        #Kick phase down and measure    
        for i in range(n_data): 
            synd_x_circ.add_gate_at([i,n_data+i],'CX')
            synd_x_circ.add_gate_at([n_data+i],'MeasureZ')
        
        synd_x_circ.to_ancilla(range(n_data,2*n_data))
        synd_x_circ = Encoded_Gate('Steane_Syndrome_X', [synd_x_circ]).circuit_wrap()
        
        #brow.from_circuit(synd_x_circ, True)
        
        main_circ = Circuit()
        main_circ.join_circuit(synd_z_circ)
        main_circ.join_circuit(synd_x_circ)
        
        return Container_Gate('EC_Steane_Correct',[main_circ]).circuit_wrap()

    @classmethod
    def encoded_zero_Steane(cls):
        """
        Creates an encoded zero for exclusive use in the 
        Steane[7,1,3] code
        """
        enc_zero = Circuit()
        for i in [0,1,3]:
            enc_zero.add_gate_at([i], 'PrepareXPlus')
        for i in [2,4,5,6]:
            enc_zero.add_gate_at([i], 'PrepareZPlus')
        cnots = [[0,2],[3,5],[1,6],[0,4],[3,6],[1,5],[0,6],[1,2],[3,4]]
        for i in cnots:
            enc_zero.add_gate_at(i, 'CX')
        return enc_zero



    @classmethod
    def encoded_plus_Steane(cls):
        """
        Creates an encoded plus for exclusive use in the 
        Steane[7,1,3] code.
        The Hadamard gate is transversal in the Steane code, so |+> is  
        almost identical to |0>; the only difference is the 
        CNOT's are flipped, |0>s are |+>s, and |+>s are |0>s.
        """
        enc_plus = Circuit()
        for i in [0,1,3]:
            enc_plus.add_gate_at([i], 'PrepareZPlus')
        for i in [2,4,5,6]:
            enc_plus.add_gate_at([i], 'PrepareXPlus')
        cnots = [[2,0],[5,3],[6,1],[4,0],[6,3],[5,1],[6,0],[2,1],[4,3]]
        for i in cnots:
            enc_plus.add_gate_at(i, 'CX')
        return enc_plus


    
    @classmethod
    def encoded_plus_i_Steane(cls):
        """
        Creates an encoded +i for exclusive use in the 
        Steane[7,1,3] code.
        It first creates a plus state and then applies a logical
        S gate.  S_L = S^t on each qubit.
        """
        enc_plus_i = cls.encoded_plus_Steane()
        for i in range(7):
            enc_plus_i.add_gate_at([i], 'Z')
            enc_plus_i.add_gate_at([i], 'P')
        return enc_plus_i

    

    @classmethod
    def FT_encoded_zero_Steane(cls, set_ancilla=True):
        circ1 = cls.encoded_zero_Steane()
        circ2 = cls.encoded_zero_Steane()
        circ1.join_circuit_at(range(7,14), circ2)

        meas_gates = []
        for i in range(7):
            circ1.add_gate_at([i,7+i], 'CX')
        for i in range(7):
            meas_gates += [circ1.add_gate_at([7+i], 'MeasureZDestroy')]
        
        if set_ancilla:  circ1.to_ancilla(range(7,14))
        
        return circ1, meas_gates

    
    
    @classmethod
    def FT_encoded_plus_Steane(cls, set_ancilla=True):
        circ1 = cls.encoded_plus_Steane()
        circ2 = cls.encoded_plus_Steane()
        circ1.join_circuit_at(range(7,14), circ2)

        #circ1.add_gate_at([0], 'Z')
        #circ1.add_gate_at([1], 'Z')
        meas_gates = []
        for i in range(7):
            circ1.add_gate_at([7+i,i], 'CX')
        for i in range(7):
            meas_gates += [circ1.add_gate_at([7+i], 'MeasureXDestroy')]
        
        if set_ancilla:  circ1.to_ancilla(range(7,14))
        
        return circ1, meas_gates
        


    @classmethod
    def detect_errors(cls, error_to_correct, n_data, initial_trans=False):
        '''
        very simple circuit to detect Z or X errors.
        It assumes the ancilla input is a FT logical |0> or |+> state
        '''
        circ = Circuit()
        m_gates = []
        # let's check this works:
        #if error_to_correct == 'X':
        #   circ.add_gate_at([0], 'X')
        #   circ.add_gate_at([1], 'X')

        if initial_trans != False:
            for i in range(n_data):
                circ.add_gate_at([i], initial_trans)

        if error_to_correct == 'X':
            for i in range(n_data):
                circ.add_gate_at([i, i+n_data], 'CX')
                m_gates += [circ.add_gate_at([i+n_data], 'MeasureZ')]
        elif error_to_correct == 'Z':
            for i in range(n_data):
                circ.add_gate_at([i+n_data, i], 'CX')
                m_gates += [circ.add_gate_at([i+n_data], 'MeasureX')]
        
        circ.to_ancilla(range(n_data, 2*n_data))

        return circ, m_gates


    @classmethod
    def steane_syndrome(cls, ancilla_parallel=False):
        """ 
        Steane syndrome measurement requires the creation of encoded zero and plus 
        states in that code.
        """
        
        #n_data = ecc.Code().block_size # number of data qubits in the code  
        
        n_data = 7                      # specific for the Steane code
        n_ancilla = n_data              # this code uses the same number of 
                                        # ancillas as data qubits

        ###
        #Z syndrome
        ###

        # create FT Encoded Zero
        synd_z_circ = Circuit()
        z_plus = Steane_Correct.FT_encoded_zero_Steane(False)[0]
        z_plus_circ = Encoded_Gate('Prepare_logical_Zero', [z_plus]).circuit_wrap()
        synd_z_circ.join_circuit_start_id(n_data, z_plus_circ)

        # kick phase down and measure    
        for i in range(n_data):
            synd_z_circ.add_gate_at([n_data+i,i],'CX')
            synd_z_circ.add_gate_at([n_data+i],'MeasureX')

        #synd_z_circ.to_ancilla(range(n_data, 2*n_data))
        synd_z_circ = Encoded_Gate('Steane_Syndrome_Z', [synd_z_circ]).circuit_wrap()

        ###
        #X syndrome
        ###

        # Create FT Encoded Plus
        synd_x_circ = Circuit()
        x_plus = Steane_Correct.FT_encoded_plus_Steane(False)[0]
        if ancilla_parallel:
            n_initial = n_data + 2*n_ancilla
        else:
            n_initial = n_data
        
        x_plus_circ = Encoded_Gate('Prepare_logical_Plus', [x_plus]).circuit_wrap()
        synd_x_circ.join_circuit_start_id(n_initial, x_plus_circ)

        # kick phase down and measure    
        for i in range(n_data):
            synd_x_circ.add_gate_at([i,n_initial+i],'CX')
            synd_x_circ.add_gate_at([n_initial+i],'MeasureZ')

        #synd_x_circ.to_ancilla(range(n_data, 2*n_data))
        synd_x_circ = Encoded_Gate('Steane_Syndrome_X', [synd_x_circ]).circuit_wrap()

        main_circ = Circuit()
        main_circ.join_circuit(synd_z_circ)
        main_circ.join_circuit(synd_x_circ)

        main_circ.to_ancilla(range(n_data, n_initial + 2*n_ancilla))

        steane_synd_circ = Encoded_Gate('EC_SteaneCorrect',[main_circ]).circuit_wrap()

        return steane_synd_circ


    @classmethod
    def steane_syndrome_old(cls, ecc, redundancy=1):
        """
        Steane syndrome measurement requires the creation of encoded zero
        and plus states. Currently we just assume that encoding is the Steane
        code. This can be expanded later.
        
        """
        
        n_data = ecc.Code().block_size  #number of data qubits in the code  
        n_anc = n_data                  # this code uses the same number of ancillas as  
                                        # total data + ancilla qubits will be 7+4*7=35
        
        main_circ=Circuit()
        
        
        ###
        #Z syndrome
        ###
        for i_redund in range(redundancy):

            # Create Encoded Zero and Verify
            enc_zero_circ, m_gates_enc_zero = cls.FT_encoded_zero_Steane()
            #gate = Verify_Gate(gate_name='Encoded Zero With Verify',
            #                   circuit_list=[enc_zero_circ])
            gate = Encoded_Gate(gate_name='FT_Encoded_Zero',
                                circuit_list=[enc_zero_circ])            

            synd_circ = gate.circuit_wrap()
            
            #(2) kick phase down and (3) measure Z
            
            synd_circ.replace_qubit_ids(range(n_data, n_data+2*n_anc))
            
            err_det_circ, m_gates_synd = cls.detect_errors('Z', n_data)
            synd_circ.join_circuit_at(range(n_data+n_anc), err_det_circ)
            synd_circ.to_ancilla(range(n_data,n_data+2*n_anc))
            main_circ.join_circuit_at(range(n_data), synd_circ)
            
        
        main_circ = Encoded_Gate('EC_SteaneSyndrome', [main_circ])
        
        corr_circ=Circuit()
        for i in range(7):
            corr_circ.add_gate_at([i],'Z')
        
        gate = Correction_Gate(gate_name='SteaneZ', circuit_list=[corr_circ])
        
        main_circ.join_circuit(gate.circuit_wrap())
                        
        ###
        #X syndrome
        ###
        for i_redund in range(redundancy):
            
            #Create Encoded Plus and Verify
            enc_plus_circ, m_gates_enc_plus = cls.FT_encoded_plus_Steane()
            gate = Verify_Gate(gate_name='Encoded Plus With Verify',
                    circuit_list=[enc_plus_circ])
            
            synd_circ = gate.circuit_wrap()
            
            #(2) kick phase down and (3) measure Z
            
            synd_circ.replace_qubit_ids(range(n_data, n_data+2*n_anc))
            
            err_det_circ, m_gates_synd = cls.detect_errors('X', n_data)
            synd_circ.join_circuit_at(range(n_data+n_anc), err_det_circ)
            synd_circ.to_ancilla(range(n_data,n_data+2*n_anc))
            main_circ.join_circuit_at(range(n_data), synd_circ)
            
            
        corr_circ=Circuit()
        for i in range(7):
            corr_circ.add_gate_at([i],'X')
                
        gate = Correction_Gate(gate_name='SteaneX', circuit_list=[corr_circ])

        main_circ.join_circuit(gate.circuit_wrap()) 
        
        return main_circ
        


class Knill_Correct:
    
    @classmethod
    def detect_errors(cls, n_data, order='normal', initial_trans=False):
        '''
        very simple circuit to detect errors.
        It assumes the input on the ancilla is a FT logical |+>
        and a FT logical |0>.
        It then prepares a logical Bell pair, applies the logical
        CNOT, and performs the logical X and Z measurements.
        
        if order == 'normal':     the circuit has data qubits on top and
                        logical Bell state at the bottom.
        elif order == 'reverse':  the other way around
        '''

        circ = Circuit()
        m_gates = []
        # let's check this works:
        #if error_to_correct == 'X':
        #   circ.add_gate_at([0], 'X')
        #   circ.add_gate_at([1], 'X')

        if order == 'normal':       
            # prepare the logical Bell pair
            for i in range(n_data):
                if initial_trans != False:
                    circ.add_gate_at([i], initial_trans)
                circ.add_gate_at([i+n_data, i+2*n_data], 'CX')
        
            # perform the logical CNOT and the measurements
            for i in range(n_data):
                circ.add_gate_at([i, i+n_data], 'CX')
                m_gates += [circ.add_gate_at([i], 'MeasureX')]
                m_gates += [circ.add_gate_at([i+n_data], 'MeasureZ')]

        elif order == 'reverse':
            # prepare the logical Bell pair
            for i in range(n_data):
                if initial_trans != False:
                    circ.add_gate_at([i+2*n_data], initial_trans)
                circ.add_gate_at([i+n_data, i], 'CX')
        
            # perform the logical CNOT and the measurements
            for i in range(n_data):
                circ.add_gate_at([i+2*n_data, i+n_data], 'CX')
                m_gates += [circ.add_gate_at([i+n_data], 'MeasureZ')]
                m_gates += [circ.add_gate_at([i+2*n_data], 'MeasureX')]

        circ.to_ancilla(range(n_data, 3*n_data))

        return circ, m_gates



    @classmethod
    def knill_syndrome(cls, ecc):
        '''
        '''
        n_data = 7
        n_ancilla = n_data
        bell_pair_circ = Circuit()
        
        # create FT encoded plus
        x_plus = Steane_Correct.FT_encoded_plus_Steane(False)[0]
        x_plus_circ = Encoded_Gate('Prepare_logical_Plus', [x_plus]).circuit_wrap()
        bell_pair_circ.join_circuit_start_id(n_data, x_plus_circ)
    
        # create FT encoded zero
        z_plus = Steane_Correct.FT_encoded_zero_Steane(False)[0]
        z_plus_circ = Encoded_Gate('Prepare_logical_Zero', [z_plus]).circuit_wrap()
        bell_pair_circ.join_circuit_start_id(n_data + 2*n_ancilla, z_plus_circ)
        
        # create Bell pair
        cnot = ecc.Generator.create_encoded_circuit('CX')
        cnot_circ = Encoded_Gate('logical_CX', [cnot]).circuit_wrap()
        cnot_qubits = range(n_data, n_data+n_ancilla) + \
                    range(n_data+2*n_ancilla, n_data+3*n_ancilla)
        bell_pair_circ.join_circuit_at(cnot_qubits, cnot_circ)
        
        bell_pair_circ = Encoded_Gate('Prepare_logical_Bell_pair', 
                                    [bell_pair_circ]).circuit_wrap()
        
    
        # couple to data and measure
        cnot = ecc.Generator.create_encoded_circuit('CX')
        cnot_circ = Encoded_Gate('logical_CX', [cnot]).circuit_wrap()
        cnot_qubits = range(n_data + n_ancilla)
        bell_pair_circ.join_circuit_at(cnot_qubits, cnot_circ)

        meas_X = ecc.Generator.create_encoded_circuit('MeasureXDestroy')
        meas_X_circ = Encoded_Gate('MeasureX', [meas_X]).circuit_wrap()
        meas_X_qubits = range(n_data)
        bell_pair_circ.join_circuit_at(meas_X_qubits, meas_X_circ)
        
        meas_Z = ecc.Generator.create_encoded_circuit('MeasureZDestroy')
        meas_Z_circ = Encoded_Gate('MeasureZ', [meas_X]).circuit_wrap()
        meas_Z_qubits = range(n_data, n_data + n_ancilla) 
        bell_pair_circ.join_circuit_at(meas_Z_qubits, meas_Z_circ)

        bell_pair_circ.to_ancilla(range(n_data, n_data + 4*n_ancilla))
        bell_pair_circ = Encoded_Gate('EC_KnillCorrect', [bell_pair_circ]).circuit_wrap()       

        return bell_pair_circ



class Aliferis_Cross_Correct:
    
    @classmethod
    def measure_T_operator(cls, data1, data2, ancilla, n=3, t='X'):
        """Measurement of two-qubit operator that results from the spliting of 
        a stabilizer. The label T comes from the original notation in Dave 
        Bacon's paper.
        """
        temp_anc = n**2
        T_meas = Circuit()
        if t == 'X':
            preparation = 'PrepareXPlus'
            control1, control2 = temp_anc, temp_anc
            target1, target2 = data1, data2
            measurement = 'MeasureXDestroy'
        else:
            preparation = 'PrepareZPlus'
            control1, control2 = data1, data2
            target1, target2 = temp_anc, temp_anc
            measurement = 'MeasureZDestroy'
        
        T_meas.add_gate_at([temp_anc], preparation)
        T_meas.add_gate_at([control1, target1], 'CX')
        T_meas.add_gate_at([control2, target2], 'CX')
        T_meas.add_gate_at([temp_anc], measurement)
        print T_meas.qubits()
        q = T_meas.qubits()[2]
        q.qubit_type = 'ancilla'
        q.qubit_id = ancilla
        T_meas.update_map()
                
        return T_meas


    @classmethod
    def measure_stabilizer(cls, first_data, second_data, first_ancilla, 
        n=3, t='X'):
        """
        Measurement of a stabilizer
        
        """
        Stabilizer_measurement = Circuit()

        for i in range(n):
            if t=='X':
                d1 = first_data*n + i
                d2 = second_data*n + i
            else:
                d1 = i*n + first_data
                d2 = i*n + second_data
            
            meas_op = Aliferis_Cross_Correct().measure_T_operator
            T_measure = meas_op(d1, d2, first_ancilla+i,n,t)
            T_gate = Encoded_Gate(gate_name='T_measure',
                                circuit_list=[T_measure])
            #T_gate = Correction_Gate(gate_name='T_measure', circuit_list=[T_measure])
            Stabilizer_measurement.add_gate(T_gate)
            
        return Stabilizer_measurement

    
    @classmethod
    def measure_all_stabilizers(cls, n=3):
        """
        Currently only implemented for the Bacon-Shor [9,1,3] code
        """
        
        All_stabilizers = Circuit()
        meas_stab = Aliferis_Cross_Correct().measure_stabilizer
        a = 0
        for t in ['X','Z']:
            for s in [[0,1],[0,2],[1,2]]:
                meas_stab = meas_stab(s[0],s[1],a,n,t)
                meas_stab_gate = Encoded_Gate(gate_name='stab_measurement',
                                            circuit_list=[meas_stab])
                All_stabilizers.add_gate(meas_stab_gate)
                a += n

        #for t in ['X','Z']:
        #   for i in range(n-1):
        #       meas_stab = Aliferis_Cross_Correct().measure_stabilizer(first=i, n=n, t=t)
        #       meas_stab_gate = Encoded_Gate(gate_name='stab_measurement', circuit_list=[meas_stab])
        #       All_stabilizers.add_gate(meas_stab_gate)
            
        #All_stabilizers.to_ancilla(range(n**2, n**2 + n))
        
        return All_stabilizers

        
        
