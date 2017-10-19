#!/bin/bash

OLDIFS=$IFS
IFS=','

#for subset in 0,2 3,0 2,1 1,2 0,3 4,0 3,1 2,2 1,3 0,4
#for subset in 1,0 0,1 2,0 1,1 0,2 3,0 2,1 1,2 0,3 4,0 3,1 2,2 1,3 0,4 5,0 4,1 3,2 2,3 1,4 0,5

# weight 1 and 2
for subset in 0,0,0,0,1 0,0,0,1,0 0,0,1,0,0 0,1,0,0,0 0,0,0,0,2 0,0,0,2,0 0,0,2,0,0 0,2,0,0,0 0,1,1,0,0 0,1,0,1,0 0,1,0,0,1 0,0,1,1,0 0,0,1,0,1 0,0,0,1,1 
do
    set -- $subset
    time python test_transversal_CNOT.py 10000 8 $subset X Z
done

# weight 3
for subset in 0,0,0,0,3 0,0,0,3,0 0,0,3,0,0 0,3,0,0,0 0,2,1,0,0 0,2,0,1,0 0,2,0,0,1 0,1,2,0,0 0,0,2,1,0 0,0,2,0,1 0,1,0,2,0 0,0,1,2,0 0,0,0,2,1 0,1,0,0,2 0,0,1,0,2 0,0,0,1,2 0,0,1,1,1 0,1,0,1,1 0,1,1,0,1 0,1,1,1,0 
do
    set -- $subset
    time python test_transversal_CNOT.py 10000 8 $subset X Z
done

# weight 4 (first part)
for subset in 0,0,0,0,4 0,0,0,4,0 0,0,4,0,0 0,4,0,0,0 0,3,1,0,0 0,3,0,1,0 0,3,0,0,1 0,1,3,0,0 0,0,3,1,0 0,0,3,0,1 0,1,0,3,0 0,0,1,3,0 0,0,0,3,1 0,1,0,0,3 0,0,1,0,3 0,0,0,1,3
do
    set -- $subset
    time python test_transversal_CNOT.py 10000 8 $subset X Z
done

# weight 4 (second part)
for subset in 0,2,0,1,1 0,2,1,0,1 0,2,1,1,0 0,0,2,1,1 0,1,2,0,1 0,1,2,1,0 0,0,1,2,1 0,1,0,2,1 0,1,1,2,0 0,0,1,1,2 0,1,0,1,2 0,1,1,0,2 0,1,1,1,1
do
    set -- $subset
    time python test_transversal_CNOT.py 10000 8 $subset X Z
done
