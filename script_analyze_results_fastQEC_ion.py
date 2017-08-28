import sys
import json
import scipy
import steane
import correction as cor
import chper_wrapper as wrapper
import qcircuit_functions as qfun


alternating = True
error_model = 'ion_trap_eQual'
output_folder = './'
# These error rates don't matter for the fast sampler
p1, p2, p_meas, p_prep, p_sm, p_cool = 0.1, 0.1, 0.1, 0.1, 0.1, 0.1
error_dict, Is_after2q, Is_after1q, faulty_groups = wrapper.dict_for_error_model(
                                                         error_model=error_model,
                                                         p_1q=p1, p_2q=p2,
                                                         p_meas=p_meas, p_prep=p_prep,
                                                         p_sm=p_sm, p_cool=p_cool)

data_folder = './MC_results/QECd3_flags/all_flags/ion_trap1/'


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
                                                      dephasing_during_MS)
#brow.from_circuit(QEC_circ, True)
QEC_circ_list = []
for log_gate in QEC_circ.gates:
    QEC_circ_list += [log_gate.circuit_list[0]]

# Define the list of error-prone gates
# For now, we have 4 groups: (a) preps and meas, (b) shuttling and merging
# (c) cooling, and (d) MS gates.
prep_meas_g, shut_g, cool_g, MS_g = wrapper.gates_list_general(QEC_circ_list, faulty_groups)
gate_indices = [prep_meas_g, shut_g, cool_g, MS_g]
n_gates = [len(gate_kind) for gate_kind in gate_indices]


# List of error subsets
list_errors1_2 = [[0,0,0,0], [0,0,0,1], [0,0,1,0], [0,1,0,0], [1,0,0,0], [0,0,0,2], [0,0,2,0], 
                  [0,2,0,0], [2,0,0,0], [1,1,0,0], [1,0,1,0], [1,0,0,1], [0,1,1,0], [0,1,0,1], 
                  [0,0,1,1]]
list_errors3 = [[0,0,0,3], [0,0,3,0], [0,3,0,0], [3,0,0,0], [2,1,0,0], [2,0,1,0], [2,0,0,1],
                [1,2,0,0], [0,2,1,0], [0,2,0,1], [1,0,2,0], [0,1,2,0], [0,0,2,1], [1,0,0,2], 
                [0,1,0,2], [0,0,1,2], [0,1,1,1], [1,0,1,1], [1,1,0,1], [1,1,1,0]]
list_errors4 = [[0,0,0,4], [0,0,4,0], [0,4,0,0], [4,0,0,0], [3,1,0,0], [3,0,1,0], [3,0,0,1], 
                [1,3,0,0], [0,3,1,0], [0,3,0,1], [1,0,3,0], [0,1,3,0], [0,0,3,1], [1,0,0,3], 
                [0,1,0,3], [0,0,1,3], [2,0,1,1], [2,1,0,1], [2,1,1,0], [0,2,1,1], [1,2,0,1], 
                [1,2,1,0], [0,1,2,1], [1,0,2,1], [1,1,2,0], [0,1,1,2], [1,0,1,2], [1,1,0,2], 
                [1,1,1,1]]


list_errors = list_errors1_2 + list_errors3 + list_errors4


# Read the results from the alternating
results_alternating = {}
for subset in list_errors:
    json_filename = '_'.join(map(str,subset)) + '.json'
    abs_filename = data_folder + 'alternating/' + json_filename
    json_file = open(abs_filename, 'r')
    local_dict = json.load(json_file)
    json_file.close()
    results_alternating[tuple(subset)] = local_dict['p_fail']
    if sum(subset) == 2:
        A = [scipy.misc.comb(n_gates[i],subset[i]) for i in range(len(subset))]
        prod_A = 1
        for prod in A:
            prod_A *= prod
        #print 'subset =', subset
        #print 'prod_A =', prod_A
        #print 'prefactor =', prod_A*local_dict['p_fail']
        #print '\n'



# Read the results from the non-alternating
#results_nonalternating = {}
#for pair in list_errors:
#    json_filename = '_'.join(map(str,subset)) + '.json'
#    abs_filename = data_folder + 'non_alternating/' + json_filename
#    json_file = open(abs_filename, 'r')
#    local_dict = json.load(json_file)
#    json_file.close()
#    results_nonalternating[tuple(subset)] = local_dict['p_fail']




# T2 dephasing (in ms)
T2 = 15.6


# Create the output dat file
list_ps = [i*1.e-3 for i in range(0,1000)]
output_string = 'descriptor p p_0 p_lower_alter p_upper_alter\n'
for p in list_ps:
    p_occurrence_total = 0.
    p_fail_total = 0.
    for subset in list_errors:
        
        p_prep = 0.001 + 0.004*p
        p_shut = (0.5/T2)*(0.03 + 0.05*p)
        p_cool = (0.5/T2)*(0.1 + 0.3*p)
        p_MS = 0.0004 + 0.0296*p
        n_ps = [p_prep, p_shut, p_cool, p_MS]

        p_occurrence = wrapper.prob_for_subset_general(n_gates, subset, n_ps)
        p_occurrence_total += p_occurrence
        p_fail = results_alternating[tuple(subset)]*p_occurrence
        p_fail_total += p_fail
        #print p_occurrence 
   
    p_upper = p_fail_total + (1.-p_occurrence_total)

    output_string += '%.15f %.15f %.15f %.15f\n' %(p, p_prep, p_fail_total, p_upper)


data_filename = 'resultsQECd3_flags_ion.dat'
abs_filename = data_folder + data_filename
data_file = open(abs_filename, 'w')
data_file.write(output_string)
data_file.close()


list_ps = [i*1.e-3 for i in range(1,1000)]
output_string = 'descriptor p p_0 p_lower_alter p_upper_alter\n'
for p in list_ps:
    p_occurrence_total = 0.
    p_fail_total = 0.
    for subset in list_errors:
        
        p_prep = 0.005*p
        p_shut = (0.5/T2)*(0.08*p)
        p_cool = (0.5/T2)*(0.4*p)
        p_MS = 0.03*p
        n_ps = [p_prep, p_shut, p_cool, p_MS]

        p_occurrence = wrapper.prob_for_subset_general(n_gates, subset, n_ps)
        p_occurrence_total += p_occurrence
        p_fail = results_alternating[tuple(subset)]*p_occurrence
        p_fail_total += p_fail
        print p_occurrence 
   
    p_upper = p_fail_total + (1.-p_occurrence_total)

    output_string += '%.15f %.15f %.15f %.15f\n' %(p, p_prep, p_fail_total, p_upper)


data_filename = 'resultsQECd3_flags_ion2.dat'
abs_filename = data_folder + data_filename
data_file = open(abs_filename, 'w')
data_file.write(output_string)
data_file.close()



