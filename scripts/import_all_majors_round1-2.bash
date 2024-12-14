#!/bin/bash
declare -A PRJ

. ./export_env.bash

BASEDIR=$PROJECT_MAJOR_BASEDIR/r1-2

PRJ=( [101]=ele [103]=inter [109]=posn-updated [33]=smt )

for num in "${!PRJ[@]}"; do
    echo $num ${PRJ[$num]}
    python import_majors.py $num $BASEDIR/$num-${PRJ[$num]}.csv
done


