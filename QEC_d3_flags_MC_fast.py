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

n_per_proc, n_proc = int(sys.argv[1]), int(sys.argv[2])
n_errors = [int(sys.argv[3]), int(sys.argv[4])]
QEC_kind = sys.argv[5]   # either 'flag' or 'diVin'

if QEC_kind == 'flag':
    output_folder = './MC_results/QECd3_flags/one_flag/' + error_model + '/'
elif QEC_kind == 'diVin':
    output_folder = './MC_results/QECd3_diVin/' + error_model + '/'
elif QEC_kind == 'diVin_new':
    output_folder = './MC_results/QECd3_diVin_new/' + error_model + '/'



# Obtain the number of 1-qubit and 2-qubit gates in the whole circuit
initial_I = True
if QEC_kind == 'flag':
    QEC_circ = cor.Flag_Correct.generate_whole_QEC_Reichardt_special(True, False, initial_I)
elif QEC_kind == 'diVin':
    QEC_circ = qfun.create_EC_subcircs('Steane', False, initial_I, False)
    QEC_circ = QEC_circ.gates[0].circuit_list[0]
elif QEC_kind == 'diVin_new':
    QEC_circ = qfun.create_EC_subcircs('Steane', False, initial_I, False, False, 2)
    QEC_circ = QEC_circ.gates[0].circuit_list[0]
    
    n_2q_gates, n_1q_gates, n_meas = [], [], []
    for i_supra in range(len(QEC_circ.gates)):
        two_q, one_q, meas = 0, 0, 0
        all_gates = QEC_circ.gates[i_supra].circuit_list[0].gates
        for gate in all_gates:
            if len(gate.qubits) > 1:
                two_q += 1
            else:
                if gate.gate_name[0] != 'I':
                    one_q += 1
                if gate.gate_name[:4] == 'Meas':
                    meas += 1
        
        n_2q_gates += [two_q]
        n_1q_gates += [one_q]
        n_meas += [meas]


QEC_circ_list = []
for i in range(len(QEC_circ.gates)):
    QEC_circ_list += [QEC_circ.gates[i].circuit_list[0]]
one_q_gates, two_q_gates = wrapper.gates_list(QEC_circ_list, error_dict.keys())


# Define initial state
state = '+Z'
init_stabs = steane.Code.stabilizer_logical_CHP[state][:]
init_destabs = steane.Code.destabilizer_logical_CHP[state][:]
init_state = [init_stabs, init_destabs]



def run_QEC_d3(init_state, QEC_circ_list, kind='flag'):
    '''
    kind: 'flag' or 'diVin'
    '''

    if kind=='flag':
        QEC_object = qwrap.QEC_with_flags(init_state, QEC_circ_list[:], chp_loc)
        QEC_object.run_all_Reichardt_d3(init_state)

    elif kind=='diVin':
        QEC_object = qwrap.QEC_d3(init_state, QEC_circ_list[:], chp_loc)
        n_X, n_Z = QEC_object.run_fullQEC_CSS('Steane', False)

    elif kind=='diVin_new':
        QEC_object = qwrap.QEC_d3(init_state, QEC_circ_list[:], chp_loc)
        n_X, n_Z = QEC_object.run_fullQEC_CSS('Steane', False, False)


    
    final_stabs, final_destabs = QEC_object.stabs[:], QEC_object.destabs[:]
    
    # Determine if there is an error (both failures and correctable errors)
    final_error = False
    for stab in final_stabs:
        if stab[0] != '+':
            final_error = True
            break

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
    
    return final_error, fail, n_X, n_Z




def run_several_QEC_fast(error_info, n_runs_total, init_state, QEC_kind):
    '''
    '''

    did_run = 0
    n_final_errors = 0
    n_fails = 0
    n_supra_gates = 0

    for n_run in xrange(n_runs_total):

        if QEC_kind == 'flag':

            fraction_of_circ = 4
            # create the supra-circuit and insert gates
            QEC_circ = cor.Flag_Correct.generate_whole_QEC_Reichardt_special(True,
                                                                             False,
                                                                             initial_I)

        elif QEC_kind == 'diVin':

            fraction_of_circ = 3
            # create the supra-circuit and insert gates
            QEC_circ = qfun.create_EC_subcircs('Steane', False, initial_I, False)
            QEC_circ = QEC_circ.gates[0].circuit_list[0]
            
        elif QEC_kind == 'diVin_new':

            fraction_of_circ = 4
            # create the supra-circuit and insert gates
            QEC_circ = qfun.create_EC_subcircs('Steane', False, initial_I, False, False, 2)
            QEC_circ = QEC_circ.gates[0].circuit_list[0]
            


        QEC_circ_list = []
        for log_gate in QEC_circ.gates:
            QEC_circ_list += [log_gate.circuit_list[0]]
        
        
        
        # Add the errors and decide to run
        errors_dict, carry_run, faulty_circs = wrapper.add_errors_fast_sampler_new(
                                                        [one_q_gates, two_q_gates],
                                                        n_errors,
                                                        QEC_circ_list,
                                                        error_info,
                                                        fraction_of_circ)

        # Run
        if carry_run:
            did_run += 1
            final_error, fail, n_X, n_Z = run_QEC_d3(init_state, faulty_circs, QEC_kind)
            n_supra_gates += sum([n_X, n_Z])
            if final_error:
                n_final_errors += 1
            if fail:  
                n_fails += 1
                #print errors_dict
                #for key in errors_dict:
                #    if errors_dict[key] != {}:
                #        brow.from_circuit(faulty_circs[key], True)
                #break

        else:
            n_supra_gates += 2*len(QEC_circ_list)/fraction_of_circ


    return n_final_errors, n_fails, n_supra_gates



def run_parallel_QEC(error_info, n_runs_per_proc, n_proc, init_state, QEC_kind):
    '''
    '''
    sim_func = run_several_QEC_fast
    pool = mp.Pool()
    results = [pool.apply_async(sim_func, (error_info, n_runs_per_proc, 
                                           init_state, QEC_kind))
                    for proc in range(n_proc)]
    pool.close()
    pool.join()
    dicts = [r.get() for r in results]

    return dicts



#print run_several_QEC_fast(error_info, 100, init_state, QEC_kind)
out_list = run_parallel_QEC(error_info, n_per_proc, n_proc, init_state, QEC_kind)
n_total = n_per_proc*n_proc

n_final_errors = sum([event[0] for event in out_list])
n_fail = sum([event[1] for event in out_list])
n_supra_gates = sum([event[2] for event in out_list])
n_twoq_gates = n_supra_gates*n_2q_gates[0]
n_oneq_gates = n_supra_gates*n_1q_gates[0]
n_meas_gates = n_supra_gates*n_meas[0]

n_correctable = n_final_errors - n_fail
p_correctable = float(n_correctable)/float(n_total)
p_fail = float(n_fail)/float(n_total)
p_supra_gates = float(n_supra_gates)/float(n_total)
p_2q_gates = float(n_twoq_gates)/float(n_total)
p_1q_gates = float(n_oneq_gates)/float(n_total)
p_meas = float(n_meas_gates)/float(n_total)
out_dict = {'n_total': n_total, 
            'n_correctable': n_correctable,
            'p_correctable': p_correctable,
            'n_fail': n_fail, 
            'p_fail': p_fail,
            'n_supra_gates': n_supra_gates,
            'p_supra_gates': p_supra_gates,
            'p_2q': p_2q_gates,
            'p_1q': p_1q_gates,
            'p_meas': p_meas}
print out_dict
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

json_filename = str(n_errors[0]) + '_' + str(n_errors[1]) + '.json'
abs_filename = output_folder + json_filename
json_file = open(abs_filename, 'w')
json.dump(out_dict, json_file, indent=4, separators=(',', ':'), sort_keys=True)
json_file.close()




