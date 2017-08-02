import sys
import time
import d5color
import itertools as it
import correction as cor
import chper_wrapper as wrapper
import MC_functions as mc
import qcircuit_functions as qfun
import qcircuit_wrapper as qwrap
from visualizer import browser_vis as brow

#circ = qfun.create_EC_subcircs('d5color', False, True, False, False, 5)
chp_loc = './chp_extended'
d5_stabs = d5color.Code.stabilizer_alt[:]
d5_stab_oct = d5_stabs[8]
flags_oct = [[1,6], [2,7]]
flags_sq = [[1,3]]
flags_list = [flags_oct] + [flags_sq for i in range(7)]
n_flags = [len(flags) for flags in flags_list]

error_model = 'standard'
p1, p2, p_meas = 0.001, 0.001, 0.001  # these don't matter for the fast sampler
error_dict, Is_after2q, Is_after_1q = wrapper.dict_for_error_model(error_model, p1, p2, p_meas)
error_info = mc.read_error_info(error_dict)
output_folder = './MC_results/QECd5_flags/' + error_model + '/'

#circ = cor.Flag_Correct.generate_one_flagged_stab(17, d5_stab_oct, flags, True, True)
#circ = cor.Flag_Correct.generate_all_flagged_stabs(d5_stabs[:8], flags_list, True,
#                                                   False, 17)
QEC_circ = cor.Flag_Correct.generate_whole_QEC_circ(5, d5_stabs, flags_list+flags_list,
                                                True, False, 17, True, False, True)
#brow.from_circuit(QEC_circ.gates[0].circuit_list[0], True)
#brow.from_circuit(QEC_circ, True)
#sys.exit(0)
QEC_circ_list = []
for log_gate in QEC_circ.gates:
    for gate in log_gate.circuit_list[0].gates:
        QEC_circ_list += [gate.circuit_list[0]]
#print len(QEC_circ_list)

one_q_gates, two_q_gates = wrapper.gates_list(QEC_circ_list, error_dict.keys())
one_q_gates0, two_q_gates0 = [], []
for one_q in one_q_gates:
    if one_q[0] == 0:
        one_q_gates0 += [one_q[1]]
for two_q in two_q_gates:
    if two_q[0] == 0:
        two_q_gates0 += [two_q[1]]

#print one_q_gates0
#print two_q_gates0
#print two_q_gates
#for i,g in enumerate(QEC_circ_list[0].gates):
#    print i, g.gate_name
#sys.exit(0)

#add_errors_after_gates(QEC_circ_list[0], [0,3,101], ['X','XX','X'])
#brow.from_circuit(QEC_circ_list[0], True)
#sys.exit(0)

# Define initial flags and initial state
first_flags = ((0,0),0,0,0,0,0,0,0)
X_stabs, X_destabs = d5color.Code.stabilizer_CHP_X[:], d5color.Code.destabilizer_CHP_X[:]
Z_stabs, Z_destabs = qfun.change_operators(X_stabs)[:], qfun.change_operators(X_destabs)[:]
init_state = [Z_stabs, Z_destabs]

QEC_circ_list = wrapper.add_specific_error_configuration(QEC_circ_list,
                                                         ['Y'],
                                                         [(0,2)])
brow.from_circuit(QEC_circ_list[0], True)
QEC_object = qwrap.QEC_with_flags(init_state, QEC_circ_list[:], chp_loc)
print QEC_object.run_one_type_stabilizers_high_indet_d5(0, first_flags, first_flags, 0)
sys.exit(0)

#out_dict = QEC_flags.run_one_roundCSS(0, first_flags, n_flags)

def exhaustive_search_subset(subset, one_q_gates, two_q_gates):
    '''
    '''
    n_one_q_errors = subset[0]
    n_two_q_errors = subset[1]
    one_q_errors_type = ['X']
    two_q_errors_type = ['IX', 'XI', 'XX']

    total_indexes, total_errors = qfun.get_total_indexes_one_circ(subset,
                                                                  one_q_gates,
                                                                  two_q_gates,
                                                                  one_q_errors_type,
                                                                  two_q_errors_type)


    for i in range(len(total_indexes)):
        print total_indexes[i]
        print total_errors[i]
        

        QEC_circ = cor.Flag_Correct.generate_whole_QEC_circ(5, d5_stabs, 
                                                            flags_list+flags_list,
                                                            True, False, 17)
        QEC_circ_list = []
        for log_gate in QEC_circ.gates:
            QEC_circ_list += [log_gate.circuit_list[0]]

        qfun.add_errors_after_gates(QEC_circ_list[0], total_indexes[i], total_errors[i])
        init_state = [Z_stabs, Z_destabs]
        QEC_flags = qwrap.QEC_with_flags(init_state, QEC_circ_list[:], chp_loc)
        output = QEC_flags.run_first_round_d5(init_state, QEC_circ_list)
        brow.from_circuit(QEC_circ_list[0], True)
        time.sleep(10)
        #sys.exit(0)
        corrX, flags_outcomesX, corrZ, flags_outcomesZ = output
        if corrX.count(1) != 0:
            raise ValueError('There should not be a Z error.')
        corr_oper = ['X' if num==1 else 'I' for num in corrZ]
        print corr_oper
        final_stabs, final_destabs = QEC_flags.stabs[:], QEC_flags.destabs[:]
        #print final_stabs
        corr_state = qfun.update_stabs(final_stabs, final_destabs, corr_oper)
        corr_stabs, corr_destabs = corr_state[0][:], corr_state[1][:]
       
        #print corr_stabs

        fail = False
        for stab in corr_stabs:
            if stab[0] != '+':
                fail = True
                print 'FAIL'
                sys.exit(0)

        #sys.exit(0)


exhaustive_search_subset((1,1), one_q_gates0, two_q_gates0)
sys.exit(0)
#print one_q_gates0
print two_q_gates0
for i in range(len(list_indexes)):
    print list_indexes[i], list_errors[i]
sys.exit(0)

add_errors_after_gates(QEC_circ_list[0], [0,3,101], ['X','XX','X'])


#add_errors_after_gates(QEC_circ_list[0], [0,3,101], ['X','XX','X'])
