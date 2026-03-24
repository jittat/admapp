#!/bin/bash
declare -A PRJ

. ./export_env.bash

BASEDIR=$PROJECT_MAJOR_BASEDIR/r1-2

PRJ=( [101]=ele12 [103]=inter12 [8]=dpst [109]=posn12 [33]=smt )

for num in "${!PRJ[@]}"; do
    echo $num ${PRJ[$num]}
    python export_majors_from_criteria.py $BASEDIR/$num-${PRJ[$num]}.csv $num
done


