import sys
import json
import math
import itertools as it
import steane as st
import chper_wrapper as wrapper
import qcircuit_functions as qfun


#p1q, p2q = float(sys.argv[1]), float(sys.argv[2])
#ns, nt = float(sys.argv[3]), float(sys.argv[4])
error_model = 'ion_trap_eQual3'
output_folder = './MC_results/QECd3_flags/all_flags/ion_trap3/CNOT/'

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


# create the latt-surg circuit
#latt_circ = qfun.create_latt_surg_CNOT(False,True,True,False,True,True,True)
#brow.from_circuit(latt_circ, True)
#sys.exit(0)

# Define the list of error-prone gates
# For now, we have 6 groups: (a) preps and meas, (b) MS2, (c) I_idle, (d) I_cross, 
#                            (e) 1-q gates, (f) MS5
#gates_indices = wrapper.gates_list_CNOT_general(latt_circ, faulty_groups)
#print [len(gate_kind) for gate_kind in gates_indices]
#sys.exit(0)

# create the transversal circuit
#CNOT_circ = st.Generator.transversal_CNOT_ion_trap(False, True)
#brow.from_circuit(CNOT_circ, True)
#sys.exit(0)

# Define the list of error-prone gates
# For now, we have 4 groups: (a) I_idle, (b) I_cross, (c) 1-q gates, (d) 2-q MS gates
#circ_list = [CNOT_circ.gates[0].circuit_list[0]]
#gates_indices = wrapper.gates_list_general(circ_list, faulty_groups)
#print [len(gate_kind) for gate_kind in gates_indices]
#sys.exit(0)



def total_perms6(perm_string):
    '''
    '''
    list_perms = []
    for perm in it.permutations(perm_string, 6):
        #new_perm = '_'.join(perm)
        new_perm = map(int,list(perm))
        if new_perm not in list_perms:
            list_perms += [new_perm]

    return list_perms

def total_perms4(perm_string):
    '''
    '''
    list_perms = []
    for perm in it.permutations(perm_string, 4):
        #new_perm = '_'.join(perm)
        #new_perm = '0_' + new_perm + '_0'
        new_perm = map(int,list(perm))
        new_perm = [0] + new_perm + [0]
        if new_perm not in list_perms:
            list_perms += [new_perm]
    
    return list_perms


w1_6, w1_4 = ['100000'], ['1000']
w2_6, w2_4 = ['200000','110000'], ['2000','1100']
w3_6, w3_4 = ['300000','210000','111000'], ['3000','2100','1110']

w_6 = w1_6 + w2_6 + w3_6
w_4 = w1_4 + w2_4 + w3_4

w_perms6, w_perms4 = [[0,0,0,0,0,0]], [[0,0,0,0,0,0]]
for config in w_6:
    w_perms6 += total_perms6(config)

for config in w_4:
    w_perms4 += total_perms4(config)

results_latt = {'pX':{}, 'pZ':{}} 
results_trans = {'pX':{}, 'pZ':{}}

total_jsons = 8
runs_per_json = 5000
total_runs = total_jsons*runs_per_json

latt_folder = output_folder + 'latt_surg/noQEC/XZ/'
for perm in w_perms6:
    if sum(perm) == 0:
        results_latt['pX'][tuple(perm)] = 0.           
        results_latt['pZ'][tuple(perm)] = 0.         
        continue
    perm_folder = latt_folder + '_'.join(map(str,perm)) + '/'
    if sum(perm) == 1:
        if perm[-1] == 0:
            abs_filename = perm_folder + '1.json'
            json_file = open(abs_filename, 'r')
            local_dict = json.load(json_file)
            json_file.close()
            results_latt['pX'][tuple(perm)] = local_dict['p_failX']           
            results_latt['pZ'][tuple(perm)] = local_dict['p_failZ']           
        else:
            results_latt['pX'][tuple(perm)] = 0.           
            results_latt['pZ'][tuple(perm)] = 0.           
            
    else:
        if perm[0]==0 and perm[1]==0 and perm[2]==0 and perm[3]==0 and perm[4]==0:
            results_latt['pX'][tuple(perm)] = 0.           
            results_latt['pZ'][tuple(perm)] = 0.           
        else:
            sum_failX, sum_failZ = 0, 0
            for json_index in range(1,total_jsons+1):
                abs_filename = perm_folder + '%i.json'%json_index
                json_file = open(abs_filename, 'r')
                local_dict = json.load(json_file)
                json_file.close()
                sum_failX += local_dict['n_failsX']
                sum_failZ += local_dict['n_failsZ']
            results_latt['pX'][tuple(perm)] = float(sum_failX)/float(total_runs)           
            results_latt['pZ'][tuple(perm)] = float(sum_failZ)/float(total_runs)           
            

trans_folder = output_folder + 'transversal/noQEC/XZ/'
for perm in w_perms4:
    if sum(perm) == 0:
        results_trans['pX'][tuple(perm)] = 0.
        results_trans['pZ'][tuple(perm)] = 0.
        continue
    abs_filename = trans_folder + '_'.join(map(str,perm)) + '.json'
    json_file = open(abs_filename, 'r')
    local_dict = json.load(json_file)
    json_file.close()
    results_trans['pX'][tuple(perm)] = local_dict['p_failX']
    results_trans['pZ'][tuple(perm)] = local_dict['p_failZ']

   
# Physical error rates
regime = 'future'
T2 = {'current': 200., 'future': 2000.}  # T2 times in ms
T_SM = {'current': 0.08, 'future': 0.03}  # Separation/merging times in ms
# prep/meas, 2qMS, SM, cross, 1q, 5qMS
n_ps_current = [0.001,
                0.01,
                0.5*(1.-math.exp(-T_SM['current']/T2['current'])),
                'p_cross',
                5.e-5,
                0.05]
n_ps_future = [1.e-4,
               2.e-4,
               0.5*(1.-math.exp(-T_SM['future']/T2['future'])),
               'p_cross',
               1.e-5,
               0.001] 

n_ps = {'current': n_ps_current, 'future': n_ps_future}
n_ps = n_ps[regime]


# number of gates in latt-surg CNOT: preps/meas, 2qMS, I_idle, I_cross, 1q, 5qMS.
n_gates_latt = [205, 200, 52908, 827, 428, 33]
# number of gates in transversal CNOT (preps/meas and 5qMS are 0)
n_gates_trans = [7, 1302, 448, 28] 

list_ps = [i*1.e-5 for i in range(1,1000)]
output_string = 'descriptor p_cross pCNOT_phys p_lattX_lower p_lattX_upper p_lattZ_lower p_lattZ_upper p_transX_lower p_transX_upper p_transZ_lower p_transZ_upper\n'
for p in list_ps:
    
    # When generating a Bell pair, 
    # the failure rate after a CNOT is 8p/15 for both X and Z errors
    p_CNOT_phys = n_ps[1]*8./15.  
    
    n_ps[3] = p  # p is the value of p_cross
    p_occurrence_latt_total, p_occurrence_trans_total = 0., 0.
    p_fail_lattX_lower, p_fail_lattZ_lower = 0., 0. 
    p_fail_transX_lower, p_fail_transZ_lower = 0., 0.
    
    # first the lattice surgery
    for perm in w_perms6:
        p_occurrence_latt = wrapper.prob_for_subset_general(n_gates_latt, perm, n_ps)
        p_occurrence_latt_total += p_occurrence_latt
        p_fail_lattX = results_latt['pX'][tuple(perm)]*p_occurrence_latt
        p_fail_lattX_lower += p_fail_lattX 
        p_fail_lattZ = results_latt['pZ'][tuple(perm)]*p_occurrence_latt
        p_fail_lattZ_lower += p_fail_lattZ

    p_fail_lattX_upper = p_fail_lattX_lower + (1.-p_occurrence_latt_total)
    p_fail_lattZ_upper = p_fail_lattZ_lower + (1.-p_occurrence_latt_total)

    # second transversal
    for perm in w_perms4:
        p_occurrence_trans = wrapper.prob_for_subset_general(n_gates_trans, perm[1:5], n_ps[1:5])
        p_occurrence_trans_total += p_occurrence_trans
        p_fail_transX = results_trans['pX'][tuple(perm)]*p_occurrence_trans
        p_fail_transX_lower += p_fail_transX 
        p_fail_transZ = results_trans['pZ'][tuple(perm)]*p_occurrence_trans
        p_fail_transZ_lower += p_fail_transZ
       
    p_fail_transX_upper = p_fail_transX_lower + (1.-p_occurrence_trans_total)
    p_fail_transZ_upper = p_fail_transZ_lower + (1.-p_occurrence_trans_total)

    output_string += '%.15f %.15f %.15f %.15f %.15f %.15f %.15f %.15f %.15f %.15f\n' %(p, p_CNOT_phys, p_fail_lattX_lower, p_fail_lattX_upper, p_fail_lattZ_lower, p_fail_lattZ_upper, p_fail_transX_lower, p_fail_transX_upper, p_fail_transZ_lower, p_fail_transZ_upper)


data_filename = 'comparison_latt_trans_failure_%s.dat' %regime
abs_filename = output_folder + data_filename
data_file = open(abs_filename, 'w')
data_file.write(output_string)
data_file.close()


