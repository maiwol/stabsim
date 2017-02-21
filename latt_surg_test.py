import sys
import qcircuit_wrapper as qcirc
import chper_wrapper as wrapper
import qcircuit_functions as qfun
import cross
from visualizer import browser_vis as brow



oper = 'Shor'
code = 'Steane'
n_code = 7
bare = False


s1=['+ZII', '+IZI', '-IIZ']
s2=['+XIII', '+IXII', '-IIXI', '+IIIZ']
s3=['+ZII', '+IZI', '-IIZ']

print qfun.combine_stabs([s1, s2, s3], [s1, s2, s3])
sys.exit(0)

Is_after2q = False
#circuits = wrapper.create_EC_subcircs(oper, Is_after2q)
circuits = qfun.create_latt_surg_CNOT(Is_after2q)
#faulty_gate = circuits[0].gates[37]
#faulty_qubit = faulty_gate.qubits[1]
#new_g = circuits[0].insert_gate(faulty_gate, [faulty_qubit], '', 'Y', False)
#new_g.is_error = True
#brow.from_circuit(circuits, True)
#sys.exit(0)

chp_loc = './chp_extended'

init_state_ctrl = wrapper.prepare_stabs_Steane('+X')
init_state_targ = wrapper.prepare_stabs_Steane('+Z')
print init_state_ctrl
sys.exit(0)

stabs, destabs = [], []
for i in range(3*n_code):
    stab = ['Z' if i==j else 'I' for j in range(3*n_code)]
    stab.insert(0, '+')
    destab = ['X' if i==j else 'I' for j in range(3*n_code)]
    destab.insert(0, '+')
    stabs += [''.join(stab)]
    destabs += [''.join(destab)]

init_state = stabs, destabs

for g in circuits.gates:
    print g.gate_name
    subcirc = g.circuit_list[0]
    for sub_g in subcirc.gates:
        print sub_g.gate_name
sys.exit(0)

#q_oper = qcirc.Quantum_Operation(init_state, circuits, chp_loc)
#dic = q_oper.run_one_circ(0)

q_oper = qcirc.QEC_d3(init_state, circuits, chp_loc)
#data_errors = q_oper.run_one_bare_anc(0, oper)
#data_errors = q_oper.run_one_diVincenzo(0, code, 'X')
n_rep = q_oper.run_fullQEC_nonCSS(code, bare)
#n_rep = q_oper.run_fullQEC_CSS(code, bare)

print n_rep
