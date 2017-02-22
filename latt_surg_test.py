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
#sys.exit(0)

chp_loc = './chp_extended'

# create the initial state (|+> ctrl; |0> targ; all |0> anc)
init_state_ctrl = wrapper.prepare_stabs_Steane('+X')
init_state_targ = wrapper.prepare_stabs_Steane('+X')
anc_stabs, anc_destabs = [], []
for i in range(n_code):
    anc_stab = ['Z' if i==j else 'I' for j in range(n_code)]
    anc_stab.insert(0, '+')
    anc_destab = ['X' if i==j else 'I' for j in range(n_code)]
    anc_destab.insert(0, '+')
    anc_stabs += [''.join(anc_stab)]
    anc_destabs += [''.join(anc_destab)]
init_state_anc = anc_stabs, anc_destabs

all_stabs = [init_state_ctrl[0]]+[init_state_targ[0]]+[init_state_anc[0]]
all_destabs = [init_state_ctrl[1]]+[init_state_targ[1]]+[init_state_anc[1]]
init_state = qfun.combine_stabs(all_stabs, all_destabs)

supra_circ = qcirc.CNOT_latt_surg(init_state, circuits, code, chp_loc)
supra_circ.run_all_gates()

