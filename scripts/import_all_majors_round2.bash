#!/bin/bash
declare -A PRJ

BASEDIR=~/Dropbox/adm65/project-majors

PRJ=( [11]=kus [12]=seed [13]=diamonds [14]=pirun [15]=thaiinter [16]=provinces [17]=sport [18]=culture [21]=irr [22]=south [23]=mou [24]=vet [26]=sciex [50]=inter2 )

for num in "${!PRJ[@]}"; do
    echo $num ${PRJ[$num]}
    python import_majors.py $num $BASEDIR/$num-${PRJ[$num]}.csv
done

python round2_update_additional_fees.py

