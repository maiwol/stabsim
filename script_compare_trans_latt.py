import sys
import json
import itertools as it
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


#FT = True
#CNOT_circuits = qfun.create_latt_surg_CNOT(Is_after2q, initial_I, anc_parallel, EC_ctrl_targ, FT)
#one_q_gates, two_q_gates = wrapper.gates_list_CNOT(CNOT_circuits, error_dict.keys())

#print len(one_q_gates), len(two_q_gates)

#FT = False
#CNOT_circuits = qfun.create_latt_surg_CNOT(Is_after2q, initial_I, anc_parallel, EC_ctrl_targ, FT)
#one_q_gates, two_q_gates = wrapper.gates_list_CNOT(CNOT_circuits, error_dict.keys())

#print len(one_q_gates), len(two_q_gates)

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

w_perms6, w_perms4 = [], []
for config in w_6:
    w_perms6 += total_perms6(config)

for config in w_4:
    w_perms4 += total_perms4(config)

results_latt, results_trans = {'pX':{}, 'pZ':{}}, {'pX':{}, 'pZ':{}}

total_jsons = 8
runs_per_json = 5000
total_runs = total_jsons*runs_per_json

latt_folder = output_folder + 'latt_surg/noQEC/XZ/'
for perm in w_perms6:
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
    abs_filename = trans_folder + '_'.join(map(str,perm)) + '.json'
    json_file = open(abs_filename, 'r')
    local_dict = json.load(json_file)
    json_file.close()
    results_trans['pX'][tuple(perm)] = local_dict['p_failX']
    results_trans['pZ'][tuple(perm)] = local_dict['p_failZ']

   


ps_slow_sampler = {0.002: 0.0617, 0.005: 0.217825, 0.008: 0.38575, 0.0025: 0.08496666666666666, 0.003: 0.1099, 0.004: 0.16507777777777777, 0.006: 0.2751, 0.007: 0.3330416666666667, 0.0015: 0.04088666666666667}
list_ps = [i*1.e-5 for i in range(1,1000)]
output_string = 'descriptor p pCNOT_p p_CNOT_l_nonFT p_CNOT_l_FT p_CNOT_l_FT2 p_CNOT_l_FTslow error_nonFT errorFT worst_case_FT worst_case_nonFT\n'
for p in list_ps:
    p_occurrence_FT_total, p_occurrence_nonFT_total = 0., 0.
    p_fail_FT, p_fail_nonFT = 0., 0.
    for pair in list_errors:
        p_occurrence_FT = wrapper.prob_for_subset(p, p, 652, 786, pair[0], pair[1])
        p_occurrence_FT_total += p_occurrence_FT
        p_fail_FT_local = results_FT[(pair[0], pair[1])]*p_occurrence_FT
        p_fail_FT += p_fail_FT_local
        
        p_occurrence_nonFT = wrapper.prob_for_subset(p, p, 56, 42, pair[0], pair[1])
        p_occurrence_nonFT_total += p_occurrence_nonFT
        p_fail_nonFT_local = results_nonFT[(pair[0], pair[1])]*p_occurrence_nonFT
        p_fail_nonFT += p_fail_nonFT_local
   
    worst_case_FT = p_fail_FT + (1.-p_occurrence_FT_total)
    worst_case_nonFT = p_fail_nonFT + (1.-p_occurrence_nonFT_total)

    error_FT = (1.-p_occurrence_FT_total)/p_occurrence_FT_total
    error_nonFT = (1.-p_occurrence_nonFT_total)/p_occurrence_nonFT_total
    if p < 0.002:
        if p in ps_slow_sampler:
            output_string += '%f nan %f %f nan %f %f %f %f %f\n' %(p, p_fail_nonFT, p_fail_FT, ps_slow_sampler[p], 100*error_nonFT, 100*error_FT, worst_case_FT, worst_case_nonFT)
        else:
            output_string += '%f nan %f %f nan nan %f %f %f %f\n' %(p, p_fail_nonFT, p_fail_FT, 100*error_nonFT, 100*error_FT, worst_case_FT, worst_case_nonFT)
    else:
        if p in ps_slow_sampler:
            output_string += '%f nan %f nan %f %f %f %f %f %f\n' %(p, p_fail_nonFT, p_fail_FT, ps_slow_sampler[p], 100*error_nonFT, 100*error_FT, worst_case_FT, worst_case_nonFT)
        else:
            output_string += '%f nan %f nan %f nan %f %f %f %f\n' %(p, p_fail_nonFT, p_fail_FT, 100*error_nonFT, 100*error_FT, worst_case_FT, worst_case_nonFT)

data_filename = 'resultsCNOT.dat'
abs_filename = output_folder + data_filename
data_file = open(abs_filename, 'w')
data_file.write(output_string)
data_file.close()


#for i in range(5):
#    for j in range(5):
#        p_local = wrapper.prob_for_subset(p1q, p2q, ns, nt, i, j)
#        p_total += p_local
#        print i,j, p_local
#print p_total
#print 100*(1.-p_total)/p_total
