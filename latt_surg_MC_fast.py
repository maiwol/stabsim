import sys
import os
import json
import error
import random as rd
import multiprocessing as mp
import qcircuit_wrapper as qcirc
import chper_wrapper as wrapper
import qcircuit_functions as qfun
import MC_functions as mc
import cross
from visualizer import browser_vis as brow


# code parameters

initial_I = True
anc_parallel = True
EC_ctrl_targ = False

oper = 'Shor'
code = 'Steane'
n_code = 7
bare = False
chp_loc = './chp_extended'

# Define error dictionary and whether or not to add Is after 2-qubit gates
# The 'standard' error model does not require Is after 2-qubit gates.
# The 'ion_trap_simple' error model does.
error_model = 'standard'
p1, p2, p_meas = 0.001, 0.001, 0.001  # these don't matter for the fast sampler
error_dict, Is_after2q, Is_after_1q = wrapper.dict_for_error_model(error_model, p1, p2, p_meas)
error_info = mc.read_error_info(error_dict)
output_folder = './MC_results/latt_CNOT/' + error_model + '/'

n_per_proc, n_proc = int(sys.argv[1]), int(sys.argv[2])
if sys.argv[3] == 'True':  FT = True
else:  FT = False

n_errors = [int(sys.argv[4]), int(sys.argv[5])]

# create the initial state (|+> ctrl; |0> targ; all |0> anc)
init_state_ctrl = wrapper.prepare_stabs_Steane('+X')
init_state_targ = wrapper.prepare_stabs_Steane('+Z')
#init_state_anc = wrapper.prepare_stabs_Steane('+Z')
anc_stabs, anc_destabs = [], []
for i in range(n_code):
    anc_stab = ['Z' if i==j else 'I' for j in range(n_code)]
    anc_stab.insert(0, '+')
    anc_destab = ['X' if i==j else 'I' for j in range(n_code)]
    anc_destab.insert(0, '+')
    anc_stabs += [''.join(anc_stab)]
    anc_destabs += [''.join(anc_destab)]
init_state_anc = anc_stabs, anc_destabs

all_stabs = [init_state_ctrl[0]]+[init_state_targ[0]]+[init_state_anc[0]]
all_destabs = [init_state_ctrl[1]]+[init_state_targ[1]]+[init_state_anc[1]]
initial_state = qfun.combine_stabs(all_stabs, all_destabs)


def run_latt_surg_circ(init_state, circuits):

    supra_circ = qcirc.CNOT_latt_surg(init_state, circuits, code, chp_loc)
    supra_circ.run_all_gates()

    final_stabs = supra_circ.state[0][:]
    final_destabs = supra_circ.state[1][:]

    # do perfect EC on ctrl and target logical qubits
    corr_circ = qfun.create_EC_subcircs(code, False, False, False, True)
    corr_circ2 = qfun.create_EC_subcircs(code, False, False, False, True)
    corr_circ.join_circuit_at(range(n_code,2*n_code), corr_circ2)
    
    final_state = (final_stabs, final_destabs)
    bare_anc = True
    supra_circ = qcirc.CNOT_latt_surg(final_state,
                                      corr_circ,
                                      code,
                                      chp_loc,
                                      bare_anc)
    supra_circ.run_all_gates()
    
    corr_stabs = supra_circ.state[0]

    # Determine if a failure has occurred
    fail = False
    for stab in corr_stabs:
        if stab[0] == '-':  
            fail = True
            break
    
    return fail



def gates_list_CNOT(CNOT_circuits, faulty_gates_names):
    '''
    improvised function to calculate the indices for 1-qubit and 2-qubit gates
    '''

    single_qubit_gates, two_qubit_gates = [], []

    for i in range(len(CNOT_circuits.gates)):
        supra_gate = CNOT_circuits.gates[i] 
        if supra_gate.gate_name == 'Logical_I' or supra_gate.gate_name == 'MeasureX':
            for j in range(len(supra_gate.circuit_list[0].gates)):
                in_gate1 = supra_gate.circuit_list[0].gates[j]
                if in_gate1.gate_name in faulty_gates_names:
                    if len(in_gate1.qubits) == 1:
                        single_qubit_gates.append((i,j))
                    elif len(in_gate1.qubits) == 2:
                        two_qubit_gates.append((i,j))
        
        elif supra_gate.gate_name[:8] == 'Measure2' or supra_gate.gate_name[:5] == 'Joint':
            for j in range(len(supra_gate.circuit_list[0].gates)):
                in_gate1 = supra_gate.circuit_list[0].gates[j]
                if in_gate1.gate_name[:7] == 'Partial':
                    for k in range(len(in_gate1.circuit_list[0].gates)):
                        in_gate2 = in_gate1.circuit_list[0].gates[k]
                        if in_gate2.gate_name in faulty_gates_names:
                            if len(in_gate2.qubits) == 1:
                                single_qubit_gates.append((i,j,k))
                            elif len(in_gate2.qubits) == 2:
                                two_qubit_gates.append((i,j,k))
                            
                elif in_gate1.gate_name[:2] == 'EC':
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




CNOT_circuits = qfun.create_latt_surg_CNOT(Is_after2q, initial_I, anc_parallel,
                                           EC_ctrl_targ, FT)
one_q_gates, two_q_gates = gates_list_CNOT(CNOT_circuits, error_dict.keys())



def run_several_latt_fast(error_info, n_runs_total, init_state):
    '''
    '''
    n_fails = 0
    for n_run in xrange(n_runs_total):
        # create the supra-circuit and insert gates
        CNOT_circuits = qfun.create_latt_surg_CNOT(Is_after2q, initial_I, anc_parallel,
                                                   EC_ctrl_targ, FT)
        
        brow.from_circuit(CNOT_circuits, True)
        sys.exit(0)
        
        # shuffle gate indices
        rd.shuffle(one_q_gates)
        rd.shuffle(two_q_gates)

        selected_one_q_gates = one_q_gates[ : n_errors[0]]
        selected_two_q_gates = two_q_gates[ : n_errors[1]]

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
                faulty_circ = CNOT_circuits.gates[group[0][0]].circuit_list[0]
            if len(group[0]) >= 3:
                faulty_circ = faulty_circ.gates[group[0][1]].circuit_list[0]
            if len(group[0]) == 4:
                faulty_circ = faulty_circ.gates[group[0][2]].circuit_list[0]

            error.add_error_alternative(faulty_circ, error_info, 'Muyalon', local_gates)
        

        # run the faulty circuit
        init_state_copy = init_state[0][:], init_state[1][:]
        fail = run_latt_surg_circ(init_state_copy, CNOT_circuits)
        if fail:  n_fails += 1


        #print 'Fail', fail

    return n_fails
        


def run_several_latt(error_info, n_runs_total, init_state):
    '''
    '''

    #if output_folder[-1] != '/':  output_folder += '/'
    #chp_loc = './chp_extended'
    #CHP_IO_files = False

    n_fails = 0

    for n_run in xrange(n_runs_total):
        # create the supra-circuit and insert gates
        CNOT_circuits = qfun.create_latt_surg_CNOT(Is_after2q, initial_I, anc_parallel,
                                                   EC_ctrl_targ, FT)
        for supra_gate in CNOT_circuits.gates:
            if supra_gate.gate_name == 'Logical_I' or supra_gate.gate_name == 'MeasureX':
                error.add_error(supra_gate.circuit_list[0], error_info)
            elif supra_gate.gate_name[:8] == 'Measure2' or supra_gate.gate_name[:5] == 'Joint':
                for in_gate in supra_gate.circuit_list[0].gates:
                    if in_gate.gate_name[:7] == 'Partial':
                        error.add_error(in_gate.circuit_list[0], error_info)
                    elif in_gate.gate_name[:2] == 'EC':
                        for in_gate2 in in_gate.circuit_list[0].gates:
                            error.add_error(in_gate2.circuit_list[0], error_info)
        
        #brow.from_circuit(CNOT_circuits, True)
        
        # run the faulty circuit
        init_state_copy = init_state[0][:], init_state[1][:]
        fail = run_latt_surg_circ(init_state_copy, CNOT_circuits)
        if fail:  n_fails += 1

    return n_fails
        


def run_parallel_latt(error_info, n_runs_per_proc, n_proc, init_state, sampling='Muyalon'):
    '''
    '''
    if sampling == 'Muyalon':  sim_func = run_several_latt_fast
    else:  sim_func = run_several_latt

    pool = mp.Pool(n_proc)
    results = [pool.apply_async(sim_func, (error_info, n_runs_per_proc,
                                           init_state)) 
                                           for i in range(n_proc)]
    pool.close()
    pool.join()
    dicts = [r.get() for r in results]

    return dicts


print run_several_latt_fast(error_info, n_per_proc*n_proc, initial_state)
sys.exit(0)

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
    
