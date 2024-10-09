#!/bin/bash
declare -A PRJ

. ./export_env.bash

BASEDIR=$PROJECT_MAJOR_BASEDIR/r1

PRJ=( [1]=ele [2]=ap [3]=inter [4]=natsport [8]=dpst [9]=posn [32]=steam )

for num in "${!PRJ[@]}"; do
    echo $num ${PRJ[$num]}
    python export_majors_from_criteria.py $BASEDIR/$num-${PRJ[$num]}.csv $num
done


