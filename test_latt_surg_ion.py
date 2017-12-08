import sys
import os
import copy
import json
import multiprocessing as mp
import chper_wrapper as wrapper
import MC_functions as mc
import qcircuit_functions as qfun
import qcircuit_wrapper as qcirc
from visualizer import browser_vis as brow


chp_loc = './chp_extended'
error_model = 'ion_trap_eQual3'
code = 'Steane'
n_code = 7

# User-defined inputs:
n_per_proc, n_proc = int(sys.argv[1]), int(sys.argv[2])

# n_errors = [preps and meas, MS2, idle, cross, 1q, MS5]
n_errors = [int(sys.argv[i]) for i in range(3,9)]

# initial_states (X or Z)
init_state1, init_state2 = sys.argv[9], sys.argv[10]

# number of round (for HPC Wales)
n_round_HPC = sys.argv[11]

# Define the output folder where the json files will be saved
output_folder = './MC_results/QECd3_flags/all_flags/ion_trap3/CNOT/latt_surg/noQEC/%s%s/' %(init_state1, init_state2)

# Define the error information
# For the subset sampler, these error rates are just place-holders;
# their exact values don't matter.
p1, p2, p_meas, p_prep, p_sm, p_cross, p_5q = 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1
error_dict, Is_after2q, Is_after1q, faulty_groups = wrapper.dict_for_error_model(
                                                        error_model=error_model,
                                                        p_1q=p1, p_2q=p2,
                                                        p_meas=p_meas, p_prep=p_prep,
                                                        p_sm=p_sm, p_cross=p_cross,
                                                        p_5q=p_5q)
error_info = mc.read_error_info(error_dict)

# create the initial state (|+> ctrl; |0> targ; all |0> anc)
init_state_ctrl = wrapper.prepare_stabs_Steane('+%s'%init_state1)
init_state_targ = wrapper.prepare_stabs_Steane('+%s'%init_state2)
init_state_anc = wrapper.prepare_stabs_Steane('+Z')
all_stabs = [init_state_ctrl[0]]+[init_state_targ[0]]+[init_state_anc[0]]
all_destabs = [init_state_ctrl[1]]+[init_state_targ[1]]+[init_state_anc[1]]
initial_state = qfun.combine_stabs(all_stabs, all_destabs)

# create the circuit
latt_circ = qfun.create_latt_surg_CNOT(False,True,True,False,True,True,True)
#brow.from_circuit(latt_circ, True)
#sys.exit(0)

# Define the list of error-prone gates
# For now, we have 6 groups: (a) preps and meas, (b) MS2, (c) I_idle, (d) I_cross, 
#                            (e) 1-q gates, (f) MS5
gates_indices = wrapper.gates_list_CNOT_general(latt_circ, faulty_groups)



# run the circuit
def run_circ(CNOT_circ_copy, chp_loc):
    '''
    '''
    ion = True
    initial_state_copy = copy.deepcopy(initial_state)
    latt_object = qcirc.CNOT_latt_surg(initial_state_copy, CNOT_circ_copy, 'Steane', chp_loc,
                                   False, ion)
    latt_object.run_all_gates()
    final_stabs, final_destabs = latt_object.state[0][:], latt_object.state[1][:]

    #print latt_object.total_subcircs_run
    #sys.exit(0)

    # Determine if there is an error (both failures and correctable errors)
    final_errorX, final_errorZ = False, False
    for stab in final_stabs:
        if stab[0] != '+':
            if 'Z' in stab:
                final_errorX = True
            elif 'X' in stab:
                final_errorZ = True

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
    failX, failZ = False, False
    for stab in corr_stabs:
        if stab[0] != '+':
            if 'Z' in stab:
                failX = True
            elif 'X' in stab:
                failZ = True

    return final_errorX, final_errorZ, failX, failZ, latt_object.total_subcircs_run



def initialize_subcirc_merge():
    '''
    '''
    subcircs_QECnonanc = {}
    subcircs_QECanc = {}
    for i in range(10):
        subcircs_QECnonanc[i] = 0
        subcircs_QECanc[i] = 0

    subcircs_total = {}
    for i in range(13):
        if i==9:
            subcircs_total[i] = subcircs_QECnonanc
        elif i==10:
            subcircs_total[i] = subcircs_QECanc
        else:
            subcircs_total[i] = 0

    return subcircs_total



def initialize_subcirc_split():
    '''
    '''
    subcircs_QECnonanc = {}
    subcircs_QECanc = {}
    for i in range(14):
        subcircs_QECnonanc[i] = 0
        subcircs_QECanc[i] = 0

    return {0: subcircs_QECnonanc, 1:subcircs_QECanc}



def initialize_total_subcirc():
    '''
    '''
    subcircs_total = {}
    subcircs_total[0] = initialize_subcirc_merge() # XX merge
    subcircs_total[1] = initialize_subcirc_split() # XX split
    subcircs_total[2] = initialize_subcirc_merge() # ZZ merge
    subcircs_total[3] = initialize_subcirc_split() # ZZ split

    return subcircs_total


def add_subcircs_merge(subcircs1, subcircs2):
    '''
    '''
    subcircs_total = {}
    for i in range(13):
        if i==9 or i==10:
            subcircs_total[i] = {}
            for j in range(10):
                subcircs_total[i][j] = subcircs1[i][j] + subcircs2[i][j]
        else:
            subcircs_total[i] = subcircs1[i] + subcircs2[i]

    return subcircs_total


def add_subcircs_split(subcircs1, subcircs2):
    '''
    '''
    subcircs_QECnonanc = {}
    subcircs_QECanc = {}
    for i in range(14):
        subcircs_QECnonanc[i] = subcircs1[0][i] + subcircs2[0][i]
        subcircs_QECanc[i] = subcircs1[1][i] + subcircs2[1][i]

    return {0: subcircs_QECnonanc, 1: subcircs_QECanc}


def add_total_subcircs(subcircs1, subcircs2):
    '''
    '''
    subcircs_total = {}
    subcircs_total[0] = add_subcircs_merge(subcircs1[0], subcircs2[0]) # XX merge
    subcircs_total[1] = add_subcircs_split(subcircs1[1], subcircs2[1]) # XX split
    subcircs_total[2] = add_subcircs_merge(subcircs1[2], subcircs2[2]) # ZZ merge
    subcircs_total[3] = add_subcircs_split(subcircs1[3], subcircs2[3]) # ZZ split

    return subcircs_total



def run_several_CNOT(error_info, n_runs_total, chp_loc):
    '''
    '''

    n_final_errorsX, n_final_errorsZ, n_failsX, n_failsZ = 0, 0, 0, 0
    subcircs_total = initialize_total_subcirc()    
    for n_run in xrange(n_runs_total):
        # first copy the error-free circuit
        latt_circ_copy = copy.deepcopy(latt_circ)
        wrapper.add_errors_fast_sampler_ion_latt_surg(gates_indices, n_errors, latt_circ_copy,
                                                      error_info)
        #brow.from_circuit(latt_circ_copy, True)
        output_run = run_circ(latt_circ_copy, chp_loc)
        if output_run[0]:  n_final_errorsX += 1
        if output_run[1]:  n_final_errorsZ += 1
        if output_run[2]:  n_failsX += 1
        if output_run[3]:  n_failsZ += 1
        subcircs_total = add_total_subcircs(subcircs_total, output_run[4])

    return n_final_errorsX, n_final_errorsZ, n_failsX, n_failsZ, subcircs_total

#print run_several_CNOT(error_info, 100, chp_loc)
#sys.exit(0)


def run_parallel_CNOT(error_info, n_runs_per_proc, n_proc, chp_loc):
    '''
    First version
    '''

    sim_func = run_several_CNOT
    pool = mp.Pool()
    results = [pool.apply_async(sim_func, (error_info, n_runs_per_proc, chp_loc))
                                for proc in range(n_proc)]
    pool.close()
    pool.join()
    dicts = [r.get() for r in results]

    return dicts



#n_runs_total = n_per_proc*n_proc
#out_list = run_several_CNOT(error_info, n_runs_total, initial_state, chp_loc)
#n_final_errorsX = out_list[0]
#n_final_errorsZ = out_list[1]
#n_failsX = out_list[2]
#n_failsZ = out_list[3]

out_list = run_parallel_CNOT(error_info, n_per_proc, n_proc, chp_loc)
n_runs_total = n_per_proc*n_proc
#n_final_errorsX = sum([event[0] for event in out_list])
#n_final_errorsZ = sum([event[1] for event in out_list])
#n_failsX = sum([event[2] for event in out_list])
#n_failsZ = sum([event[3] for event in out_list])
n_final_errorsX, n_final_errorsZ = 0, 0
n_failsX, n_failsZ = 0, 0
subcircs_run_total = initialize_total_subcirc()
for event in out_list:
    n_final_errorsX += event[0] 
    n_final_errorsZ += event[1] 
    n_failsX += event[2] 
    n_failsZ += event[3] 
    subcircs_run_total = add_total_subcircs(subcircs_run_total, event[4])


n_correctableX = n_final_errorsX - n_failsX
n_correctableZ = n_final_errorsZ - n_failsZ
p_correctableX = float(n_correctableX)/float(n_runs_total)
p_correctableZ = float(n_correctableZ)/float(n_runs_total)
p_failX = float(n_failsX)/float(n_runs_total)
p_failZ = float(n_failsZ)/float(n_runs_total)
out_dict = {'n_total': n_runs_total,
            'n_corrX': n_correctableX,
            'n_corrZ': n_correctableZ,
            'n_failsX': n_failsX,
            'n_failsZ': n_failsZ,
            'p_corrX': p_correctableX,
            'p_corrZ': p_correctableZ,
            'p_failX': p_failX,
            'p_failZ': p_failZ,
            'subcircs_run': subcircs_run_total}

extra_folder = '_'.join(map(str, n_errors)) + '/'
output_folder = output_folder + extra_folder
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

#json_filename = '_'.join(map(str, n_errors)) + '.json'
json_filename = n_round_HPC + '.json' 
abs_filename = output_folder + json_filename
json_file = open(abs_filename, 'w')
json.dump(out_dict, json_file, indent=4, separators=(',', ':'), sort_keys=True)
json_file.close()

