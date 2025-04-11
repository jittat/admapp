#!/bin/bash

. ./export_env.bash

BASEDIR=$ADMAPP_DATA_BASEDIR/r2/applicants

declare -A PRJ

PRJ=( [11]=kus [12]=seed [13]=diamonds [14]=pirun [16]=provinces [17]=sport [18]=culture [23]=mou [24]=vet [34]=spe [35]=med [50]=inter2)

for num in "${!PRJ[@]}"; do
    echo $num ${PRJ[$num]}
    python export_paid_applicants_w_info.py $num 2 >  $BASEDIR/r2-$num-${PRJ[$num]}-applicants.csv
done
