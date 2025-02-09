#!/bin/bash
declare -A PRJ

. ./export_env.bash

BASEDIR=$PROJECT_MAJOR_BASEDIR/r2

PRJ=( [11]=kus [12]=seed [13]=diamonds [14]=pirun [16]=provinces [17]=sport [18]=culture [23]=mou [24]=vet [34]=spe [35]=med [50]=inter2 )

for num in "${!PRJ[@]}"; do
    echo $num ${PRJ[$num]}
    python export_majors_from_criteria.py $BASEDIR/$num-${PRJ[$num]}.csv $num
done


