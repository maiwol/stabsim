import sys
import os
import json
import multiprocessing as mp
import steane
import correction as cor
from visualizer import browser_vis as brow
import chper_wrapper as wrapper
import MC_functions as mc
import qcircuit_functions as qfun
import qcircuit_wrapper as qwrap


chp_loc = './chp_extended'
error_model = 'ion_trap_eQual'
decoder = 'new'
if decoder == 'new':  n_subcircs_first_round = 9
else:  n_subcircs_first_round = 12
# These error rates don't matter for the fast sampler
p1, p2, p_meas, p_prep, p_sm, p_cool = 0.1, 0.1, 0.1, 0.1, 0.1, 0.1 
error_dict, Is_after2q, Is_after1q, faulty_groups = wrapper.dict_for_error_model(
                                                         error_model=error_model,
                                                         p_1q=p1, p_2q=p2,
                                                         p_meas=p_meas, p_prep=p_prep,
                                                         p_sm=p_sm, p_cool=p_cool)
error_info = mc.read_error_info(error_dict)

n_per_proc, n_proc = int(sys.argv[1]), int(sys.argv[2])
n_errors = [int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])]
alternating = sys.argv[7]   # either 'True' or 'False'
in_state = sys.argv[8]  # either 'Z' or 'X'

if alternating == 'True':
    alternating = True
    output_folder = './MC_results/QECd3_flags/all_flags/ion_trap1/alternating/%s/%s/' %(decoder,in_state)
else:
    alternating = False
    output_folder = './MC_results/QECd3_flags/all_flags/ion_trap1/non_alternating/%s/%s/' %(decoder, in_state)



# Define the circuit and the circuit_list
i_first_anc = 7
stabs = steane.Code.stabilizer_alt
if alternating:
    stabs = [stabs[0], stabs[3], stabs[1], stabs[4], stabs[2], stabs[5]]
meas_errors = True
initial_I = True
dephasing_during_MS = True
QEC_circ = cor.Flag_Correct.generate_whole_QEC_d3_ion(stabs, 
                                                      meas_errors,
                                                      initial_I,
                                                      dephasing_during_MS,
                                                      decoder)
#brow.from_circuit(QEC_circ, True)
#sys.exit(0)
QEC_circ_list = []
for log_gate in QEC_circ.gates:
    QEC_circ_list += [log_gate.circuit_list[0]]

# Define the list of error-prone gates
# For now, we have 4 groups: (a) preps and meas, (b) shuttling and merging
# (c) cooling, and (d) MS gates.
prep_meas_g, shut_g, cool_g, MS_g = wrapper.gates_list_general(QEC_circ_list, faulty_groups)
gate_indices = [prep_meas_g, shut_g, cool_g, MS_g]


# Define the number of all the 2-q gates, 1-q gates, and measurements
# for resource counting purposes
n_2q_gates, n_1q_gates, n_meas, n_5q_gates = [], [], [], []
#n_Ism, n_Icool = [], []
for subcirc in QEC_circ_list:
    two_q, one_q, meas, five_q = 0, 0, 0, 0
    Ism, Icool = 0, 0
    for phys_gate in subcirc.gates:
        if len(phys_gate.qubits) == 5:
            # trick used because the for each ISM5,
            # there are really 2 5-qubit MS gates
            five_q += 2
        elif len(phys_gate.qubits) == 2:
            if phys_gate.gate_name[0] != 'C':
                two_q += 1
        else:
            if phys_gate.gate_name[0] != 'I':
                one_q += 1
            if phys_gate.gate_name[:4] == 'Meas':
                meas += 1
            #elif phys_gate.gate_name == 'Ism':
            #    Ism += 1
            #elif phys_gate.gate_name == 'Icool':
            #    Icool += 1
    n_5q_gates += [five_q]
    n_2q_gates += [two_q]
    n_1q_gates += [one_q]
    n_meas += [meas]
    #n_Ism += [Ism]
    #n_Icool += [Icool]



# Define initial state
state = '+' + in_state
init_stabs = steane.Code.stabilizer_logical_CHP[state][:]
#init_stabs[0] = '-' + init_stabs[0][1:]
#init_stabs[3] = '-' + init_stabs[3][1:]
init_destabs = steane.Code.destabilizer_logical_CHP[state][:]
init_state = [init_stabs, init_destabs]
#print init_stabs


def run_QEC_d3(init_state, QEC_circ_list, chp_loc, alternating, decoder='old'):
    '''
    '''

    QEC_object = qwrap.QEC_with_flags(init_state, QEC_circ_list[:], chp_loc)
    supra_gates = QEC_object.run_stabilizers_high_indet_ion(0, alternating,
                                                            'any', decoder)

    final_stabs, final_destabs = QEC_object.stabs[:], QEC_object.destabs[:]

    # Determine if there is an error (both failures and correctable errors)
    final_error = False
    for stab in final_stabs:
        if stab[0] != '+':
            final_error = True
            break

    # Do perfect EC on the final state
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

    return final_error, fail, supra_gates



def run_several_QEC_fast(error_info, n_runs_total, init_state, QEC_circ_list,
                         chp_loc, alternating, n_subcircs_first_round=12,
                         decoder='old'):
    '''
    '''
    did_run = 0
    n_final_errors = 0
    n_fails = 0
    n_supra_gates = 0
    n_FT_subcirc, n_nonFT_subcirc = 0, 0
    n_1round, n_2round = 0, 0   # number of runs that required 1 or 2 rounds of QEC

    for n_run in xrange(n_runs_total):

        #print n_run
        # Add the errors and decide to run
        sampler_output = wrapper.add_errors_fast_sampler_ion(gate_indices,
                                                             n_errors,
                                                             QEC_circ_list,
                                                             error_info,
                                                             n_subcircs_first_round)
        faulty_gates, carry_run, faulty_circs = sampler_output
       
        #print faulty_circs
        # just for now we will always run the circuit, 
        # cause the sampler function only works for the old decoder
        carry_run = True

        if not carry_run:
            n_supra_gates += int(n_subcircs_first_round/2)
            n_FT_subcirc += int(n_subcircs_first_round/2)
            n_1round += 1
                
        else:
            did_run += 1
            final_error, fail, supra_local = run_QEC_d3(init_state,
                                                        faulty_circs,
                                                        chp_loc,
                                                        alternating,
                                                        decoder)
            n_supra_gates += len(supra_local)
            if len(supra_local) == int(n_subcircs_first_round/2):
                n_1round += 1
                n_FT_subcirc += len(supra_local)
            else:
                n_2round += 1

                if decoder == 'old':
                    for num in supra_local:
                        if (num%2 == 0) and (num < n_subcircs_first_round):
                            n_FT_subcirc += 1
                        else:
                            n_nonFT_subcirc += 1
                elif decoder == 'new':
                    for num in supra_local:
                        if num < 6:  n_FT_subcirc += 1
                        else:  n_nonFT_subcirc += 1
            

            if final_error:  n_final_errors += 1
            if fail:  n_fails += 1


    return n_final_errors, n_fails, n_supra_gates, n_FT_subcirc, n_nonFT_subcirc, n_1round, n_2round, did_run 



def run_parallel_QEC(error_info, n_runs_per_proc, n_proc, init_state, QEC_circ_list,
                     chp_loc, alternating, n_subcircs_first_round, decoder):
    '''
    '''
    sim_func = run_several_QEC_fast
    pool = mp.Pool()
    results = [pool.apply_async(sim_func, (error_info, n_runs_per_proc,
                                           init_state, QEC_circ_list,
                                           chp_loc, alternating, 
                                           n_subcircs_first_round, decoder))
                                   for proc in range(n_proc)]
    pool.close()
    pool.join()
    dicts = [r.get() for r in results]

    return dicts


out_list = run_parallel_QEC(error_info, n_per_proc, n_proc, init_state,
                            QEC_circ_list, chp_loc, alternating, n_subcircs_first_round,
                            decoder)
n_total = n_per_proc*n_proc
n_final_errors = sum([event[0] for event in out_list])
n_fail = sum([event[1] for event in out_list])
n_supra_gates = sum([event[2] for event in out_list])
n_FT_gates = sum([event[3] for event in out_list])
n_nonFT_gates = sum([event[4] for event in out_list])
n_1round = sum([event[5] for event in out_list])
n_2round = sum([event[6] for event in out_list])
n_run = sum([event[7] for event in out_list])

# number of shuttling and merging steps
n_sm = 17*n_FT_gates + 2*n_nonFT_gates
# number of cooling steps
n_cool = 6*n_FT_gates + 1*n_nonFT_gates
# number of rotation steps
n_rot = n_FT_gates
# number of 2q MS gates
n_2qMS = 6*n_FT_gates
# number of 5q MS gates
n_5qMS = 2*n_nonFT_gates
# number of preps (and measurements)
n_preps = 2*n_FT_gates + n_nonFT_gates


if alternating:
    n_sm += 22*(n_1round + 2*n_2round)
    n_rot += 6*(n_1round + 2*n_2round)
else:
    n_sm += 44*(n_1round + 2*n_2round)
    n_rot += 12*(n_1round + 2*n_2round)


n_correctable = n_final_errors - n_fail
p_correctable = float(n_correctable)/float(n_total)
p_fail = float(n_fail)/float(n_total)
p_supra_gates = float(n_supra_gates)/float(n_total)
p_FT_gates = float(n_FT_gates)/float(n_total)
p_nonFT_gates = float(n_nonFT_gates)/float(n_total)
p_sm = float(n_sm)/float(n_total)
p_cool = float(n_cool)/float(n_total)
p_rot = float(n_rot)/float(n_total)
p_2qMS = float(n_2qMS)/float(n_total)
p_5qMS = float(n_5qMS)/float(n_total)
p_preps = float(n_preps)/float(n_total)
p_run = float(n_run)/float(n_total)
out_dict = {'n_total': n_total,
            'n_correctable': n_correctable,
            'p_correctable': p_correctable,
            'n_fail': n_fail,
            'p_fail': p_fail,
            'n_supra_gates': n_supra_gates,
            'p_supra_gates': p_supra_gates,
            'p_FT_gates': p_FT_gates,
            'p_nonFT_gates': p_nonFT_gates,
            'p_sm': p_sm,
            'p_cool': p_cool,
            'p_rot': p_rot,
            'p_2qMS': p_2qMS,
            'p_5qMS': p_5qMS,
            'p_preps': p_preps,
            'p_run': p_run}

if not os.path.exists(output_folder):
    os.makedirs(output_folder)


json_filename = '_'.join(map(str, n_errors)) + '.json'
abs_filename = output_folder + json_filename
json_file = open(abs_filename, 'w')
json.dump(out_dict, json_file, indent=4, separators=(',', ':'), sort_keys=True)
json_file.close()

