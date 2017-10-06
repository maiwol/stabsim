import sys
import os
import steane as st
import qcircuit_functions as qfun
import qcircuit_wrapper as qcirc
import chper_wrapper as wrapper
from visualizer import browser_vis as brow

chp_loc = './chp_extended'
code = 'Steane'

# create the initial state (|+> ctrl; |0> targ; all |0> anc)
init_state_ctrl = wrapper.prepare_stabs_Steane('+X')
init_state_targ = wrapper.prepare_stabs_Steane('+Z')
all_stabs = [init_state_ctrl[0]]+[init_state_targ[0]]
all_destabs = [init_state_ctrl[1]]+[init_state_targ[1]]
init_state = qfun.combine_stabs(all_stabs, all_destabs)


# create the circuit
CNOT_circ = st.Generator.transversal_CNOT_ion_trap(False, True)
#brow.from_circuit(CNOT_circ, True)

CNOT_object = qcirc.Supra_Circuit(init_state, CNOT_circ, code, chp_loc)
CNOT_gate = CNOT_circ.gates[0]
print CNOT_object.state[0]
out_dict = CNOT_object.run_one_oper(CNOT_gate)
print CNOT_object.state[0]
