#!/bin/bash --login

#SBATCH -N 1-1   
#SBATCH --tasks-per-node=8
#SBATCH --cpus-per-task=1
#SBATCH -t 44:00:00

module load /app/modules-new/languages/python/2.7.11

for round_i 1 2 3 4 5 6 7 8
do
    python test_latt_surg_ion.py 1 10 2 0 0 0 0 0 X Z $round_i &
done


wait
