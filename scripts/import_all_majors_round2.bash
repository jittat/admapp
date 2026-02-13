#!/bin/bash
declare -A PRJ

. ./export_env.bash

BASEDIR=$PROJECT_MAJOR_BASEDIR/r2

PRJ=( [11]=kus [12]=seed [13]=diamonds-updated [14]=pirun-updated [16]=provinces [17]=sport [23]=mou-updated [24]=vet [34]=spe [35]=med [36]=andaman [50]=inter2 )

for num in "${!PRJ[@]}"; do
    echo $num ${PRJ[$num]}
    python import_majors.py $num $BASEDIR/$num-${PRJ[$num]}.csv
done

python round2_update_additional_fees.py

