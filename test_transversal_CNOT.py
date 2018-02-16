import sys
import os
import json
import multiprocessing as mp
import circuit as c
import steane as st
import MC_functions as mc
import qcircuit_functions as qfun
import qcircuit_wrapper as qcirc
import chper_wrapper as wrapper
from visualizer import browser_vis as brow

chp_loc = './chp_extended'
error_model = 'ion_trap_eQual2'
code = 'Steane'
n_code = 7

#testchange to branch

# User-defined inputs:
n_per_proc, n_proc = int(sys.argv[1]), int(sys.argv[2])

# n_errors = [preps and meas, MS, idle, cross, 1q]
n_errors = [int(sys.argv[i]) for i in range(3,8)]

# initial_states (X or Z)
init_state1, init_state2 = sys.argv[8], sys.argv[9]

# Define the output folder where the json files will be saved
output_folder = './MC_results/QECd3_flags/all_flags/ion_trap2/CNOT/transversal/noQEC/%s%s/' %(init_state1, init_state2)

# Define the error information
# For the subset sampler, these error rates are just place-holders;
# their exact values don't matter.
p1, p2, p_meas, p_prep, p_sm, p_cross = 0.1, 0.1, 0.1, 0.1, 0.1, 0.1
error_dict, Is_after2q, Is_after1q, faulty_groups = wrapper.dict_for_error_model(
                                                        error_model=error_model,
                                                        p_1q=p1, p_2q=p2,
                                                        p_meas=p_meas, p_prep=p_prep,
                                                        p_sm=p_sm, p_cross=p_cross)

error_info = mc.read_error_info(error_dict)
#for key in error_dict:
#    if key != 'IMS5':
#        print key, error_dict[key]
#print faulty_groups


# create the initial state (|+> ctrl; |0> targ; all |0> anc)
init_state_ctrl = wrapper.prepare_stabs_Steane('+%s'%init_state1)
init_state_targ = wrapper.prepare_stabs_Steane('+%s'%init_state2)
all_stabs = [init_state_ctrl[0]]+[init_state_targ[0]]
all_destabs = [init_state_ctrl[1]]+[init_state_targ[1]]
init_state = qfun.combine_stabs(all_stabs, all_destabs)


# create the circuit
CNOT_circ = st.Generator.transversal_CNOT_ion_trap(False, True)
#brow.from_circuit(CNOT_circ, True)

# Define the list of error-prone gates
# For now, we have 4 groups: (a) I_idle, (b) I_cross, (c) 1-q gates, (d) 2-q MS gates
circ_list = [CNOT_circ.gates[0].circuit_list[0]]
gates_indices = wrapper.gates_list_general(circ_list, faulty_groups)
#print gates_indices
#for i in range(len(faulty_groups)):
#    print faulty_groups[i]
#    print 'N =', len(gates_indices[i])
#    print gates_indices[i]
#    print '\n'




def run_CNOT(init_state, CNOT_circ, chp_loc):
    '''
    First version
    '''

    # Temporary fix:  CNOT_circ is really a 1-element list
    CNOT_circ = c.Encoded_Gate('Transversal_CNOT', CNOT_circ).circuit_wrap()

    CNOT_object = qcirc.Supra_Circuit(init_state, CNOT_circ, code, chp_loc)
    CNOT_gate = CNOT_circ.gates[0]

    out_dict = CNOT_object.run_one_oper(CNOT_gate)
    final_stabs, final_destabs = CNOT_object.state[0][:], CNOT_object.state[1][:]

    # Determine if there is an error (both failures and correctable errors)
    final_errorX, final_errorZ = False, False
    for stab in final_stabs:
        if stab[0] == '-':
            if 'Z' in stab:
                final_errorX = True
            elif 'X' in stab:
                final_errorZ = True
            #break

    # Do perfect EC on the final state
    corr_circ = qfun.create_EC_subcircs(code, False, False, False, True)
    corr_circ2 = qfun.create_EC_subcircs(code, False, False, False, True)
    corr_circ.join_circuit_at(range(n_code,2*n_code), corr_circ2)

    final_state = (final_stabs, final_destabs)
    bare_anc = True
    supra_circ = qcirc.CNOT_latt_surg(final_state, corr_circ, code, chp_loc, bare_anc)
    supra_circ.run_all_gates()
    corr_stabs = supra_circ.state[0]

    # Determine if a failure has occurred
    failX, failZ = False, False
    for stab in corr_stabs:
        if stab[0] == '-':
            if 'Z' in stab:
                failX = True
            elif 'X' in stab:
                failZ = True
            #break

    return final_errorX, final_errorZ, failX, failZ



def run_several_CNOT(error_info, n_runs_total, init_state, circ_list,
                     chp_loc):
    '''
    First version
    '''

    n_final_errorsX, n_final_errorsZ, n_failsX, n_failsZ = 0, 0, 0, 0
    for n_run in xrange(n_runs_total):
        sampler_output = wrapper.add_errors_fast_sampler_ion(gates_indices,
                                                             n_errors,
                                                             circ_list,
                                                             error_info)
        faulty_gates, carry_run, faulty_circs = sampler_output

        output_CNOT = run_CNOT(init_state, faulty_circs, chp_loc)
        if output_CNOT[0]:  n_final_errorsX += 1
        if output_CNOT[1]:  n_final_errorsZ += 1
        if output_CNOT[2]:  n_failsX += 1
        if output_CNOT[3]:  n_failsZ += 1

    return n_final_errorsX, n_final_errorsZ, n_failsX, n_failsZ



def run_parallel_CNOT(error_info, n_runs_per_proc, n_proc, init_state, circ_list, chp_loc):
    '''
    First version
    '''

    sim_func = run_several_CNOT
    pool = mp.Pool()
    results = [pool.apply_async(sim_func, (error_info, n_runs_per_proc,
                                           init_state, circ_list, chp_loc))
                                for proc in range(n_proc)]
    pool.close()
    pool.join()
    dicts = [r.get() for r in results]

    return dicts


out_list = run_parallel_CNOT(error_info, n_per_proc, n_proc, init_state, circ_list, chp_loc)
n_runs_total = n_per_proc*n_proc
n_final_errorsX = sum([event[0] for event in out_list])
n_final_errorsZ = sum([event[1] for event in out_list])
n_failsX = sum([event[2] for event in out_list])
n_failsZ = sum([event[3] for event in out_list])

n_correctableX = n_final_errorsX - n_failsX
n_correctableZ = n_final_errorsZ - n_failsZ
p_correctableX = float(n_correctableX)/float(n_runs_total)
p_correctableZ = float(n_correctableZ)/float(n_runs_total)
p_failX = float(n_failsX)/float(n_runs_total)
p_failZ = float(n_failsZ)/float(n_runs_total)
out_dict = {'n_total': n_runs_total,
            'n_corrX': n_correctableX,
            'n_corrZ': n_correctableZ,
            'p_corrX': p_correctableX,
            'p_corrZ': p_correctableZ,
            'p_failX': p_failX,
            'p_failZ': p_failZ}

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

json_filename = '_'.join(map(str, n_errors)) + '.json'
abs_filename = output_folder + json_filename
json_file = open(abs_filename, 'w')
json.dump(out_dict, json_file, indent=4, separators=(',', ':'), sort_keys=True)
json_file.close()

