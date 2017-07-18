import sys
import os
import json
import random as rd
import multiprocessing as mp
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
output_folder = './MC_results/QECd3_flags/one_flag/' + error_model + '/'

n_per_proc, n_proc = int(sys.argv[1]), int(sys.argv[2])
n_errors = [int(sys.argv[3]), int(sys.argv[4])]

        
state = '+Z'
init_stabs = steane.Code.stabilizer_logical_CHP[state][:]
init_destabs = steane.Code.destabilizer_logical_CHP[state][:]
init_state = [init_stabs, init_destabs]

def run_QEC_d3(init_state, QEC_circ_list):
    
    QEC_flags = qwrap.QEC_with_flags(init_state, QEC_circ_list[:], chp_loc)
    QEC_flags.run_all_Reichardt_d3(init_state)
    #print QEC_flags.stabs

    final_stabs = QEC_flags.stabs[:]
    final_destabs = QEC_flags.destabs[:]
    
    # do perfect EC
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
    
    return fail




def gates_QEC_d3(QEC_circ, faulty_gates_names):
    '''
    improvised function to calculate the indices for 1-qubit and 2-qubit gates
    '''
    
    single_q_gates, two_q_gates = [], []
    for i in range(len(QEC_circ.gates)):
        supra_gate = QEC_circ.gates[i]
        for j in range(len(supra_gate.circuit_list[0].gates)):
            in_gate = supra_gate.circuit_list[0].gates[j]
            if in_gate.gate_name in faulty_gates_names:
                if len(in_gate.qubits) == 1:
                    single_q_gates.append((i,j))
                elif len(in_gate.qubits) == 2:
                    two_q_gates.append((i,j))

    return single_q_gates, two_q_gates


initial_I = True
Reich_circ = cor.Flag_Correct.generate_whole_QEC_Reichardt_special(True, False, initial_I)
#brow.from_circuit(Reich_circ, True)
one_q_gates, two_q_gates = gates_QEC_d3(Reich_circ, error_dict.keys())


def run_several_QEC_flags_fast(error_info, n_runs_total, init_state):
    '''
    '''

    did_run = 0
    n_fails = 0
    for n_run in xrange(n_runs_total):
        # create the supra-circuit and insert gates
        Reich_circ = cor.Flag_Correct.generate_whole_QEC_Reichardt_special(True,
                                                                           False,
                                                                           initial_I)
        QEC_circ_list = []
        for log_gate in Reich_circ.gates:
            QEC_circ_list += [log_gate.circuit_list[0]]
        
        # Add the errors and decide to run
        errors_dict, carry_run, faulty_circs = wrapper.add_errors_fast_sampler_Reich(
                                                    [one_q_gates, two_q_gates],
                                                    n_errors,
                                                    QEC_circ_list,
                                                    error_info)
        #for key in errors_dict:
        #    if errors_dict[key] != {}:
        #        brow.from_circuit(faulty_circs[key], True)
        #print errors_dict

        # Run
        if carry_run:
            did_run += 1
            fail = run_QEC_d3(init_state, faulty_circs)
            if fail:  
                n_fails += 1
                #print errors_dict
                #for key in errors_dict:
                #    if errors_dict[key] != {}:
                #        brow.from_circuit(faulty_circs[key], True)
                #break

    return n_fails


def run_parallel_Reich(error_info, n_runs_per_proc, n_proc, init_state):
    '''
    '''
    sim_func = run_several_QEC_flags_fast
    pool = mp.Pool()
    results = [pool.apply_async(sim_func, (error_info, n_runs_per_proc, init_state))
                    for proc in range(n_proc)]
    pool.close()
    pool.join()
    dicts = [r.get() for r in results]

    return dicts


out_list = run_parallel_Reich(error_info, n_per_proc, n_proc, init_state)
n_total = n_per_proc*n_proc
n_fail = sum(out_list)
p_fail = float(n_fail)/float(n_total)
out_dict = {'n_total': n_total, 'n_fail': n_fail, 'p_fail': p_fail}
print out_dict
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

json_filename = str(n_errors[0]) + '_' + str(n_errors[1]) + '.json'
abs_filename = output_folder + json_filename
json_file = open(abs_filename, 'w')
json.dump(out_dict, json_file, indent=4, separators=(',', ':'), sort_keys=True)
json_file.close()




