import sys
import json
import steane
import surface17 as surf17
import d5color
import correction as cor
import chper_wrapper as wrapper
import qcircuit_functions as qfun


error_model = 'standard'
output_folder = './MC_results/QECd3_flags/one_flag/' + error_model + '/'
p1q, p2q = 0.01, 0.01
error_dict, Is_after2q, Is_after_1q = wrapper.dict_for_error_model(error_model, p1q, p2q, p1q)

initial_I = True
QECd3_flags_circ = cor.Flag_Correct.generate_whole_QEC_Reichardt_special(True, 
                                                                         False,
                                                                         initial_I)
QEC_circ_list = []
for i in range(len(QECd3_flags_circ.gates)):
    QEC_circ_list += [QECd3_flags_circ.gates[i].circuit_list[0]]
one_q_gates, two_q_gates = wrapper.gates_list(QEC_circ_list, error_dict.keys())
n_oneq, n_twoq = len(one_q_gates), len(two_q_gates)
#print n_oneq
#print n_twoq
#sys.exit(0)

# diVincenzo new (only 2 reps)
QEC_circ = qfun.create_EC_subcircs('Steane', False, initial_I, False, False, 2)
QEC_circ = QEC_circ.gates[0].circuit_list[0]
QEC_circ_list = []
for i in range(len(QEC_circ.gates)):
    QEC_circ_list += [QEC_circ.gates[i].circuit_list[0]]
one_q_gates, two_q_gates = wrapper.gates_list(QEC_circ_list, error_dict.keys())
n_oneq_diVin_new, n_twoq_diVin_new = len(one_q_gates), len(two_q_gates)
#print '1-q surf17 =', n_oneq_diVin_new
#print '2-q surf17 =', n_twoq_diVin_new
#sys.exit(0)

# all flags (1 flag/stab)
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
one_q_gates, two_q_gates = wrapper.gates_list(QEC_circ_list, error_dict.keys())
n_oneq_all_flags, n_twoq_all_flags = len(one_q_gates), len(two_q_gates)

# surface17
surface17_stabs = surf17.Code.stabilizers[:]
QEC_circ = cor.Bare_Correct.generate_rep_bare_meas(9, surface17_stabs, 2, initial_I, True,
                                                   Is_after2q, False, False, True)
QEC_circ_list = []
for supra_gate in QEC_circ.gates:
    QEC_circ_list += [supra_gate.circuit_list[0]]
one_q_gates, two_q_gates = wrapper.gates_list(QEC_circ_list, error_dict.keys())
n_oneq_surf17, n_twoq_surf17 = len(one_q_gates), len(two_q_gates)
#print '1-q surf17 =', n_oneq_surf17
#print '2-q surf17 =', n_twoq_surf17


# d5 color code
d5_stabs = d5color.Code.stabilizer_alt[:]
flags_oct = [[1,6], [2,7]]
flags_sq = [[1,3]]
flags_list_d5 = [flags_oct] + [flags_sq for i in range(7)]
QEC_circ = cor.Flag_Correct.generate_whole_QEC_circ(4, d5_stabs, flags_list_d5+flags_list_d5,
                                                True, False, 17, True, False, True)
QEC_circ_list = []
for log_gate in QEC_circ.gates:
    for gate in log_gate.circuit_list[0].gates:
        QEC_circ_list += [gate.circuit_list[0]]

# Define the list of error-prone 1-q and 2-q gates
one_q_gates, two_q_gates = wrapper.gates_list(QEC_circ_list, error_dict.keys())
n_oneq_colord5, n_twoq_colord5 = len(one_q_gates), len(two_q_gates)
print '1-q colord5 =', n_oneq_colord5
print '2-q colord5 =', n_twoq_colord5
#sys.exit(0)

#list_errors = [[0,0], [1,0], [0,1], [2,0], [1,1], [0,2], [3,0], [2,1], [1,2], [0,3],
#               [4,0], [3,1], [2,2], [1,3], [0,4], [5,0], [4,1], [3,2], [2,3], [1,4],
#               [0,5], [6,0], [5,1], [4,2], [3,3], [2,4], [1,5], [0,6]]
list_errors = [[0,0], [1,0], [0,1], [2,0], [1,1], [0,2], [3,0], [2,1], [1,2], [0,3],
               [4,0], [3,1], [2,2], [1,3], [0,4]]
#list_errors = [[0,0], [1,0], [0,1], [2,0], [1,1], [0,2]]


# Read the results from the fast sampler
results_QECd3_flags = {}
for pair in list_errors:
    json_filename = str(pair[0]) + '_' + str(pair[1]) + '.json'
    abs_filename = output_folder + json_filename
    json_file = open(abs_filename, 'r')
    local_dict = json.load(json_file)
    json_file.close()
    results_QECd3_flags[(pair[0], pair[1])] = local_dict['p_fail']

# Read the results from the new diVincenzo (only 2 reps)
results_QECd3_diVin_new = {}
for pair in list_errors:
    input_folder = './MC_results/QECd3_diVin_new/' + error_model + '/'
    json_filename = str(pair[0]) + '_' + str(pair[1]) + '.json'
    abs_filename = input_folder + json_filename
    json_file = open(abs_filename, 'r')
    local_dict = json.load(json_file)
    json_file.close()
    results_QECd3_diVin_new[(pair[0], pair[1])] = local_dict['p_fail']

# Read the results from the flags with 1 flag/stab
results_QECd3_all_flags = {}
for pair in list_errors:
    input_folder = './MC_results/QECd3_flags/all_flags/' + error_model + '/'
    json_filename = str(pair[0]) + '_' + str(pair[1]) + '.json'
    abs_filename = input_folder + json_filename
    json_file = open(abs_filename, 'r')
    local_dict = json.load(json_file)
    json_file.close()
    results_QECd3_all_flags[(pair[0], pair[1])] = local_dict['p_fail']

# Read the results from the surface17
results_QECd3_surf17 = {}
for pair in list_errors:
    input_folder = './MC_results/QECd3_surface17/' + error_model + '/'
    json_filename = str(pair[0]) + '_' + str(pair[1]) + '.json'
    abs_filename = input_folder + json_filename
    json_file = open(abs_filename, 'r')
    local_dict = json.load(json_file)
    json_file.close()
    results_QECd3_surf17[(pair[0], pair[1])] = local_dict['p_fail']


# Read the old results from the diVincenzo EC
extra_input_folder = '/home/mau/Desktop/FTQEC-master/MC_results/ShorEC/' + error_model + '/'
extra_filename = 'results.dat'
extra_filename = extra_input_folder + extra_filename
extra_file = open(extra_filename, 'r')
results_diVin = {}
for line in extra_file:
    split_line = line.split()
    try:
        p, p_diVin = float(split_line[0]), float(split_line[2])
    except ValueError:
        continue
    results_diVin[p] = p_diVin
extra_file.close()


# Now the distance-5 codes
# Read the results from the d-5 color code
results_QECd5_color = {}
for pair in list_errors:
    input_folder = './MC_results/QECd5_flags/' + error_model + '/'
    json_filename = str(pair[0]) + '_' + str(pair[1]) + '.json'
    abs_filename = input_folder + json_filename
    json_file = open(abs_filename, 'r')
    local_dict = json.load(json_file)
    json_file.close()
    results_QECd5_color[(pair[0], pair[1])] = local_dict['p_fail']




    
# Create the output dat file
list_ps = [i*1.e-5 for i in range(1,1000)]
output_string = 'descriptor p p_0 p_d3_flag_lower p_d3_flag_upper p_diVin p_diVin_new p_d3_flag_all p_surf17 p_surf17_upper p_d5_color p_d5_color_upper\n'
for p in list_ps:
    p_occurrence_total, p_occ_total_diVin_new, p_occ_total_all_flags, p_occ_surf, p_occ_d5color = 0.,0.,0.,0.,0.
    p_fail_total, p_fail_total_diVin_new, p_fail_total_all_flags, p_fail_total_surf, p_fail_total_d5color = 0.,0.,0.,0.,0.
    for pair in list_errors:
        p_occurrence = wrapper.prob_for_subset(p, p, n_oneq, n_twoq, pair[0], pair[1])
        p_occurrence_total += p_occurrence
        p_fail = results_QECd3_flags[(pair[0], pair[1])]*p_occurrence
        p_fail_total += p_fail
        
        #diVin_new
        p_occurrence = wrapper.prob_for_subset(p, p, n_oneq_diVin_new, n_twoq_diVin_new,
                                               pair[0], pair[1])
        p_occ_total_diVin_new += p_occurrence
        p_fail = results_QECd3_diVin_new[(pair[0], pair[1])]*p_occurrence
        p_fail_total_diVin_new += p_fail
        
        # all_flags
        p_occurrence = wrapper.prob_for_subset(p, p, n_oneq_all_flags, n_twoq_all_flags,
                                               pair[0], pair[1])
        p_occ_total_all_flags += p_occurrence
        p_fail = results_QECd3_all_flags[(pair[0], pair[1])]*p_occurrence
        p_fail_total_all_flags += p_fail
        
        # surf17
        p_occurrence = wrapper.prob_for_subset(p, p, n_oneq_surf17, n_twoq_surf17,
                                               pair[0], pair[1])
        p_occ_surf += p_occurrence
        p_fail = results_QECd3_surf17[(pair[0], pair[1])]*p_occurrence
        p_fail_total_surf += p_fail
   
        # d5color
        p_occurrence = wrapper.prob_for_subset(p, p, n_oneq_colord5, n_twoq_colord5,
                                               pair[0], pair[1])
        p_occ_d5color += p_occurrence
        p_fail = results_QECd5_color[(pair[0], pair[1])]*p_occurrence
        p_fail_total_d5color += p_fail
    
    
    p_upper = p_fail_total + (1.-p_occurrence_total)
    p_upper_surf17 = p_fail_total_surf + (1.-p_occ_surf)
    p_upper_d5color = p_fail_total_d5color + (1.-p_occ_d5color)

    if p in results_diVin:
        p_diVin = str(results_diVin[p])
    else:
        p_diVin = 'nan'
    
    output_string += '%f %f %.15f %.15f %s %.15f %.15f %.15f %.15f %.15f %.15f\n' %(p, 2*p/3, p_fail_total, p_upper, p_diVin, p_fail_total_diVin_new, p_fail_total_all_flags, p_fail_total_surf, p_upper_surf17, p_fail_total_d5color, p_upper_d5color)


data_filename = 'resultsQECd3_flags_all_results.dat'
abs_filename = output_folder + data_filename
data_file = open(abs_filename, 'w')
data_file.write(output_string)
data_file.close()


