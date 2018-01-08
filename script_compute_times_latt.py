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
w4_6, w4_4 = ['400000','310000','220000','211000','111100'], ['4000','3100','2200','2110','1111']
w5_6 = ['500000','410000','320000','311000','221000','211100','111110']
w6_6 = ['600000','510000']

w5_4 = ['5000','4100','3200','3110','2210','2111']
w6_4 = ['6000','5100','4200','4110','3300','3210','3111','2220','2211']
w7_4 = ['7000','6100','5200','5110','4300','4210','4111','3310','3211']

w_6 = w1_6 + w2_6 + w3_6 + w4_6 + w5_6 + w6_6
w_4 = w1_4 + w2_4 + w3_4 + w4_4 + w5_4 + w6_4 + w7_4 

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


# Total dictionaries
dict_cross = {}
dict_twoq = {}
dict_oneq = {}
dict_fiveq = {}
dict_meas = {}
dict_prep = {}
dict_reor = {}

# Dictionaries for the first subcircuit (Measure XX)
cross0_QEC = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0}
twoq0_QEC = {0:6, 1:6, 2:6, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0}
oneq0_QEC = {0:8, 1:8, 2:8, 3:0, 4:0, 5:3, 6:3, 7:3, 8:0, 9:0}
fiveq0_QEC = {0:0, 1:0, 2:0, 3:0, 4:0, 5:2, 6:2, 7:2, 8:0, 9:0}
meas0_QEC = {0:2, 1:2, 2:2, 3:0, 4:0, 5:1, 6:1, 7:1, 8:0, 9:0}
prep0_QEC = {0:2, 1:2, 2:2, 3:0, 4:0, 5:1, 6:1, 7:1, 8:0, 9:0}
reor0_QEC = {0:36, 1:43, 2:45, 3:7, 4:10, 5:5, 6:12, 7:14, 8:7, 9:10}

cross0 = {0:1, 1:0, 2:1, 3:1, 4:4, 5:2, 6:0, 7:2, 8:2, 9:cross0_QEC, 10:cross0_QEC, 11:2, 12:4}
twoq0 = {0:2, 1:2, 2:0, 3:2, 4:4, 5:4, 6:4, 7:0, 8:4, 9:twoq0_QEC, 10:twoq0_QEC, 11:2, 12:4}
oneq0 = {0:2, 1:2, 2:0, 3:2, 4:4, 5:4, 6:4, 7:0, 8:4, 9:oneq0_QEC, 10:oneq0_QEC, 11:2, 12:4}
fiveq0 = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:fiveq0_QEC, 10:fiveq0_QEC, 11:0, 12:0}
meas0 = {0:1, 1:1, 2:0, 3:1, 4:1, 5:1, 6:1, 7:0, 8:1, 9:meas0_QEC, 10:meas0_QEC, 11:1, 12:1}
prep0 = {0:1, 1:1, 2:0, 3:1, 4:1, 5:1, 6:1, 7:0, 8:1, 9:prep0_QEC, 10:prep0_QEC, 11:1, 12:1}
reor0 = {0:20, 1:19, 2:12, 3:22, 4:32, 5:37, 6:37, 7:12, 8:37, 9:reor0_QEC, 10:reor0_QEC, 11:21, 12:32}

# Dictionaries for the second subcircuit (Joint QECZ)
cross1_QEC = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0, 13:0}
twoq1_QEC = {0:6, 1:6, 2:6, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0, 13:0}
oneq1_QEC = {0:16, 1:16, 2:16, 3:0, 4:0, 5:11, 6:11, 7:11, 8:0, 9:11, 10:11, 11:11, 12:0, 13:0}
fiveq1_QEC = {0:0, 1:0, 2:0, 3:0, 4:0, 5:2, 6:2, 7:2, 8:0, 9:2, 10:2, 11:2, 12:0, 13:0}
meas1_QEC = {0:2, 1:2, 2:2, 3:0, 4:0, 5:1, 6:1, 7:1, 8:0, 9:1, 10:1, 11:1, 12:0, 13:0}
prep1_QEC = {0:2, 1:2, 2:2, 3:0, 4:0, 5:1, 6:1, 7:1, 8:0, 9:1, 10:1, 11:1, 12:0, 13:0}
reor1_QEC = {0: 36, 1:43, 2:45, 3:7, 4:9, 5:5, 6:12, 7:14, 8:9, 9:5, 10:12, 11:14, 12:7, 13:10}

cross1 = {0:cross1_QEC, 1:cross1_QEC}
twoq1 = {0:twoq1_QEC, 1:twoq1_QEC}
oneq1 = {0:oneq1_QEC, 1:oneq1_QEC}
fiveq1 = {0:fiveq1_QEC, 1:fiveq1_QEC}
meas1 = {0:meas1_QEC, 1:meas1_QEC}
prep1 = {0:prep1_QEC, 1:prep1_QEC}
reor1 = {0:reor1_QEC, 1:reor1_QEC}

# Dictionaries for the third subcircuit (Measure ZZ)
oneq2_QEC = {0:16, 1:16, 2:16, 3:0, 4:0, 5:11, 6:11, 7:11, 8:0, 9:0}

cross2 = {0:1, 1:0, 2:1, 3:1, 4:4, 5:2, 6:0, 7:2, 8:2, 9:cross0_QEC, 10:cross0_QEC, 11:2, 12:4}
twoq2 = {0:2, 1:2, 2:0, 3:2, 4:4, 5:4, 6:4, 7:0, 8:4, 9:twoq0_QEC, 10:twoq0_QEC, 11:2, 12:4}
oneq2 = {0:2, 1:2, 2:0, 3:2, 4:4, 5:4, 6:4, 7:0, 8:4, 9:oneq2_QEC, 10:oneq2_QEC, 11:2, 12:4}
fiveq2 = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:fiveq0_QEC, 10:fiveq0_QEC, 11:0, 12:0}
meas2 = {0:1, 1:1, 2:0, 3:1, 4:1, 5:1, 6:1, 7:0, 8:1, 9:meas0_QEC, 10:meas0_QEC, 11:1, 12:1}
prep2 = {0:1, 1:1, 2:0, 3:1, 4:1, 5:1, 6:1, 7:0, 8:1, 9:prep0_QEC, 10:prep0_QEC, 11:1, 12:1}
reor2 = {0:18, 1:18, 2:12, 3:18, 4:34, 5:34, 6:34, 7:12, 8:34, 9:reor0_QEC, 10:reor0_QEC, 11:18, 12:34}

# Dictionaries for the fourth subcircuit
oneq3_QEC = {0:8, 1:8, 2:8, 3:0, 4:0, 5:3, 6:3, 7:3, 8:0, 9:3, 10:3, 11:3, 12:0, 13:0}

cross3 = {0:cross1_QEC, 1: dict([(key, cross1_QEC[key]) for key in cross1_QEC.keys()[:9])}
twoq3 = {0:twoq1_QEC, 1: dict([(key, twoq1_QEC[key]) for key in twoq1_QEC.keys()[:9])}
oneq3 = {0:oneq3_QEC, 1: dict([(key, oneq3_QEC[key]) for key in oneq1_QEC.keys()[:9])}
fiveq3 = {0:fiveq1_QEC, 1: dict([(key, fiveq1_QEC[key]) for key in fiveq1_QEC.keys()[:9])}
meas3 = {0:meas1_QEC, 1: dict([(key, meas1_QEC[key]) for key in meas1_QEC.keys()[:9])}
prep3 = {0:prep1_QEC, 1: dict([(key, prep1_QEC[key]) for key in prep1_QEC.keys()[:9])}
reor3 = {0:reor1_QEC, 1: dict([(key, reor1_QEC[key]) for key in reor1_QEC.keys()[:9])}

# Dictionaries for fifth subcircuit
cross4 = {0:0}
twoq4 = {0:0}
oneq4 = {0:7}  # even though we're just doing MeasureX in the circuit itself
fiveq4 = {0:0}
meas4 = {0:7}
prep4 = {0:0}
reor4 = {0:0}

# Complete dictionaries
dict_cross = {0:cross0, 1:cross1, 2:cross2, 3:cross3, 4:cross4}
dict_twoq = {0:twoq0, 1:twoq1, 2:twoq2, 3:twoq3, 4:twoq4}
dict_oneq = {0:oneq0, 1:oneq1, 2:oneq2, 3:oneq3, 4:oneq4}
dict_fiveq = {0:fiveq0, 1:fiveq1, 2:fiveq2, 3:fiveq3, 4:fiveq4}
dict_meas = {0:meas0, 1:meas1, 2:meas2, 3:meas3, 4:meas4}
dict_prep = {0:prep0, 1:prep1, 2:prep2, 3:prep3, 4:prep4}
dict_reor = {0:reor0, 1:reor1, 2:reor2, 3:reor3, 4:reor4}
resource_dict_list = [dict_cross, dict_twoq, dict_oneq, dict_fiveq, 
                      dict_meas, dict_prep, dict_reor]
n_resources = len(resource_dict_list)


latt_folder = output_folder + 'latt_surg/noQEC/XZ/'
for perm in w_perms6:
    #if sum(perm) == 0:
        #results_latt['pX'][tuple(perm)] = 0.           
        #results_latt['pZ'][tuple(perm)] = 0.         
        #continue
    
    perm_folder = latt_folder + '_'.join(map(str,perm)) + '/'

    
    clause1 = perm[0]==0 and perm[1]==0 and perm[2]==0 and perm[3]==0 and perm[4]==0
    clause2 = sum(perm)==1 and perm!=[0,0,1,0,0,0]

    if clause1 or clause2:
        # for all of these permutations there is only 1 subcirc dict.
        if clause1:
            # for these permutations the resources are the same.  We get the numbers from
            # 0_0_0_0_0_2.
            perm_folder = latt_folder + '0_0_0_0_0_2/'
        
        abs_filename = perm_folder + '1.json'
        json_file = open(abs_filename, 'r')
        local_dict = json.load(json_file)
        json_file.close()

        subcirc_dict = local_dict['subcircs_run']
        resources_perm = [] 
        for resource_dict in resource_dict_list:
            resources_local = qfun.add_dict_resources_latt_surg(subcirc_dict,
                                                                resource_dict,
                                                                local_dict['n_total'])
            resources_perm += [float(resources_local)/float(local_dict['n_total'])]

    else:
        # all the other permutations have 8 subcirc dicts.

        resources_perm = [0 for i in range(n_resources)]
        for json_index in range(1,total_jsons+1):
            abs_filename = perm_folder + '%i.json'%json_index
            json_file = open(abs_filename, 'r')
            local_dict = json.load(json_file)
            json_file.close()

            subcirc_dict = local_dict['subcircs_run']
            resources_local_local_list = [] 
            for resource_dict in resource_dict_list:
                resources_local = qfun.add_dict_resources_latt_surg(subcirc_dict,
                                                                    resource_dict,
                                                                    local_dict['n_total'])
                resources_local_list += [float(resources_local)/float(local_dict['n_total'])]
            
            for i in range(n_resources):
                resources_perm[i] += resources_local_list[i]


            

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

    if p < 0.003:
        output_string += '%.15f %.15f %.15f %.15f %.15f %.15f %.15f %.15f %.15f %.15f\n' %(p, p_CNOT_phys, p_fail_lattX_lower, p_fail_lattX_upper, p_fail_lattZ_lower, p_fail_lattZ_upper, p_fail_transX_lower, p_fail_transX_upper, p_fail_transZ_lower, p_fail_transZ_upper)
    else:
        output_string += '%.15f %.15f nan nan nan nan nan nan %.15f %.15f\n' %(p, p_CNOT_phys, p_fail_transZ_lower, p_fail_transZ_upper)


data_filename = 'comparison_latt_trans_failure_%s.dat' %regime
abs_filename = output_folder + data_filename
data_file = open(abs_filename, 'w')
data_file.write(output_string)
data_file.close()


