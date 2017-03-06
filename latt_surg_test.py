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


# create the supra-circuit
Is_after2q = False
circuits = qfun.create_latt_surg_CNOT(Is_after2q)
#faulty_gate = circuits[0].gates[37]
#faulty_qubit = faulty_gate.qubits[1]
#new_g = circuits[0].insert_gate(faulty_gate, [faulty_qubit], '', 'Y', False)
#new_g.is_error = True
#brow.from_circuit(circuits, True)
#i = 0
#for supra_gate in circuits.gates:
#    i += 1
#    print 'gate', i
#    print supra_gate.gate_name
#sys.exit(0)

chp_loc = './chp_extended'

# create the initial state (|+> ctrl; |0> targ; all |0> anc)
init_state_ctrl = wrapper.prepare_stabs_Steane('+X')
init_state_targ = wrapper.prepare_stabs_Steane('+Z')
anc_stabs, anc_destabs = [], []
for i in range(n_code):
    anc_stab = ['Z' if i==j else 'I' for j in range(n_code)]
    anc_stab.insert(0, '+')
    anc_destab = ['X' if i==j else 'I' for j in range(n_code)]
    anc_destab.insert(0, '+')
    anc_stabs += [''.join(anc_stab)]
    anc_destabs += [''.join(anc_destab)]
init_state_anc = anc_stabs, anc_destabs
init_state_anc = wrapper.prepare_stabs_Steane('+Z')


all_stabs = [init_state_ctrl[0]]+[init_state_targ[0]]+[init_state_anc[0]]
all_destabs = [init_state_ctrl[1]]+[init_state_targ[1]]+[init_state_anc[1]]
init_state = qfun.combine_stabs(all_stabs, all_destabs)

supra_circ = qcirc.CNOT_latt_surg(init_state, circuits, code, chp_loc)
supra_circ.run_all_gates()

final_stabs = supra_circ.state[0][:]
final_destabs = supra_circ.state[1][:]

corr_circ = qfun.create_EC_subcircs(code, False, False, False, True)
bare_anc = True
supra_circ = qcirc.Supra_Circuit((final_stabs, final_destabs),
                                  corr_circ,
                                  'Steane',
                                  chp_loc,
                                  bare_anc)
print 'Hola'
supra_circ.run_one_oper(supra_circ.quant_opers[0])
