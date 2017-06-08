import sys
import numpy as np
import json
import itertools as it
import schedule_functions as sched_fun


# total number of physical qubits
n_total = 17

d5_stabs = [
              [2,3,6,5,10,9,13,14],
              [6,7,10,11],
              [10,11,14,15],
              [7,11,15,16],
              [0,1,2,3],
              [0,2,4,5],
              [4,5,8,9],
              [8,9,12,13]
           ]

logical_oper = range(n_total)
log_bin = sched_fun.convert_to_binary(logical_oper)

# Errors
errors_0 = [[]]
errors_1 = [[i] for i in range(n_total)]
errors_2 = []
for i in range(n_total):
    for j in range(i+1, n_total):
        errors_2 += [[i,j]]

total_errors = errors_0 + errors_1 + errors_2
    

# Trivial lookuptable is the basis of every dictionary.
# It includes only the trivial syndrome.
trivial_lookup = {}
for err in errors_0:
    err_bin = sched_fun.convert_to_binary(err, n_total)
    syn = tuple(sched_fun.error_to_syndrome(err_bin, n_total, d5_stabs[:]))
    trivial_lookup[syn] = err_bin
    
# Basic lookuptable is the basis of every dictionary.
# It includes the trivial syndrome and all 1-q errors.
basic_lookup = {}
for err in errors_0 + errors_1:
    err_bin = sched_fun.convert_to_binary(err, n_total)
    syn = tuple(sched_fun.error_to_syndrome(err_bin, n_total, d5_stabs[:]))
    basic_lookup[syn] = err_bin


# dict_noflag is the dictionary when no flags are triggered.
# First, we add the I, 1-q, and 2-q errors.
dict_noflag = {}
for err in total_errors:
    err_bin = sched_fun.convert_to_binary(err, n_total)
    syn = tuple(sched_fun.error_to_syndrome(err_bin, n_total, d5_stabs[:]))
    dict_noflag[syn] = err_bin




def basic_dict1(sched, flags=[1,3], n_total=17, stabs=d5_stabs[:],
                extra_errors=[]):
    '''
    computes the basic dictionary when the stabilizer given by
    sched triggers a flag.  Basic dictionary means that we don't
    try to complete all the 2^8 syndromes, just the ones necessary
    to correct for 1-q and 2-q error events.  
    
    The second argument, flags, gives the location of the two-qubit 
    gates from the ancilla qubit to the flag qubit.  
    For example, [1,3] means that the first CNOT occurs before the 
    second gate and the second CNOT occurs before the third gate.
   
    extra_errors are other errors, apart from the 1-q erros, that
    can occur with probability O(p).  For example, when the octagon
    has flags [2,6], (0,1) and (6,7) are extra_errors.

    returns True, dict1  if it's possible to construct the dict
            False, {}    if it's not possible.
    '''

    sched = list(sched)

    dict1 = dict(basic_lookup)
    for extra_error in extra_errors:
        extra_bin = sched_fun.convert_to_binary(extra_error, n_total)
        syn = tuple(sched_fun.error_to_syndrome(extra_bin, n_total, stabs[:]))
        if syn not in dict1:
            dict1[syn] = extra_bin
        else:
            after_corr, num_corr = sched_fun.correct_until_in_codespace(extra_bin,
                                                                        dict1,
                                                                        n_total,
                                                                        stabs[:])
            log_parity = sched_fun.overlapping_parity(after_corr, tuple(log_bin))
            if log_parity == 1:
                return False, {}
        

    for i in range(flags[0], flags[1]+1):
        hook = sched[i : ]
        hook_bin = sched_fun.convert_to_binary(hook, n_total)
        for err in errors_0 + errors_1 + extra_errors:
            err_bin = sched_fun.convert_to_binary(err, n_total)
            comb_err = sched_fun.multiply_operators(hook_bin, err_bin)
            syn = tuple(sched_fun.error_to_syndrome(comb_err, n_total, stabs[:]))
            if syn not in dict1:
                dict1[syn] = comb_err
            else:
                after_corr, num_corr = sched_fun.correct_until_in_codespace(comb_err,
                                                                            dict1,
                                                                            n_total,
                                                                            stabs[:])
                log_parity = sched_fun.overlapping_parity(after_corr, tuple(log_bin))
                if log_parity == 1:
                    return False, {}
    
    return True, dict1



def basic_dict2(sched1, flags1, sched2, flags2, n_total=17, stabs=d5_stabs[:]):
    '''
    '''

    sched1, sched2 = list(sched1), list(sched2)

    # (no hook)1 (no hook)2
    dict2 = {tuple([0 for i in range(len(stabs))]): tuple([0 for i in range(n_total)])}

    # (no hook)1 (hook)2  and  (hook)1 (no hook)2
    for combo in [[sched1, flags1], [sched2, flags2]]:
        flags = combo[1]
        for i in range(flags[0], flags[1]+1):
            hook = combo[0][i : ]
            hook_bin = sched_fun.convert_to_binary(hook, n_total)
            syn = tuple(sched_fun.error_to_syndrome(hook_bin, n_total, stabs[:]))
            if syn not in dict2:
                dict2[syn] = hook_bin
            else:
                after_corr, num_corr = sched_fun.correct_until_in_codespace(hook_bin,
                                                                            dict2,
                                                                            n_total,
                                                                            stabs[:])
                log_parity = sched_fun.overlapping_parity(after_corr, tuple(log_bin))
                if log_parity == 1:
                    return False, {}
    
    # (hook)1 (hook)2
    for i in range(flags1[0], flags1[1]+1):
        hook1 = sched1[i : ]
        hook1_bin = sched_fun.convert_to_binary(hook1, n_total)
        for j in range(flags2[0], flags2[1]+1):
            hook2 = sched2[j : ]
            hook2_bin = sched_fun.convert_to_binary(hook2, n_total)
            comb_err = sched_fun.multiply_operators(hook1_bin, hook2_bin)
            syn = tuple(sched_fun.error_to_syndrome(comb_err, n_total, stabs[:]))
            if syn not in dict2:
                dict2[syn] = comb_err
            else:
                after_corr, num_corr = sched_fun.correct_until_in_codespace(comb_err,
                                                                            dict2,
                                                                            n_total,
                                                                            stabs[:])
                log_parity = sched_fun.overlapping_parity(after_corr, tuple(log_bin))
                if log_parity == 1:
                    return False, {}

    return True, dict2



def dict2_for_every_sched(good_scheds, flags_good, schedn, flagn, 
                          n_total=17, stabs=d5_stabs[:]):
    '''
    good_scheds is a list of schedules that are already confirmed to be good.
    They are schedules for n stabilizers.
    flags_good is the list of the corresponding flags (the flags for those n
    stabilizers).
    schedn is a possible schedule for the n stabilizer.  
    flagn i the flags for that stabilizer.
    
    Output:  if schedn is good, then:  True
             else:                     False
    '''

    for i in range(len(good_scheds)):
        exists2, dict2 = basic_dict2(good_scheds[i][:], flags_good[i][:],
                                     schedn[:], flagn[:],
                                     n_total, stabs)
        if not exists2:
            return False

    return True



def add_next_sched(list_good_scheds, flags_good, stabn, flagsn,
                   n_total=17, stabs=d5_stabs[:], perms_important=[],
                   extra_errors=[]):
    '''
    Each schedule is a tuple

    list_good_scheds is a list of all the good schedules found so far:
    [[sched1, sched2, ...], [sched1, sched2, ...], ...]
    '''

    new_good_scheds = []
    #for schedn in it.permutations(stabn):
    for perm in perms_important:
        schedn = [stabn[q] for q in perm]
        #schedn = list(schedn)
        
        for good_scheds in list_good_scheds:
            # First compute dict1 for the new schedule
            # Need to add the extra_errors
            # This is inefficient.
            errors_oct = [[good_scheds[0][q] for q in err] for err in extra_errors]
            exists1, dict1 = basic_dict1(schedn[:], flagsn[:], n_total,
                                         stabs, errors_oct)
            if exists1:
                # if dict1 exists, then check that there's a dict2 between the
                # new schedule and every schedule in the list of good schedules
                exists2 = dict2_for_every_sched(good_scheds[:], flags_good[:],
                                                schedn[:], flagsn[:],
                                                n_total, stabs)
    
                if exists2:
                    new_good_scheds += [good_scheds[:] + [schedn]] 

    return new_good_scheds



# First we obtain the good schedules for the octagon
#flags_oct = [2,6]
# When flags_oct = [2,6], the schedules have mirror
# symmetry in the sense that the reversed schedule
# has the same hook errors.
'''
perms_important, perms_reversed = [], []
for perm in it.permutations(range(8)):
    if perm not in perms_reversed:
        perms_important += [perm]
        perms_reversed += [tuple(reversed(perm))]

n_good = 0
sched_dict = {}
for perm in perms_important:
    sched = [d5_stabs[0][i] for i in perm]
    exists, dict1 = basic_dict1(sched, flags_oct)
    if exists:
        sched_dict[n_good] = sched
        n_good += 1

outfile_name = 'schedules_octagon_optimized.json'
outfile = open(outfile_name, 'w')
json.dump(sched_dict, outfile, indent=4, separators=(',', ':'),
          sort_keys=True)
outfile.close()
print 'good schedules octagon =', n_good
'''


# First we load the schedules we had obtained for the octagon
# There are 2880 of them if we choose flags = [2,6].

'''
infile_name = 'schedules_octagon_optimized.json'
infile = open(infile_name, 'r')
good_schedules_oct = json.load(infile).values()
infile.close()
list_good_schedules = []
for sched in good_schedules_oct:
    list_good_schedules += [[tuple(sched)]]

flags_good = [flags_oct[:]]
flags_sq = [1,3]
extra_oct_errors = [[0,1], [6,7]]

perms_important_sq, perms_reversed_sq = [], []
for perm in it.permutations(range(4)):
    if perm not in perms_reversed_sq:
        perms_important_sq += [perm]
        perms_reversed_sq += [tuple(reversed(perm))]

#perms_important_sq = [(0,1,2,3)]
for stabilizer in d5_stabs[1:]:
    list_good_schedules = add_next_sched(list_good_schedules, flags_good[:],
                                         stabilizer, flags_sq[:], 
                                         n_total, d5_stabs[:],
                                         perms_important_sq, extra_oct_errors)
    flags_good += [flags_sq[:]]
    outfile_name = 'other_schedules%i.json' %d5_stabs.index(stabilizer)
    outfile = open(outfile_name, 'w')
    good_schedules_dict = {}
    for i in range(len(list_good_schedules)):
        good_schedules_dict[i] = list_good_schedules[i]
    json.dump(good_schedules_dict, outfile, indent=4, separators=(',', ':'),
              sort_keys=True)
    outfile.close()

    print '%i: %i' %(d5_stabs.index(stabilizer), len(list_good_schedules))
'''

def hook_and_flag(sched_flags, err_locs, flag='f1', n_total=17):
    '''
    - sched_flags is a schedule with a flag.  For example:
    [2,3,'f1',5,6,9,10,'f1',13,14,'m1']
    - err_locs are the indexes of the locations of the errors
    - flag is the flag we are interested in, cause we might
    have more than two for the octagon.

    returns:  trigger (0 or 1), the hook error
    '''

    meas = 'm' + flag[1]
    flag_indexes = [i for i,q in enumerate(sched_flags) if q==flag]
    total_hook_bin = [0 for i in range(n_total)]
    trigger = 0
    for err_loc in err_locs:
        local_hook_flags = sched_flags[err_loc:]
        if local_hook_flags.count(flag)%2==1 or sched_flags[err_loc]==meas:
            trigger += 1
        local_hook = [q for q in local_hook_flags if type(q)==type(0)]
        local_hook_bin = sched_fun.convert_to_binary(local_hook, n_total)
        total_hook_bin = sched_fun.multiply_operators(total_hook_bin, 
                                                      local_hook_bin)

    return trigger%2, total_hook_bin



def all_hooks(sched_flags, flags=['f1'], err_weight=1, n_total=17):
    '''
    for a schedule with flags, it calculates all the possible
    hook errors that are caused by an error event of 
    weight err_weight and whether or not they trigger each flag.
    This is only for a particular schedule of a given stabilizer.

    It returns a dictionary of flag triggering outcomes and hooks.
    '''
    
    dict_hooks = {}
    for prod in it.product([0,1], repeat=len(flags)):
        dict_hooks[prod] = []

    for err_locs in it.combinations(range(len(sched_flags)), err_weight):
        err_locs = list(err_locs)
        triggers, hooks = [], []
        for flag in flags:
            trigger, hook = hook_and_flag(sched_flags[:], err_locs, 
                                          flag, n_total)
            triggers += [trigger]
        # for a given error location, the hook will always be the same;
        # only the triggering pattern will change.
        if hook not in dict_hooks[tuple(triggers)]:
            dict_hooks[tuple(triggers)]+= [hook]

    return dict_hooks



def all_lookups_one_schedule(sched_bare, flags=[[1,3]], n_total=17, stabs=d5_stabs[:]):
    '''
    '''

    # First we add the flags to the schedule
    sched_flags = sched_bare[:]
    for i in range(len(flags)):
        flag_name = 'f' + str(i+1)
        meas_name = 'm' + str(i+1)
        flag_qs = [sched_bare[j] for j in flags[i]]
        for q in flag_qs:
            anc_index = sched_flags.index(q)
            sched_flags.insert(anc_index, flag_name)
        sched_flags += [meas_name]

    # Now we define the dictionary of lookup tables.
    # There's one lookup table for each flag combination
    lookups = {}
    for prod in it.product([0,1], repeat=len(flags)):
        err_weight = sum(prod)
        if err_weight == 0:
            lookups[prod] = dict(dict_noflag)
        elif err_weight == 1:
            lookups[prod] = dict(basic_lookup)
        elif err_weight == 2:
            lookups[prod] = dict(trivial_lookup)

    flag_names = ['f'+str(i+1) for i in range(len(flags))]
    for err_weight in [1,2]:
        dict_hooks = all_hooks(sched_flags, flag_names, err_weight)
        for trig_comb in dict_hooks:
            for hook in dict_hooks[trig_comb]:
                syn = tuple(sched_fun.error_to_syndrome(hook[:], n_total, stabs[:]))
                if syn not in lookups[trig_comb].keys():
                    lookups[trig_comb][syn] = hook
                else:
                    after_corr, num_corr = sched_fun.correct_until_in_codespace(
                                                            hook[:],
                                                            lookups[trig_comb],
                                                            n_total,
                                                            stabs[:])
                    log_parity = sched_fun.overlapping_parity(after_corr, 
                                                              tuple(log_bin))
                    if log_parity == 1:
                        return False, {}
                    
    return True, lookups



#look = all_lookups_one_schedule([2,3,5,6,9,10,13,14], [[1,3], [4,6]])
exists, lookups = all_lookups_one_schedule([0,1,2,3], [[1,3]])
for trig in lookups:
    print trig
    print len(lookups[trig])
for syn in lookups[(1,)]:
    if syn not in basic_lookup:
        print lookups[(1,)][syn]
sys.exit(0)

sched = [0,'f1',1,2,'f1',3,'m1']
di = all_hooks(sched, ['f1'], 2)
for key in di:
    print key
    for ho in di[key]:
        print ho
