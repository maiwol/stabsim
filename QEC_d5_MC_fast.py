import sys
import os
import copy
import json
import error
import random as rd
import multiprocessing as mp
import d5color
import correction as cor
import qcircuit_functions as qfun
import qcircuit_wrapper as qwrap
import chper_wrapper as wrapper
import MC_functions as mc
from visualizer import browser_vis as brow


chp_location = './chp_extended'
code = 'd5color'
n_code = 17


# Define error dictionary and whether or not to add Is after 2-qubit gates
# The 'standard' error model does not require Is after 2-qubit gates.
# The 'ion_trap_simple' error model does.
error_model = 'standard'
p1, p2, p_meas = 0.001, 0.001, 0.001  # these don't matter for the fast sampler
error_dict, Is_after2q, Is_after_1q = wrapper.dict_for_error_model(error_model, p1, p2, p_meas)
error_info = mc.read_error_info(error_dict)
output_folder = './MC_results/QECd5/' + error_model + '/'

n_per_proc, n_proc = int(sys.argv[1]), int(sys.argv[2])
if sys.argv[3] == 'True':  FT = True
else:  FT = False

n_errors = [int(sys.argv[4]), int(sys.argv[5])]

'''
stabs = [
          [2,3,6,5,9,10,13,14],
          [0,1,2,3],
          [0,2,4,5],
          [4,5,8,9],
          [8,9,12,13],
          [6,7,10,11],
          [10,11,14,15],
          [7,11,15,16]
        ]

color_stabs = []
for stab_kind in ['X','Z']:
    for stab in stabs:
        color_stabs += [[[stab_kind, index] for index in stab]]
'''
initial_I = False
meas_errors, Is_after_two = True, Is_after2q
rep_w8, redun = 5, 5

init_stabs, init_destabs = d5color.Code.stabilizer_CHP_X[:], d5color.Code.destabilizer_CHP_X[:] 
initial_state = [init_stabs, init_destabs]


def gates_list_QECd5(QECd5_circ, faulty_gates_names):
    '''
    improvised function to calculate the indices for 1-qubit and 2-qubit gates
    '''

    single_qubit_gates, two_qubit_gates = [], []

    for i in range(len(QECd5_circ.gates)):
        supra_gate = QECd5_circ.gates[i]
        for j in range(len(supra_gate.circuit_list[0].gates)):
            in_gate1 = supra_gate.circuit_list[0].gates[j]
            for k in range(len(in_gate1.circuit_list[0].gates)):
                in_gate2 = in_gate1.circuit_list[0].gates[k]

                #print in_gate2.gate_name
                if in_gate2.gate_name[:7] == 'weight8':
                    for l in range(len(in_gate2.circuit_list[0].gates)):
                        in_gate3 = in_gate2.circuit_list[0].gates[l]
                        if in_gate3.gate_name[:3] == 'rep':
                            for m in range(len(in_gate3.circuit_list[0].gates)):
                                in_gate4 = in_gate3.circuit_list[0].gates[m]
                                for n in range(len(in_gate4.circuit_list[0].gates)):
                                    in_gate5 = in_gate4.circuit_list[0].gates[n]
                                    if in_gate5.gate_name in faulty_gates_names:
                                        if len(in_gate5.qubits) == 1:
                                            single_qubit_gates.append((i,j,k,l,m,n))
                                        elif len(in_gate5.qubits) == 2:
                                            two_qubit_gates.append((i,j,k,l,m,n))

                        elif in_gate3.gate_name[:4] == 'coup':    
                            for m in range(len(in_gate3.circuit_list[0].gates)):
                                in_gate4 = in_gate3.circuit_list[0].gates[m]
                                if in_gate4.gate_name in faulty_gates_names:
                                    if len(in_gate4.qubits) == 1:
                                        single_qubit_gates.append((i,j,k,l,m))
                                    elif len(in_gate4.qubits) == 2:
                                        two_qubit_gates.append((i,j,k,l,m))

                elif in_gate2.gate_name[:7] == 'Weight4':
                    for l in range(len(in_gate2.circuit_list[0].gates)):
                        in_gate3 = in_gate2.circuit_list[0].gates[l]
                        if in_gate3.gate_name in faulty_gates_names:
                            if len(in_gate3.qubits) == 1:
                                single_qubit_gates.append((i,j,k,l))
                            elif len(in_gate3.qubits) == 2:
                                two_qubit_gates.append((i,j,k,l))
                             
    return single_qubit_gates, two_qubit_gates
    

def gates_list_QECd5_bare_anc(QECd5_circ, faulty_gates_names):
    '''
    '''

    single_qubit_gates, two_qubit_gates = [], []
    for i in range(len(QECd5_circ.gates)):
        supra_gate = QECd5_circ.gates[i]
        for j in range(len(supra_gate.circuit_list[0].gates)):
            in_gate1 = supra_gate.circuit_list[0].gates[j]
            for k in range(len(in_gate1.circuit_list[0].gates)):
                in_gate2 = in_gate1.circuit_list[0].gates[k]
                for l in range(len(in_gate2.circuit_list[0].gates)):
                    in_gate3 = in_gate2.circuit_list[0].gates[l]
                    if in_gate3.gate_name in faulty_gates_names:
                        if len(in_gate3.qubits) == 1:
                            single_qubit_gates.append((i,j,k,l))
                        elif len(in_gate3.qubits) == 2:
                            two_qubit_gates.append((i,j,k,l))

    return single_qubit_gates, two_qubit_gates
                


#QECd5_circ = cor.Cat_Correct.EC_d5_color_code(initial_I, color_stabs, meas_errors, 
#                                              Is_after_two, rep_w8, redun)
#one_q_gates, two_q_gates = gates_list_QECd5(QECd5_circ, error_dict.keys())


QECd5_FT1_3rep_circ = qfun.create_EC_subcircs('d5color', Is_after_two, initial_I)
#QECd5_FT1_5rep_circ = qfun.create_EC_subcircs('d5color', Is_after_two, initial_I,
#                                              False, False, 5)
one_q_gates, two_q_gates = gates_list_QECd5_bare_anc(QECd5_FT1_3rep_circ, 
                                                      error_dict.keys())



def run_QECd5(init_state, QECcirc, bare_anc=True, rep=3):
    '''
    '''
    if bare_anc:
        q_oper = qwrap.QEC_d5(init_state, [QECcirc], chp_location)
        n_X, n_Z = q_oper.run_bare_anc(rep)

    else:
        q_oper = qwrap.QEC_d5(init_state, [QECcirc], chp_location)
        n_X, n_Z = q_oper.run_fullQEC_CSS()

    final_stabs = q_oper.stabs[:]
    final_destabs = q_oper.destabs[:]

    # do perfect EC
    corr_circ = qfun.create_EC_subcircs(code, False, False, False, True)
    #brow.from_circuit(corr_circ.gates[0].circuit_list[0].gates[0].circuit_list[0], True)

    corr_oper = qwrap.Quantum_Operation([final_stabs, final_destabs], 
            [corr_circ.gates[0].circuit_list[0].gates[0].circuit_list[0]],
            chp_location)
    out_dict = corr_oper.run_one_circ(0)
    X_stabs = [out_dict[i][0] for i in range(17,17+8)]
    X_stabs_dec = qfun.binary_to_decimal(X_stabs)
    Z_err = d5color.Code.lookuptable_str[str(X_stabs_dec)]
    Z_err = [i if i=='I' else 'Z' for i in Z_err]
    corr_state = qfun.update_stabs(final_stabs, final_destabs, Z_err)
    final_stabs, final_destabs = corr_state[0][:], corr_state[1][:]

    Z_stabs = [out_dict[i][0] for i in range(17+8,17+16)]
    Z_stabs_dec = qfun.binary_to_decimal(Z_stabs)
    X_err = d5color.Code.lookuptable_str[str(Z_stabs_dec)]
    X_err = [i if i=='I' else 'X' for i in X_err]
    corr_state = qfun.update_stabs(final_stabs, final_destabs, X_err)
    final_stabs, final_destabs = corr_state[0][:], corr_state[1][:]
    
    # Determine if failure has occured
    fail = False
    for stab in final_stabs:
        if stab[0] == '-':
            fail = True
            break
    
    return fail




def run_several_latt_fast(error_info, n_runs_total, init_state):
    '''
    '''

    n_fails = 0
    for n_run in xrange(n_runs_total):
        # create the supra-circuit and insert gates
        QECd5_circ = cor.Cat_Correct.EC_d5_color_code(initial_I, color_stabs, 
                                                      meas_errors, Is_after_two, 
                                                      rep_w8, redun)
                                                                                   
        # shuffle gate indices
        rd.shuffle(one_q_gates)
        rd.shuffle(two_q_gates)

        selected_one_q_gates = one_q_gates[ : n_errors[0]]
        selected_two_q_gates = two_q_gates[ : n_errors[1]]


        #print selected_one_q_gates
        #print selected_two_q_gates

        # group the selected gates
        total_selected_gates = selected_one_q_gates + selected_two_q_gates
        gate_groups = []
        for gate in total_selected_gates:
            in_group = False
            for group in gate_groups:
                for g in group:
                    if g[:-1] == gate[:-1]:
                        group.insert(0, gate)
                        in_group = True
                        break
            
            if not in_group:
                gate_groups += [[gate]]


        # insert errors
        for group in gate_groups:
            local_gates = [g[-1] for g in group]
            if len(group[0]) >= 2:
                faulty_circ = QECd5_circ.gates[group[0][0]].circuit_list[0]
            if len(group[0]) >= 3:
                faulty_circ = faulty_circ.gates[group[0][1]].circuit_list[0]
            if len(group[0]) >= 4:
                faulty_circ = faulty_circ.gates[group[0][2]].circuit_list[0]
            if len(group[0]) >= 5:
                faulty_circ = faulty_circ.gates[group[0][3]].circuit_list[0]
            if len(group[0]) == 6:
                faulty_circ = faulty_circ.gates[group[0][4]].circuit_list[0]

            error.add_error_alternative(faulty_circ, error_info, 'Muyalon', local_gates)

        # run the faulty circuit
        init_state_copy = init_state[0][:], init_state[1][:]
        fail = run_QECd5(init_state_copy, QECd5_circ)
        if fail:  n_fails += 1

        #print 'Fail', fail

    return n_fails



def run_several_latt_fast_QEC_rep3(error_info, n_runs_total, init_state):
    '''
    '''

    n_fails = 0
    for n_run in xrange(n_runs_total):
        # create the supra-circuit and insert gates
        QECd5_circ = qfun.create_EC_subcircs('d5color', Is_after_two, initial_I)
                                                                                   
        # shuffle gate indices
        rd.shuffle(one_q_gates)
        rd.shuffle(two_q_gates)

        selected_one_q_gates = one_q_gates[ : n_errors[0]]
        selected_two_q_gates = two_q_gates[ : n_errors[1]]


        #print selected_one_q_gates
        #print selected_two_q_gates

        # group the selected gates
        total_selected_gates = selected_one_q_gates + selected_two_q_gates
        gate_groups = []
        for gate in total_selected_gates:
            in_group = False
            for group in gate_groups:
                for g in group:
                    if g[:-1] == gate[:-1]:
                        group.insert(0, gate)
                        in_group = True
                        break
            
            if not in_group:
                gate_groups += [[gate]]


        # insert errors
        for group in gate_groups:
            local_gates = [g[-1] for g in group]
            if len(group[0]) >= 2:
                faulty_circ = QECd5_circ.gates[group[0][0]].circuit_list[0]
            if len(group[0]) >= 3:
                faulty_circ = faulty_circ.gates[group[0][1]].circuit_list[0]
            if len(group[0]) == 4:
                faulty_circ = faulty_circ.gates[group[0][2]].circuit_list[0]

            error.add_error_alternative(faulty_circ, error_info, 'Muyalon', local_gates)


        # run the faulty circuit
        init_state_copy = init_state[0][:], init_state[1][:]
        fail = run_QECd5(init_state_copy, QECd5_circ)
        if fail:  n_fails += 1

        #print 'Fail', fail

    return n_fails






def run_parallel_latt(error_info, n_runs_per_proc, n_proc, init_state, sampling='Muyalon'):
    '''
    '''
    #if sampling == 'Muyalon':  sim_func = run_several_latt_fast
    if sampling == 'Muyalon':  sim_func = run_several_latt_fast_QEC_rep3
    else:  sim_func = run_several_latt

    pool = mp.Pool(n_proc)
    results = [pool.apply_async(sim_func, (error_info, n_runs_per_proc,
                                           init_state))
                                           for i in range(n_proc)]
    pool.close()
    pool.join()
    dicts = [r.get() for r in results]

    return dicts



out_list = run_parallel_latt(error_info, n_per_proc, n_proc, initial_state)
n_total = n_per_proc*n_proc
n_fail = sum(out_list)
p_fail = float(n_fail)/float(n_total)
out_dict = {'n_total': n_total, 'n_fail': n_fail, 'p_fail': p_fail}
for i in range(n_proc):
    out_dict[i] = out_list[i]
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

if FT:
    json_filename = 'FT_' + str(n_errors[0]) + '_' + str(n_errors[1]) + '.json'
else:
    json_filename = 'nonFT_' + str(n_errors[0]) + '_' + str(n_errors[1]) + '.json'
abs_filename = output_folder + json_filename
json_file = open(abs_filename, 'w')
json.dump(out_dict, json_file, indent=4, separators=(',', ':'), sort_keys=True)
json_file.close()

