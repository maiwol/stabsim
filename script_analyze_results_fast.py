import sys
import json
import chper_wrapper as wrapper
import qcircuit_functions as qfun


#p1q, p2q = float(sys.argv[1]), float(sys.argv[2])
#ns, nt = float(sys.argv[3]), float(sys.argv[4])
error_model = 'standard'
output_folder = './MC_results/latt_CNOT/' + error_model + '/'
initial_I = True
anc_parallel = True
EC_ctrl_targ = False
p1q, p2q = 0.01, 0.01
error_dict, Is_after2q, Is_after_1q = wrapper.dict_for_error_model(error_model, p1q, p2q, p1q)

#FT = True
#CNOT_circuits = qfun.create_latt_surg_CNOT(Is_after2q, initial_I, anc_parallel, EC_ctrl_targ, FT)
#one_q_gates, two_q_gates = wrapper.gates_list_CNOT(CNOT_circuits, error_dict.keys())

#print len(one_q_gates), len(two_q_gates)

#FT = False
#CNOT_circuits = qfun.create_latt_surg_CNOT(Is_after2q, initial_I, anc_parallel, EC_ctrl_targ, FT)
#one_q_gates, two_q_gates = wrapper.gates_list_CNOT(CNOT_circuits, error_dict.keys())

#print len(one_q_gates), len(two_q_gates)


list_errors = [[1,0]]
results_FT, results_nonFT = {}, {}
for pair in list_errors:
    json_filename = 'FT_' + str(pair[0]) + '_' + str(pair[1]) + '.json'
    abs_filename = output_folder + json_filename
    json_file = open(abs_filename, 'r')
    local_dict = json.load(json_file)
    json_file.close()
    results_FT[(pair[0], pair[1])] = local_dict['p_fail']
        
    json_filename = 'nonFT_' + str(pair[0]) + '_' + str(pair[1]) + '.json'
    abs_filename = output_folder + json_filename
    json_file = open(abs_filename, 'r')
    local_dict = json.load(json_file)
    json_file.close()
    results_nonFT[(pair[0], pair[1])] = local_dict['p_fail']
    

list_ps = [1.e-5, 1.e-4, 1.e-3]
output_string = 'descriptor p pCNOT_p p_CNOT_l_nonFT p_CNOT_l_FT error_nonFT errorFT\n'
for p in list_ps:
    p_occurrence_FT_total, p_occurrence_nonFT_total = 0., 0.
    p_fail_FT, p_fail_nonFT = 0., 0.
    for pair in results_FT:
        p_occurrence_FT = wrapper.prob_for_subset(p, p, 652, 786, pair[0], pair[1])
        p_occurrence_FT_total += p_occurrence_FT
        p_fail_FT_local = results_FT[(pair[0], pair[1])]*p_occurrence_FT
        p_fail_FT += p_fail_FT_local
        
        p_occurrence_nonFT = wrapper.prob_for_subset(p, p, 56, 42, pair[0], pair[1])
        p_occurrence_nonFT_total += p_occurrence_nonFT
        p_fail_nonFT_local = results_nonFT[(pair[0], pair[1])]*p_occurrence_nonFT
        p_fail_nonFT += p_fail_nonFT_local
    
    error_FT = (1.-p_occurrence_FT_total)/p_occurrence_FT_total
    error_nonFT = (1.-p_occurrence_nonFT_total)/p_occurrence_nonFT_total
    output_string += '%f nan %f %f %f %f\n' %(p, p_fail_nonFT, p_fail_FT, error_nonFT, error_FT)

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
