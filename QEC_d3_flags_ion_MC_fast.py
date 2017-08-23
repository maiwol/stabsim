import sys
import os
import steane
import correction as cor
from visualizer import browser_vis as brow
import chper_wrapper as wrapper
import qcircuit_functions as qfun
import qcircuit_wrapper as qwrap


chp_loc = './chp_extended'
error_model = 'ion_trap_eQual'
# These error rates don't matter for the fast sampler
p1, p2, p_meas, p_prep, p_sm, p_cool = 0.1, 0.1, 0.1, 0.1, 0.1, 0.1 
error_dict, Is_after2q, Is_after1q, faulty_groups = wrapper.dict_for_error_model(
                                                         error_model=error_model,
                                                         p_1q=p1, p_2q=p2,
                                                         p_meas=p_meas, p_prep=p_prep,
                                                         p_sm=p_sm, p_cool=p_cool)
n_per_proc, n_proc = int(sys.argv[1]), int(sys.argv[2])
n_errors = [int(sys.argv[3]), int(sys.argv[4])]
alternating = sys.argv[5]   # either 'True' or 'False'

if alternating == 'True':
    alternating = True
    output_folder = './MC_results/QECd3_flags/all_flags/ion_trap1/alternating/'
else:
    alternating = False
    output_folder = './MC_results/QECd3_flags/all_flags/ion_trap1/non_alternating/'



# Define the circuit and the circuit_list
i_first_anc = 7
stabs = steane.Code.stabilizer_alt
if alternating:
    stabs = [stabs[0], stabs[3], stabs[1], stabs[4], stabs[2], stabs[5]]
meas_errors = True
initial_I = True
dephasing_during_MS = True
QEC_circ = cor.Flag_Correct.generate_whole_QEC_d3_ion(stabs, 
                                                      meas_errors,
                                                      initial_I,
                                                      dephasing_during_MS)
#brow.from_circuit(QEC_circ, True)
QEC_circ_list = []
for log_gate in QEC_circ.gates:
    QEC_circ_list += [log_gate.circuit_list[0]]

# Define the list of error-prone gates
# For now, we have 4 groups: (a) preps and meas, (b) shuttling and merging
# (c) cooling, and (d) MS gates.
prep_meas_g, shut_g, cool_g, MS_g = wrapper.gates_list_general(QEC_circ_list, faulty_groups)


# Define the number of all the 2-q gates, 1-q gates, and measurements
# for resource counting purposes
n_2q_gates, n_1q_gates, n_meas, n_5q_gates = [], [], [], []
#n_Ism, n_Icool = [], []
for subcirc in QEC_circ_list:
    two_q, one_q, meas, five_q = 0, 0, 0, 0
    Ism, Icool = 0, 0
    for phys_gate in subcirc.gates:
        if len(phys_gate.qubits) == 5:
            # trick used because the for each ISM5,
            # there are really 2 5-qubit MS gates
            five_q += 2
        elif len(phys_gate.qubits) == 2:
            if phys_gate.gate_name[0] != 'C':
                two_q += 1
        else:
            if phys_gate.gate_name[0] != 'I':
                one_q += 1
            if phys_gate.gate_name[:4] == 'Meas':
                meas += 1
            #elif phys_gate.gate_name == 'Ism':
            #    Ism += 1
            #elif phys_gate.gate_name == 'Icool':
            #    Icool += 1
    n_5q_gates += [five_q]
    n_2q_gates += [two_q]
    n_1q_gates += [one_q]
    n_meas += [meas]
    #n_Ism += [Ism]
    #n_Icool += [Icool]


# Define initial state
state = '+Z'
init_stabs = steane.Code.stabilizer_logical_CHP[state][:]
init_stabs[0] = '-' + init_stabs[0][1:]
#init_stabs[3] = '-' + init_stabs[3][1:]
init_destabs = steane.Code.destabilizer_logical_CHP[state][:]
init_state = [init_stabs, init_destabs]
print init_stabs


def run_QEC_d3(init_state, QEC_circ_list, chp_loc, alternating):
    '''
    '''

    QEC_object = qwrap.QEC_with_flags(init_state, QEC_circ_list[:], chp_loc)
    supra_gates = QEC_object.run_stabilizers_high_indet_ion(0, alternating)

    final_stabs, final_destabs = QEC_object.stabs[:], QEC_object.destabs[:]

    # Determine if there is an error (both failures and correctable errors)
    final_error = False
    for stab in final_stabs:
        if stab[0] != '+':
            final_error = True
            break

    # Do perfect EC on the final state
    corr_circ = qfun.create_EC_subcircs('Steane', False, False, False, True)
    final_state = (final_stabs, final_destabs)
    bare_anc = True
    supra_circ = qwrap.CNOT_latt_surg(final_state, corr_circ, 'Steane', chp_loc, bare_anc)
    supra_circ.run_all_gates()
    corr_stabs = supra_circ.state[0]

    # Determine if a failure has occured.
    fail = False
    for stab in corr_stabs:
        if stab[0] != '+':
            fail = True
            break

    return final_error, fail, supra_gates


# Run the circuit
print run_QEC_d3(init_state, QEC_circ_list[:], chp_loc, alternating)
