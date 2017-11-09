import sys
import os
import correction as corr
import chper_wrapper as wrapper
import qcircuit_functions as qfun
import qcircuit_wrapper as qcirc
import MC_functions as mc
from visualizer import browser_vis as brow


# chp location
n_code = 7
chp_loc = './chp_extended'
error_model = 'standard'
p1, p2, p_meas = 0.001, 0.001, 0.001  # these don't matter for the fast sampler
error_dict, Is_after2q, Is_after_1q = wrapper.dict_for_error_model(error_model, p1, p2, p_meas)
error_info = mc.read_error_info(error_dict)
default_one_q_errors_type = ['X','Y','Z']
default_two_q_errors_type = ['IX','IY','IZ',
                             'XI','XX','XY','XZ',
                             'YI','YX','YY','YZ',
                             'ZI','ZX','ZY','ZZ']


# create the initial state (|+> ctrl; |0> targ; all |0> anc)
init_state_ctrl = wrapper.prepare_stabs_Steane('+X')
init_state_targ = wrapper.prepare_stabs_Steane('+X')
init_state_anc = wrapper.prepare_stabs_Steane('+Z')
all_stabs = [init_state_ctrl[0]]+[init_state_targ[0]]+[init_state_anc[0]]
all_destabs = [init_state_ctrl[1]]+[init_state_targ[1]]+[init_state_anc[1]]
initial_state = qfun.combine_stabs(all_stabs, all_destabs)

# create circuit
#QEC_circ = corr.Flag_Correct.measure_XXlogical()
#CNOT_circ = corr.Flag_Correct.latt_surg_CNOT(True)
CNOT_circ = qfun.create_latt_surg_CNOT(False,True,True,False,True,True)
#brow.from_circuit(CNOT_circ, True)
#sys.exit(0)

# Get list of all 1-q and 2-q gates
one_q_gates, two_q_gates = wrapper.gates_list_CNOT(CNOT_circ, error_dict.keys())
#print one_q_gates
subset = (0,1)
one_q_errors_type = ['Y']

n_one_q_errors = subset[0]
n_two_q_errors = subset[1]

total_indexes, total_errors = qfun.get_total_indexes_one_circ(subset,
                                                              one_q_gates,
                                                              two_q_gates,
                                                              one_q_errors_type,
                                                              default_two_q_errors_type)
final_error_count, final_failure_count = 0, 0
#print total_errors[1170], total_indexes[1170]
#sys.exit(0)
#first_error_config = 1215
#first_error_config = 1293    # flag jointQECZ
#first_error_config = 2070    # weird error on old method.  WEIRD!
first_error_config = 2
for i in range(first_error_config,len(total_indexes)):
    print i
    print total_errors[i], total_indexes[i]
    CNOT_circ_copy = qfun.create_latt_surg_CNOT(False,True,True,False,True,True)
    qfun.add_specific_error_config_CNOT(CNOT_circ_copy, total_errors[i], total_indexes[i])
    brow.from_circuit(CNOT_circ_copy, True)
    sys.exit(0)

    QEC_object = qcirc.CNOT_latt_surg(initial_state, CNOT_circ_copy, 'Steane', chp_loc)
    QEC_object.run_all_gates()
    final_stabs, final_destabs = QEC_object.state[0][:], QEC_object.state[1][:]

    # Determine if there is an error (both failures and correctable errors)
    for stab in final_stabs:
        if stab[0] != '+':
            #print 'ERROR'
            final_error_count += 1
            break

    # do perfect EC on ctrl and target logical qubits
    corr_circ = qfun.create_EC_subcircs('Steane', False, False, False, True)
    corr_circ2 = qfun.create_EC_subcircs('Steane', False, False, False, True)
    corr_circ.join_circuit_at(range(n_code,2*n_code), corr_circ2)

    final_state = (final_stabs[:], final_destabs[:])
    bare_anc = True
    supra_circ = qcirc.CNOT_latt_surg(final_state, corr_circ, 'Steane', chp_loc, bare_anc)
    supra_circ.run_all_gates()
    corr_stabs = supra_circ.state[0]

    # Determine if failure has occured
    for stab in corr_stabs:
        if stab[0] != '+':
            final_failure_count += 1
            print 'ESTOY FEO'
            brow.from_circuit(CNOT_circ_copy, True)
            sys.exit(0)



#qfun.exhaustive_search_subset_latt_surg(subset, one_q_gates, two_q_gates,
#QEC_objecf = qcirc.CNOT_latt_surg(initial_state, CNOT_circ, 'Steane', chp_loc)
#QEC_object.run_all_gates()
#                                                           one_q_errors_type,
#                                                           default_two_q_errors_type)





QEC_object = qcirc.CNOT_latt_surg(initial_state, CNOT_circ, 'Steane', chp_loc)
QEC_object.run_all_gates()
#for stab in QEC_object.state[0]:
#    print stab
