import sys
import numpy as np
import json
import itertools as it
import multiprocessing as mp
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
        in_dict, log_par, syn = sched_fun.can_correct(extra_bin[:], dict1, 
                                                      n_total, stabs[:])
        if not in_dict:
            dict1[syn] = extra_bin
        else:
            if log_par == 1:
                return False, {} 

    for i in range(flags[0], flags[1]+1):
        hook = sched[i : ]
        hook_bin = sched_fun.convert_to_binary(hook, n_total)
        for err in errors_0 + errors_1 + extra_errors:
            err_bin = sched_fun.convert_to_binary(err, n_total)
            comb_err = sched_fun.multiply_operators(hook_bin, err_bin)
            in_dict, log_par, syn = sched_fun.can_correct(comb_err[:], dict1,
                                                          n_total, stabs[:])
            if not in_dict:
                dict1[syn] = comb_err
            else:
                if log_par == 1:
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
            in_dict, log_par, syn = sched_fun.can_correct(hook_bin[:], dict2, 
                                                          n_total, stabs[:])
            if not in_dict:
                dict2[syn] = hook_bin
            else:
                if log_par == 1:
                    return False, {} 
    
    # (hook)1 (hook)2
    for i in range(flags1[0], flags1[1]+1):
        hook1 = sched1[i : ]
        hook1_bin = sched_fun.convert_to_binary(hook1, n_total)
        for j in range(flags2[0], flags2[1]+1):
            hook2 = sched2[j : ]
            hook2_bin = sched_fun.convert_to_binary(hook2, n_total)
            comb_err = sched_fun.multiply_operators(hook1_bin, hook2_bin)
            in_dict, log_par, syn = sched_fun.can_correct(comb_err[:], dict2, 
                                                          n_total, stabs[:])
            if not in_dict:
                dict2[syn] = comb_err
            else:
                if log_par == 1:
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
    sched_flags = sched_fun.add_flags_to_sched(sched_bare, flags)

    # Now we define the dictionary of lookup tables.
    # There's one lookup table for each flag combination
    lookups = {}
    for prod in it.product([0,1], repeat=len(flags)):
        err_weight = sum(prod)
        if err_weight == 0:
            lookups[prod] = dict(dict_noflag)
        elif err_weight == 1:
            lookups[prod] = dict(basic_lookup)
        elif err_weight > 1:
            lookups[prod] = dict(trivial_lookup)

    flag_names = ['f'+str(i+1) for i in range(len(flags))]
    
    
    # First we deal with the cases where we only had 1 error
    # on the ancilla
    dict_hooks = all_hooks(sched_flags, flag_names, 1)
    for trig_comb in dict_hooks:
        for hook in dict_hooks[trig_comb]:
            # for each hook we add all the possible w-1
            # errors on the data
            for data_err in errors_0 + errors_1:
                #print data_err
                data_err_bin = sched_fun.convert_to_binary(data_err, n_total)
                comb_err = sched_fun.multiply_operators(hook[:], data_err_bin[:])
                in_dict, log_par, syn = sched_fun.can_correct(comb_err[:],
                                                              lookups[trig_comb],
                                                              n_total,
                                                              stabs[:])
                if not in_dict:
                    lookups[trig_comb][syn] = comb_err[:]
                else:
                    if log_par == 1:
                        return False, {}


    # Secondly we deal with the cases where we had 2 errors
    # on the ancilla
    dict_hooks = all_hooks(sched_flags, flag_names, 2)
    for trig_comb in dict_hooks:
        for hook in dict_hooks[trig_comb]:
            in_dict, log_par, syn = sched_fun.can_correct(hook[:],
                                                          lookups[trig_comb],
                                                          n_total,
                                                          stabs[:])
            if not in_dict:
                lookups[trig_comb][syn] = hook[:]
            else:
                if log_par == 1:
                    return False, {}
               
    return True, lookups



def add_two_lookups(trig_comb1, lookup1, trig_comb2, lookup2,
                    n_total, stabs):
    '''
    '''
    w1 = sched_fun.total_trig_comb_w(trig_comb1)
    w2 = sched_fun.total_trig_comb_w(trig_comb2)
    total_w = w1 + w2
    if total_w > 2:
        raise ValueError('The total weight cannot be larger than 2.')
    elif total_w == 2:
        return True, {}
    elif total_w == 1:
        if w1 == 1:  
            return True, dict(lookup1)
        else:        
            return True, dict(lookup2)
    elif total_w == 0:
        comb_lookup = dict(lookup1)
        for syn in lookup2:
            if syn not in comb_lookup:
                comb_lookup[syn] = lookup2[syn]
            else:
                err1 = comb_lookup[syn]
                err2 = lookup2[syn]
                total_err = sched_fun.multiply_operators(err1, err2)
                total_syn = sched_fun.error_to_syndrome(total_err,
                                                        n_total,
                                                        stabs)
                if total_syn.count(1) == 0:
                    log_parity = sched_fun.overlapping_parity(total_err, 
                                                              tuple(log_bin))
                    if log_parity == 1:  
                        return False, None
                else:
                    raise ValueError('The total correction does not take me to the CS.')

        return True, comb_lookup 

        

def merge_two_lookups_dicts(old_lookups, old_scheds, old_flags, new_lookups, 
                            new_sched, new_flags, n_total=17, stabs=d5_stabs[:]):
    '''
    '''

    #print old_scheds
    #print old_flags
    #print new_sched
    #print new_flags
    #sys.exit(0)


    updated_lookups = {}
    for trig_comb_old in old_lookups:
        trig_comb_old_w = sched_fun.total_trig_comb_w(trig_comb_old)
        if trig_comb_old_w < 2:
            for trig_comb_new in new_lookups:
                #print 'old =', trig_comb_old
                #print 'new =', trig_comb_new
                trig_comb_up = trig_comb_old + trig_comb_new
                #print 'updated =', trig_comb_up
                exist1, comb_lookup = add_two_lookups(trig_comb_old,
                                                      old_lookups[trig_comb_old],
                                                      trig_comb_new,
                                                      new_lookups[trig_comb_new],
                                                      n_total, stabs)
                #print exist1, len(comb_lookup)
                
                if not exist1:  return False, None
                updated_lookups[trig_comb_up] = comb_lookup

        else:
            # if the weight of the triggering combination is already 2,
            # then we just add a 0 and keep the same dictionary.
            trig_comb_up = trig_comb_old + (0,)
            updated_lookups[trig_comb_up] = old_lookups[trig_comb_old]

    
    for old_sched_i in range(len(old_scheds)):
        exist2, updated_lookups = add_dicts2(updated_lookups, 
                                             old_sched_i,
                                             old_scheds[old_sched_i],
                                             old_flags[old_sched_i],
                                             new_sched, 
                                             new_flags,
                                             n_total,
                                             stabs)
        if not exist2:  return False, None

    return True, updated_lookups




def add_dicts2(updated_lookups, old_sched_index, old_sched, old_flags,
               new_sched, new_flags, n_total=17, stabs=d5_stabs[:]):
    '''
    '''
    updated_lookups = dict(updated_lookups)
    total_stabs_so_far = len(updated_lookups.keys()[0])
    total_trig_basic = [0 for i in range(total_stabs_so_far-1)]

    #print updated_lookups.keys()
    #print old_sched_index
    #print old_sched
    #print old_flags
    #print new_sched
    #print new_flags

    # First we create the flagged schedules and the flag names
    old_flag_names = ['f'+str(i+1) for i in range(len(old_flags))]
    new_flag_names = ['f'+str(i+1) for i in range(len(new_flags))]
    old_sched_flags = sched_fun.add_flags_to_sched(old_sched, old_flags)
    new_sched_flags = sched_fun.add_flags_to_sched(new_sched, new_flags)

    #print old_flag_names
    #print new_flag_names
    #print old_sched_flags
    #print new_sched_flags

    # Now we generate every possible w-1 hook error on the old schedule
    # and every possible w-1 hook error on the new schedule.
    dict_hooks_old = all_hooks(old_sched_flags, old_flag_names, 1)
    dict_hooks_new = all_hooks(new_sched_flags, new_flag_names, 1)
    #print dict_hooks_old.keys()
    #print dict_hooks_new.keys()
    for trig_comb_old in dict_hooks_old:
        for trig_comb_new in dict_hooks_new:
            total_trig = total_trig_basic[:]
            #print total_trig
            total_trig[old_sched_index] = trig_comb_old
            #print total_trig
            total_trig += trig_comb_new
            #print total_trig
            total_trig = tuple(total_trig)
            #print total_trig

            for hook_old in dict_hooks_old[trig_comb_old]:
                for hook_new in dict_hooks_new[trig_comb_new]:

                    #print hook_old
                    #print hook_new
                    comb_hook = sched_fun.multiply_operators(hook_old[:], hook_new[:])
                    #print comb_hook

                    in_dict, log_par, syn = sched_fun.can_correct(comb_hook[:],
                                                                  updated_lookups[total_trig],
                                                                  n_total,
                                                                  stabs[:])
                    #print in_dict, log_par, syn
                    if not in_dict:
                        updated_lookups[total_trig][syn] = comb_hook[:]
                    else:
                        if log_par == 1:
                            return False, {}

    return True, updated_lookups

'''
old_lookups = {((0,0),): 'nothing', ((0,1),): 'nothing', ((1,0),): 'nothing', ((1,1),): 'nothing'}
new_lookups = {(0,): 'nothing', (1,): 'nothing'}
up1 = merge_two_lookups_dicts(old_lookups, [], new_lookups, [])
for key in up1:  print key
up2 = merge_two_lookups_dicts(up1, [], new_lookups, [])
for key in up2:  print key
sys.exit(0)
'''


#look = all_lookups_one_schedule([2,3,5,6,9,10,13,14], [[1,3], [4,6]])
#exists, lookups = all_lookups_one_schedule([0,1,2,3], [[1,3]])
#print exists
#if exists:
#    print len(dict_noflag)
#    print len(basic_lookup)
#    for trig in lookups:
#        print trig
#        print len(lookups[trig])
#for syn in lookups[(1,)]:
#    if syn not in basic_lookup:
#        print lookups[(1,)][syn]


def try_all_schedules_octagon(flags): 
    '''
    '''
    
    flags_str = '_'.join(map(str,[q for flag in flags for q in flag]))
    outfile_name = 'schedules_octagon_%s.json' %flags_str

    good_schedules = []
    for perm in it.permutations(range(8)):
        sched = [octagon[i] for i in perm]    
        exists, lookups = all_lookups_one_schedule(sched, flags)
        if exists:
            good_schedules += [sched]

    sched_dict = {}
    for i in range(len(good_schedules)):
        sched_dict[i] = good_schedules[i]
    outfile_name = 'schedules_octagon_%s.json' %flags_str
    outfile = open(outfile_name, 'w')
    json.dump(sched_dict, outfile, indent=4, separators=(',', ':'),
              sort_keys=True)
    outfile.close()
    #print 'good schedules octagon =', len(good_schedules)

    return len(good_schedules)





def try_all_schedules_octagon_several_flags(flags_combos):
    n_good = 0
    for flags in flags_combos:
        n_good += try_all_schedules_octagon(flags)
    
    return n_good


n_flags=0
octagon = d5_stabs[0][:]

'''
flags_combos = []
for comb1 in it.combinations(range(8), 2):
    #print comb1
    if comb1[0] == 0 and comb1[1] < 6:  continue
    for comb2 in it.combinations(range(8), 2):
        #print comb2
        flags = [list(comb1), list(comb2)]
        #print flags
        flags_combos += [flags]
        n_flags+=1
        #print all_lookups_one_schedule(octagon[:], flags)
print n_flags


n_proc = 4
n_per_group = n_flags/4
print n_per_group
flags_combos_div = [flags_combos[i*n_per_group:(i+1)*n_per_group] for i in range(n_proc)]
#flags_combos_div = [flags_combos[i*n_per_group:i*n_per_group+2] for i in range(n_proc)]
#print flags_combos_div[0]

pool = mp.Pool(n_proc)
results = [pool.apply_async(try_all_schedules_octagon_several_flags, (flags_combos_div[i],))
            for i in range(n_proc)]
pool.close()
pool.join()
n_good_results = [r.get() for r in results]
print n_good_results

# Just to make sure that it works if we have 7 flags
# It does work!
#exists, lookups = all_lookups_one_schedule(octagon[:], [[0,1],[1,2],[2,3],[3,4],[4,5],
#                                            [5,6],[6,7]])
#print exists
'''


flags_oct = [[1,6], [2,7]]
flags_str = '_'.join(map(str,[q for flag in flags_oct for q in flag]))
octagon_filename = 'schedules_octagon_%s.json' %flags_str
json_file = open(octagon_filename, 'r')
json_dict = json.load(json_file)
json_file.close()
sched_oct = json_dict['0']
exists_oct, old_lookups_oct = all_lookups_one_schedule(sched_oct, flags_oct)
lookups_oct = {}
for comb_trig in old_lookups_oct:
    lookups_oct[(comb_trig,)] = old_lookups_oct[comb_trig]

flags_sq = [[1,3]]
sched_sq = d5_stabs[1][:]
#exists_sq, lookups_sq = all_lookups_one_schedule(sched_sq, flags_sq)

#exist, lo = merge_two_lookups_dicts(lookups_oct, [sched_oct], [flags_oct], 
#                                    lookups_sq, sched_sq, flags_sq)
#print lo.keys()

def add_extra_sched(old_lookups, old_scheds, old_flags, new_sched, new_flags,
                    n_total=17, stabs=d5_stabs[:]):
    '''
    '''
    
    # First we compute the dict1 for the new schedule
    exist1, new_lookups = all_lookups_one_schedule(new_sched, new_flags,
                                                   n_total, stabs)
    if not exist1:  return False, {}, [] 

    # Then we compute the dict2
    exist2, updated_lookups = merge_two_lookups_dicts(old_lookups, old_scheds,
                                                      old_flags, new_lookups,
                                                      new_sched, new_flags,
                                                      n_total, stabs)
    if not exist2:  return False, {}, []

    updated_scheds = old_scheds + [new_sched]
    return True, updated_lookups, updated_scheds


exist, lo = add_extra_sched(lookups_oct, [sched_oct], [flags_oct],
                            sched_sq, flags_sq)
print exist
print lo.keys()

def next_good_sched(list_good_scheds, flags_good, stabn, flagsn,
                    n_total=17, stabs=d5_stabs[:], perms_important=[],
                    extra_errors=[]):
    '''
    '''

    
