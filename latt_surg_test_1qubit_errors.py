import sys
import qcircuit_wrapper as qcirc
import chper_wrapper as wrapper
import qcircuit_functions as qfun
import cross
from visualizer import browser_vis as brow


# code parameters
oper = 'Shor'
code = 'Steane'
n_code = 7
bare = False
chp_loc = './chp_extended'


# create the supra-circuit
Is_after2q = False
CNOT_circuits = qfun.create_latt_surg_CNOT(Is_after2q)
#faulty_gate = circuits[0].gates[37]
#faulty_qubit = faulty_gate.qubits[1]
#new_g = circuits[0].insert_gate(faulty_gate, [faulty_qubit], '', 'Y', False)
#new_g.is_error = True
brow.from_circuit(CNOT_circuits, True)
#i = 0
#for supra_gate in circuits.gates:
#    i += 1
#    print 'gate', i
#    print supra_gate.gate_name
sys.exit(0)

# create the initial state (|+> ctrl; |0> targ; all |0> anc)
init_state_ctrl = wrapper.prepare_stabs_Steane('+Z')
init_state_targ = wrapper.prepare_stabs_Steane('+Z')
init_state_anc = wrapper.prepare_stabs_Steane('+Z')
#anc_stabs, anc_destabs = [], []
#for i in range(n_code):
#    anc_stab = ['Z' if i==j else 'I' for j in range(n_code)]
#    anc_stab.insert(0, '+')
#    anc_destab = ['X' if i==j else 'I' for j in range(n_code)]
#    anc_destab.insert(0, '+')
#    anc_stabs += [''.join(anc_stab)]
#    anc_destabs += [''.join(anc_destab)]
#init_state_anc = anc_stabs, anc_destabs

all_stabs = [init_state_ctrl[0]]+[init_state_targ[0]]+[init_state_anc[0]]
all_destabs = [init_state_ctrl[1]]+[init_state_targ[1]]+[init_state_anc[1]]
initial_state = qfun.combine_stabs(all_stabs, all_destabs)


def run_latt_surg_circ(init_state, circuits):

    supra_circ = qcirc.CNOT_latt_surg(init_state, circuits, code, chp_loc)
    supra_circ.run_all_gates()

    final_stabs = supra_circ.state[0][:]
    final_destabs = supra_circ.state[1][:]

    # do perfect EC on ctrl and target logical qubits
    corr_circ = qfun.create_EC_subcircs(code, False, False, False, True)
    corr_circ2 = qfun.create_EC_subcircs(code, False, False, False, True)
    corr_circ.join_circuit_at(range(n_code,2*n_code), corr_circ2)
    
    final_state = (final_stabs, final_destabs)
    bare_anc = True
    supra_circ = qcirc.CNOT_latt_surg(final_state,
                                      corr_circ,
                                      code,
                                      chp_loc,
                                      bare_anc)
    supra_circ.run_all_gates()
    
    corr_stabs = supra_circ.state[0]

    # Determine if a failure has occurred
    fail = False
    for stab in corr_stabs:
        if stab[0] == '-':  
            fail = True
            break
    
    return fail




for supra_gate in CNOT_circuits.gates:
    #if supra_gate.gate_name == 'Logical_I':
    if True:
        supra_i = CNOT_circuits.gates.index(supra_gate)
        print 'Supra index =', supra_i
        in_gates = supra_gate.circuit_list[0].gates
        
        for faulty_gate in in_gates:
            if faulty_gate.gate_name != 'I':  continue
            in_i = in_gates.index(faulty_gate)
            print 'Inside index =', in_i
            
            #for Pauli_error in ['Z']:
            for Pauli_error in ['X', 'Y', 'Z']:
                clean_circuits = qfun.create_latt_surg_CNOT(Is_after2q)
                clean_faulty_g = clean_circuits.gates[supra_i].circuit_list[0].gates[in_i]
                clean_faulty_q = clean_faulty_g.qubits[0]
                print 'Error =', Pauli_error, clean_faulty_q.qubit_id

                #if clean_faulty_q.qubit_id in range(7,14):
                if True:    
                    error_g = clean_circuits.gates[supra_i].circuit_list[0].insert_gate(clean_faulty_g,
                                                                                    [clean_faulty_q],
                                                                                    '',
                                                                                    Pauli_error,
                                                                                    False)
                    error_g.is_error = True

                init_state_copy = initial_state[0][:], initial_state[1][:]
                #brow.from_circuit(clean_circuits, True)
                fail = run_latt_surg_circ(init_state_copy, clean_circuits)

                if fail:
                    print 'FAIL'
                    print supra_i
                    print in_i
                    sys.exit(0)

                #sys.exit(0)


    
