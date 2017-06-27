import sys
import steane
import correction as cor
import chper_wrapper as wrapper
import MC_functions as mc
import qcircuit_functions as qfun
import qcircuit_wrapper as qwrap
from visualizer import browser_vis as brow


chp_loc = './chp_extended'
error_model = 'standard'
p1, p2, p_meas = 0.001, 0.001, 0.001  # these don't matter for the fast sampler
error_dict, Is_after2q, Is_after_1q = wrapper.dict_for_error_model(error_model, p1, p2, p_meas)
error_info = mc.read_error_info(error_dict)
output_folder = './MC_results/QECd3_flags/' + error_model + '/'

#Reich_circ = cor.Flag_Correct.generate_Reichardt_d3_1_flag(False, False, 'X')
Reich_circ = cor.Flag_Correct.generate_whole_QEC_Reichardt(True, False, 3)
#brow.from_circuit(Reich_circ, True)

QEC_circ_list = []
for log_gate in Reich_circ.gates:
    QEC_circ_list += [log_gate.circuit_list[0]]
    
one_q_gates, two_q_gates = wrapper.gates_list(QEC_circ_list, error_dict.keys())
one_q_gates0, two_q_gates0 = [], []
for one_q in one_q_gates:
    if one_q[0] == 0:
        one_q_gates0 += [one_q[1]]
for two_q in two_q_gates:
    if two_q[0] == 0:
        two_q_gates0 += [two_q[1]]

state = '+Z'
init_stabs = steane.Code.stabilizer_logical_CHP[state][:]
init_destabs = steane.Code.destabilizer_logical_CHP[state][:]



def exhaustive_search_subset_circ0(subset, one_q_gates, two_q_gates,
                                   one_q_errors_type=['Z'],
                                   two_q_errors_type=['IX','XI','XX']):
    '''
    '''

    n_one_q_errors = subset[0]
    n_two_q_errors = subset[1]

    total_indexes, total_errors = qfun.get_total_indexes_one_circ(subset,
                                                                  one_q_gates,
                                                                  two_q_gates,
                                                                  one_q_errors_type,
                                                                  two_q_errors_type)

    for i in range(len(total_indexes)):
        print total_indexes[i]
        print total_errors[i]

        QEC_circ = cor.Flag_Correct.generate_whole_QEC_Reichardt(True, Is_after2q, 3)
        QEC_circ_list = []
        for log_gate in QEC_circ.gates:
            QEC_circ_list += [log_gate.circuit_list[0]]

        qfun.add_errors_after_gates(QEC_circ_list[0], total_indexes[i], total_errors[i])
        #if total_indexes[i][0] == 9:
        #    brow.from_circuit(QEC_circ_list[0], True)
        init_state = [init_stabs, init_destabs]
        QEC_flags = qwrap.QEC_with_flags(init_state, QEC_circ_list[:], chp_loc)
        QEC_flags.run_one_round_Reichardt_d3(0, 0)
        

exhaustive_search_subset_circ0((1,0), one_q_gates0, two_q_gates0)
