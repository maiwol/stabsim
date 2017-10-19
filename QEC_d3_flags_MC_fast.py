import sys
import os
import time
import json
import copy
import random as rd
import multiprocessing as mp
import steane
import surface17 as surf17
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

if QEC_kind == 'surface17':
    output_folder = './MC_results/QECd3_surface17/' + error_model + '/' 
elif QEC_kind == 'all_flags':
    output_folder = './MC_results/QECd3_flags/all_flags/' + error_model + '/' 
elif QEC_kind == 'flag':
    output_folder = './MC_results/QECd3_flags/one_flag/' + error_model + '/'
elif QEC_kind == 'diVin':
    output_folder = './MC_results/QECd3_diVin/' + error_model + '/'
elif QEC_kind == 'diVin_new':
    output_folder = './MC_results/QECd3_diVin_new/' + error_model + '/'



# Define the circuit and the circuit_list
initial_I = True
if QEC_kind == 'surface17':
    surface17_stabs = surf17.Code.stabilizers[:]
    QEC_circ = cor.Bare_Correct.generate_rep_bare_meas(9, surface17_stabs, 2, initial_I, True,
                                                       Is_after2q, False, False, True)
    QEC_circ_list = []
    for supra_gate in QEC_circ.gates:
        QEC_circ_list += [supra_gate.circuit_list[0]]

elif QEC_kind == 'all_flags':
    steane_stabs = steane.Code.stabilizer_alt[:]
    flags_sq = [[1,3]]
    flags_list = [flags_sq for i in range(3)]
    QEC_circ = cor.Flag_Correct.generate_whole_QEC_circ(2, steane_stabs, flags_list+flags_list,
                                                        True, Is_after2q, 7, initial_I, False,
                                                        True)
    QEC_circ_list = []
    for supra_gate in QEC_circ.gates:
        for gate in supra_gate.circuit_list[0].gates:
            QEC_circ_list += [gate.circuit_list[0]]

elif QEC_kind == 'flag':
    QEC_circ = cor.Flag_Correct.generate_whole_QEC_Reichardt_special(True, False, initial_I)

elif QEC_kind == 'diVin':
    QEC_circ = qfun.create_EC_subcircs('Steane', False, initial_I, False)
    QEC_circ = QEC_circ.gates[0].circuit_list[0]

elif QEC_kind == 'diVin_new':
    QEC_circ = qfun.create_EC_subcircs('Steane', False, initial_I, False, False, 2)
    QEC_circ = QEC_circ.gates[0].circuit_list[0]
    QEC_circ_list = []
    for i in range(len(QEC_circ.gates)):
        QEC_circ_list += [QEC_circ.gates[i].circuit_list[0]]


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

# Define initial state
if QEC_kind == 'surface17':
    state = '+Z'
    init_stabs = surf17.Code.stabilizer_CHP[:]
    init_destabs = surf17.Code.destabilizer_CHP[:]
    init_state = [init_stabs, init_destabs]
else:
    state = '+Z'
    init_stabs = steane.Code.stabilizer_logical_CHP[state][:]
    init_destabs = steane.Code.destabilizer_logical_CHP[state][:]
    init_state = [init_stabs, init_destabs]


#QEC_circ_list = wrapper.add_specific_error_configuration(QEC_circ_list,
#                                                         ['Y'],
#                                                         [(0,3)])
#brow.from_circuit(QEC_circ_list[0], True)
#QEC_object = qwrap.QEC_d3(init_state, QEC_circ_list[:], chp_loc)
#print QEC_object.run_fullQEC_CSS('surface17', True, False)
#sys.exit(0)


def run_QEC_d3(init_state, QEC_circ_list, kind='flag'):
    '''
    kind: 'flag' or 'diVin'
    '''
    if kind=='surface17':
        QEC_object = qwrap.QEC_d3(init_state, QEC_circ_list[:], chp_loc)
        n_X, n_Z = QEC_object.run_fullQEC_CSS_d3('surface17', True, False)
        n_supra_gates = n_X + n_Z

    elif kind=='all_flags':
        QEC_object = qwrap.QEC_with_flags(init_state, QEC_circ_list[:], chp_loc)
        # In this case, n_supra_gates is not an integer.  It's a list of run subcircs.
        n_supra_gates = QEC_object.run_Reichardt_d3_one_flag_stab('cheap', 'any')

    elif kind=='flag':
        QEC_object = qwrap.QEC_with_flags(init_state, QEC_circ_list[:], chp_loc)
        QEC_object.run_all_Reichardt_d3(init_state)

    elif kind=='diVin':
        QEC_object = qwrap.QEC_d3(init_state, QEC_circ_list[:], chp_loc)
        n_X, n_Z = QEC_object.run_fullQEC_CSS('Steane', False)
        n_supra_gates = n_X + n_Z

    elif kind=='diVin_new':
        QEC_object = qwrap.QEC_d3(init_state, QEC_circ_list[:], chp_loc)
        n_X, n_Z = QEC_object.run_fullQEC_CSS('Steane', False, False)
        n_supra_gates = n_X + n_Z

    
    final_stabs, final_destabs = QEC_object.stabs[:], QEC_object.destabs[:]
    
    # Determine if there is an error (both failures and correctable errors)
    final_error = False
    for stab in final_stabs:
        if stab[0] != '+':
            final_error = True
            break

    # do perfect EC
    if kind=='surface17':
        surface17_stabs = surf17.Code.stabilizers[:]
        corr_circ = cor.Bare_Correct.generate_rep_bare_meas(9, surface17_stabs, 2, False, True,
                                                            False, False, False, True)
        corr_circ_list = []
        for supra_gate in corr_circ.gates:
            corr_circ_list += [supra_gate.circuit_list[0]]
        corr_object = qwrap.QEC_d3([final_stabs[:],final_destabs[:]], corr_circ_list[:], chp_loc) 
        # don't matter 1 and don't matter 2
        dm1, dm2 = corr_object.run_fullQEC_CSS('surface17', True, False)
        corr_stabs = corr_object.stabs[:]

    else:
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
    
    return final_error, fail, n_supra_gates


#QEC_circ_list = wrapper.add_specific_error_configuration(QEC_circ_list,
#                                                         ['Y'],
#                                                         [(0,3)])
#brow.from_circuit(QEC_circ_list[0], True)
#print run_QEC_d3(init_state, QEC_circ_list, 'surface17')
#sys.exit(0)



def run_several_QEC_fast_all_flags(error_info, n_runs_total, init_state, QEC_kind='all_flags'):
    '''
    '''
    did_run = 0
    n_final_errors = 0
    n_fails = 0
    n_supra_gates = 0
    even_supra, odd_supra = 0, 0

    for n_run in xrange(n_runs_total):

        QEC_circ_list_copy = []
        for subcirc in QEC_circ_list:
            QEC_circ_list_copy += [copy.deepcopy(subcirc)]
        
        # Add the errors and decide to run (in this case we'll always run)
        errors_dict, carry_run, faulty_circs = wrapper.add_errors_fast_sampler_new(
                                                        [one_q_gates, two_q_gates],
                                                        n_errors,
                                                        QEC_circ_list_copy,
                                                        error_info)
        
        # Run
        did_run += 1
        final_error, fail, n_supra_local = run_QEC_d3(init_state, faulty_circs, QEC_kind)
        n_supra_gates += len(n_supra_local)
        #print n_supra_local
        for num in n_supra_local:
            if num%2 == 0:  even_supra += 1
            else:           odd_supra += 1

        if final_error:
            n_final_errors += 1
        if fail:  
            n_fails += 1

    return n_final_errors, n_fails, n_supra_gates, even_supra, odd_supra



def run_several_QEC_fast(error_info, n_runs_total, init_state, QEC_kind, QEC_circ_list):
    '''
    '''

    did_run = 0
    n_final_errors = 0
    n_fails = 0
    n_supra_gates = 0

    for n_run in xrange(n_runs_total):

        if QEC_kind == 'surface17':
            
            fraction_of_circ = 4
            
            QEC_circ_list_copy = []
            for subcirc in QEC_circ_list:
                QEC_circ_list_copy += [copy.deepcopy(subcirc)]

            # Add the errors and decide to run
            errors_dict, carry_run, faulty_circs = wrapper.add_errors_fast_sampler_new(
                                                        [one_q_gates, two_q_gates],
                                                        n_errors,
                                                        QEC_circ_list_copy,
                                                        error_info,
                                                        fraction_of_circ)

            #brow.from_circuit(QEC_circ_list_copy[0], True)
            #time.sleep(5)

        
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
            


        if QEC_kind != 'surface17':
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
            final_error, fail, n_supra_local = run_QEC_d3(init_state, faulty_circs, QEC_kind)
            n_supra_gates += n_supra_local
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



def run_parallel_QEC(error_info, n_runs_per_proc, n_proc, init_state, QEC_kind, QEC_circ_list):
    '''
    '''
    if QEC_kind == 'all_flags':
        sim_func = run_several_QEC_fast_all_flags
    else:
        sim_func = run_several_QEC_fast
    pool = mp.Pool()
    results = [pool.apply_async(sim_func, (error_info, n_runs_per_proc, 
                                           init_state, QEC_kind, QEC_circ_list[:]))
                    for proc in range(n_proc)]
    pool.close()
    pool.join()
    dicts = [r.get() for r in results]

    return dicts


#print run_several_QEC_fast(error_info, 10, init_state, QEC_kind, QEC_circ_list[:])
#print run_several_QEC_fast_all_flags(error_info, 10, init_state, QEC_kind)
#print n_per_proc, n_proc, QEC_kind

#print run_several_QEC_fast(error_info, 100, init_state, QEC_kind)
out_list = run_parallel_QEC(error_info, n_per_proc, n_proc, init_state, 
                            QEC_kind, QEC_circ_list)
n_total = n_per_proc*n_proc
#print out_list
#print n_total
#sys.exit(0)
n_final_errors = sum([event[0] for event in out_list])
n_fail = sum([event[1] for event in out_list])
n_supra_gates = sum([event[2] for event in out_list])
#n_even_gates = sum([event[3] for event in out_list])
#n_odd_gates = sum([event[4] for event in out_list])

#n_twoq_gates = n_even_gates*n_2q_gates[0] + n_odd_gates*n_2q_gates[1]
#n_oneq_gates = n_even_gates*n_1q_gates[0] + n_odd_gates*n_1q_gates[1]
#n_meas_gates = n_even_gates*n_meas[0] + n_odd_gates*n_meas[1]

n_twoq_gates = n_supra_gates*n_2q_gates[0]
n_oneq_gates = n_supra_gates*n_1q_gates[0]
n_meas_gates = n_supra_gates*n_meas[0]

n_correctable = n_final_errors - n_fail
p_correctable = float(n_correctable)/float(n_total)
p_fail = float(n_fail)/float(n_total)
p_supra_gates = float(n_supra_gates)/float(n_total)
#p_even_supra = float(n_even_gates)/float(n_total)
#p_odd_supra = float(n_odd_gates)/float(n_total)
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
            #'p_even_supra': p_even_supra,
            #'p_odd_supra': p_odd_supra,
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




