import sys
import os
import time
import copy
import json
import d5color
import itertools as it
import multiprocessing as mp
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
default_two_q_errors_type = ['IX','IY','IZ',
                             'XI','XX','XY','XZ',
                             'YI','YX','YY','YZ',
                             'ZI','ZX','ZY','ZZ']


n_per_proc, n_proc = int(sys.argv[1]), int(sys.argv[2])
n_errors = [int(sys.argv[3]), int(sys.argv[4])]
QEC_kind = sys.argv[5]   # either 'color' or 'surface49'



QEC_circ = cor.Flag_Correct.generate_whole_QEC_circ(4, d5_stabs, flags_list+flags_list,
                                                True, False, 17, True, False, True)
QEC_circ_list = []
for log_gate in QEC_circ.gates:
    for gate in log_gate.circuit_list[0].gates:
        QEC_circ_list += [gate.circuit_list[0]]

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

X_stabs, X_destabs = d5color.Code.stabilizer_CHP_X[:], d5color.Code.destabilizer_CHP_X[:]
Z_stabs, Z_destabs = qfun.change_operators(X_stabs)[:], qfun.change_operators(X_destabs)[:]
init_state = [Z_stabs, Z_destabs]


def run_QEC_d5(init_state, QEC_circ_list, code='color'):
    '''
    '''
    #if code == 'color':
    QEC_object = qwrap.QEC_with_flags(init_state, QEC_circ_list[:], chp_loc)
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
    corr_circ = cor.Flag_Correct.generate_whole_QEC_circ(4, d5_stabs, flags_list+flags_list,
                                                True, False, 17, True, False, True)
    corr_circ_list = []
    for log_gate in corr_circ.gates:
        for gate in log_gate.circuit_list[0].gates:
            corr_circ_list += [gate.circuit_list[0]]
    
    corr_object = qwrap.QEC_with_flags([final_stabs[:], final_destabs[:]],
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




def exhaustive_search_subset(subset, one_q_gates, two_q_gates,
                             one_q_errors_type=['X'],
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


    print len(total_errors)
    
    final_error_count, final_failure_count = 0, 0
    for i in range(len(total_indexes)):
        #print total_indexes[i]
        #print total_errors[i]
        
        QEC_circ_list_copy = []
        for subcirc in QEC_circ_list:
            QEC_circ_list_copy += [copy.deepcopy(subcirc)]

        faulty_circ_list = wrapper.add_specific_error_configuration(QEC_circ_list_copy,
                                                                    total_errors[i],
                                                                    total_indexes[i])
        #brow.from_circuit(faulty_circ_list[0], True)
        #time.sleep(5)

        final_error, fail, n_supra = run_QEC_d5(init_state, faulty_circ_list)
        if final_error:
            final_error_count += 1
        if fail:
            final_failure_count += 1
            print 'FAIL!'
            sys.exit(0)

    return final_error_count, final_failure_count



def run_several_QEC_fast(error_info, n_runs_total, init_state, QEC_circ_list):
    '''
    '''
    did_run = 0
    n_final_errors = 0
    n_fails = 0
    n_supra_gates = 0
    even_supra, odd_supra = 0, 0
    even_supra8, odd_supra8 = 0, 0

    for n_run in xrange(n_runs_total):

        # I just realized it's more efficient to copy the circuit list
        # only if we decide to run the circuit.
        # Instead, we perform the copying process in add_errors...
        #QEC_circ_list_copy = []
        #for subcirc in QEC_circ_list:
        #    QEC_circ_list_copy += [copy.deepcopy(subcirc)]

        # Add the errors and decide to run (in this case we'll always run)
        errors_dict, carry_run, faulty_circs = wrapper.add_errors_fast_sampler_color(
                                                                [one_q_gates, two_q_gates],
                                                                n_errors,
                                                                QEC_circ_list,
                                                                error_info)


        if not carry_run:
            n_supra_gates += 32
            even_supra8 += 2
            even_supra += 14

        else:
            # Run
            did_run += 1
            final_error, fail, supra_local = run_QEC_d5(init_state, faulty_circs)
            n_supra_gates += len(supra_local)
            for num in supra_local:
                if num%16 == 0:
                    even_supra8 += 1
                elif num%16 == 1:
                    odd_supra8 += 1
                elif num%2 == 0:
                    even_supra += 1
                else:
                    odd_supra += 1

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
                


    return n_final_errors, n_fails, n_supra_gates, even_supra, odd_supra, even_supra8, odd_supra8, did_run



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



#print run_several_QEC_fast(error_info, 50000, init_state, QEC_circ_list)
#sys.exit(0)
out_list = run_parallel_QEC(error_info, n_per_proc, n_proc, init_state,
                            QEC_circ_list)
n_total = n_per_proc*n_proc
n_final_errors = sum([event[0] for event in out_list])
n_fail = sum([event[1] for event in out_list])
n_supra_gates = sum([event[2] for event in out_list])
n_even_gates = sum([event[3] for event in out_list])
n_odd_gates = sum([event[4] for event in out_list])
n_even8_gates = sum([event[5] for event in out_list])
n_odd8_gates = sum([event[6] for event in out_list])
n_run = sum([event[7] for event in out_list])

n_twoq_gates = n_even8_gates*n_2q_gates[0] + n_odd8_gates*n_2q_gates[1] + n_even_gates*n_2q_gates[2] + n_odd_gates*n_2q_gates[3]
n_oneq_gates = n_even8_gates*n_1q_gates[0] + n_odd8_gates*n_1q_gates[1] + n_even_gates*n_1q_gates[2] + n_odd_gates*n_1q_gates[3]
n_meas_gates = n_even8_gates*n_meas[0] + n_odd8_gates*n_meas[1] + n_even_gates*n_meas[2] + n_odd_gates*n_meas[3]

n_correctable = n_final_errors - n_fail
p_correctable = float(n_correctable)/float(n_total)
p_fail = float(n_fail)/float(n_total)
p_supra_gates = float(n_supra_gates)/float(n_total)
p_even_supra = float(n_even_gates)/float(n_total)
p_odd_supra = float(n_odd_gates)/float(n_total)
p_even8_supra = float(n_even8_gates)/float(n_total)
p_odd8_supra = float(n_odd8_gates)/float(n_total)
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
            'p_even_supra': p_even_supra,
            'p_odd_supra': p_odd_supra,
            'p_even8_supra': p_even8_supra,
            'p_odd8_supra': p_odd8_supra,
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
