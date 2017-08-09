import sys
import os
import json
import multiprocessing as mp
import surface49 as surf49
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
output_folder = './MC_results/QECd5_surface49/' + error_model + '/'

n_per_proc, n_proc = int(sys.argv[1]), int(sys.argv[2])
n_errors = [int(sys.argv[3]), int(sys.argv[4])]
QEC_kind = sys.argv[5]   # either 'color' or 'surface49'


n_qubits = 25
initial_I = True
surface49_stabs = surf49.Code.stabilizers[:]
QEC_circ = cor.Bare_Correct.generate_rep_bare_meas(25, surface49_stabs, 4, initial_I, True,
                                                   Is_after2q, False, False, True)
#brow.from_circuit(QEC_circ, True)
QEC_circ_list = []
for supra_gate in QEC_circ.gates:
    QEC_circ_list += [supra_gate.circuit_list[0]]
#brow.from_circuit(QEC_circ_list[1])


# Define the list of error-prone 1-q and 2-q gates
one_q_gates, two_q_gates = wrapper.gates_list(QEC_circ_list, error_dict.keys())

# Define the number of all the 2-q gates, 1-q gates, and measurements
# for resource counting purposes
n_2q_gates, n_1q_gates, n_meas = [], [], []
for subcirc in QEC_circ_list:
    two_q, one_q, meas = 0, 0, 0
    for phys_gate in subcirc.gates:
        if len(phys_gate.qubits) > 1:
            two_q += 1
        else:
            if phys_gate.gate_name[0] != 'I':
                one_q += 1
            if phys_gate.gate_name[:4] == 'Meas':
                meas += 1
    n_2q_gates += [two_q]
    n_1q_gates += [one_q]
    n_meas += [meas]

#print n_2q_gates
#print n_1q_gates
#print n_meas


# Initial state: we start with the product state |000...0> and
# measure the X stabilizers
init_kind = 'Z'
prod_state = list(qfun.initial_product_state(n_qubits, init_kind))
init_object = qwrap.QEC_d5(prod_state[:], QEC_circ_list[:], chp_loc)
#syndromes, error_det, data_error_det = QEC_object.run_one_bare_anc_new(0, 'surface49', 'X', 0)
#print syndromes
#print error_det
#print data_error_det
list_indices = init_object.run_QEC_d5()
init_state = [init_object.stabs[:], init_object.destabs[:]]



def run_QEC_d5(init_state, QEC_circ_list, code='surface49'):
    '''
    '''
    #for stab in init_state[0]:
    #    if stab[0] != '+':  print 'PROBLEMS!!!!'
    #if code == 'color':
    QEC_object = qwrap.QEC_d5(init_state, QEC_circ_list[:], chp_loc)
    n_supra_gates = QEC_object.run_QEC_d5()
     
    final_stabs, final_destabs = QEC_object.stabs[:], QEC_object.destabs[:]

    # Determine if there is an error (both failures and correctable errors)
    final_error = False
    for stab in final_stabs:
        if stab[0] != '+':
            final_error = True
            break

    # Do perfect EC
    #if code == 'color':
    corr_circ = cor.Bare_Correct.generate_rep_bare_meas(25, surface49_stabs, 4, initial_I, True,
                                                   Is_after2q, False, False, True)
    corr_circ_list = []
    for supra_gate in QEC_circ.gates:
       corr_circ_list += [supra_gate.circuit_list[0]]
    
    corr_object = qwrap.QEC_d5([final_stabs[:], final_destabs[:]],
                               corr_circ_list,
                               chp_loc)
    # Number of gates here "don't matta"
    dm = corr_object.run_QEC_d5()
    corr_stabs = corr_object.stabs[:]

    # Determine if a failure has occured.
    fail = False
    for stab in corr_stabs:
        if stab[0] != '+':
            fail = True
            break

    return final_error, fail, n_supra_gates



def run_several_QEC_fast(error_info, n_runs_total, init_state, QEC_circ_list):
    '''
    '''
    did_run = 0
    n_final_errors = 0
    n_fails = 0
    n_supra_gates = 0

    for n_run in xrange(n_runs_total):

        # I just realized it's more efficient to copy the circuit list
        # only if we decide to run the circuit.
        # Instead, we perform the copying process in add_errors...
        #QEC_circ_list_copy = []
        #for subcirc in QEC_circ_list:
        #    QEC_circ_list_copy += [copy.deepcopy(subcirc)]

        # Add the errors and decide to run (in this case we'll always run)
        errors_dict, carry_run, faulty_circs = wrapper.add_errors_fast_sampler_new(
                                                                [one_q_gates, two_q_gates],
                                                                n_errors,
                                                                QEC_circ_list,
                                                                error_info)


        if not carry_run:
            n_supra_gates += 2
            #even_supra8 += 2
            #even_supra += 14

        else:
            # Run
            did_run += 1
            final_error, fail, supra_local = run_QEC_d5(init_state, faulty_circs)
            n_supra_gates += len(supra_local)

            if final_error:
                n_final_errors += 1
            if fail:
                n_fails += 1
                print 'Selected 1q gates =', errors_dict[0]
                print 'Selected 2q gates =', errors_dict[1]
                print supra_local
                for faulty_circ in faulty_circs:
                    for gate in faulty_circ.gates:
                        if gate.is_error:
                            print gate.gate_name, gate.qubits
                

    return n_final_errors, n_fails, n_supra_gates, did_run



def run_parallel_QEC(error_info, n_runs_per_proc, n_proc, init_state, QEC_circ_list):
    '''
    '''
    sim_func = run_several_QEC_fast
    pool = mp.Pool()
    results = [pool.apply_async(sim_func, (error_info, n_runs_per_proc,
                                           init_state, QEC_circ_list))
                            for proc in range(n_proc)]
    pool.close()
    pool.join()
    dicts = [r.get() for r in results]

    return dicts


out_list = run_parallel_QEC(error_info, n_per_proc, n_proc, init_state,
                            QEC_circ_list)
n_total = n_per_proc*n_proc
n_final_errors = sum([event[0] for event in out_list])
n_fail = sum([event[1] for event in out_list])
n_supra_gates = sum([event[2] for event in out_list])
n_run = sum([event[3] for event in out_list])

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
p_run = float(n_run)/float(n_total)
out_dict = {'n_total': n_total,
            'n_correctable': n_correctable,
            'p_correctable': p_correctable,
            'n_fail': n_fail,
            'p_fail': p_fail,
            'n_supra_gates': n_supra_gates,
            'p_supra_gates': p_supra_gates,
            'p_2q': p_2q_gates,
            'p_1q': p_1q_gates,
            'p_meas': p_meas,
            'n_run': n_run,
            'p_run': p_run}

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

json_filename = str(n_errors[0]) + '_' + str(n_errors[1]) + '.json'
abs_filename = output_folder + json_filename
json_file = open(abs_filename, 'w')
json.dump(out_dict, json_file, indent=4, separators=(',', ':'), sort_keys=True)
json_file.close()

