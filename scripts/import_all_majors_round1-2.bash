#!/bin/bash
declare -A PRJ

. ./export_env.bash

BASEDIR=$PROJECT_MAJOR_BASEDIR/r1-2

PRJ=( [101]=ele12 [103]=inter12 [8]=dpst [109]=posn12-updated [33]=smt )

for num in "${!PRJ[@]}"; do
    echo $num ${PRJ[$num]}
    python import_majors.py $num $BASEDIR/$num-${PRJ[$num]}.csv
done


