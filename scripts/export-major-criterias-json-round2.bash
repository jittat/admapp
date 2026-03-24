#!/bin/bash
declare -A PRJ

. ./export_env.bash

BASEDIR=$ADMAPP_DATA_BASEDIR/criterias/r2

PRJ=( [11]=kus [12]=seed [13]=diamonds [14]=pirun [16]=provinces [17]=sport [23]=mou [24]=vet [34]=spe [35]=med [36]=andaman [50]=inter2 )

for num in "${!PRJ[@]}"; do
    echo $num ${PRJ[$num]}
    python export_major_criterias_as_json.py $num 2 >  $BASEDIR/$num-${PRJ[$num]}.json
done


