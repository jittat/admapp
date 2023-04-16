#!/bin/bash
declare -A PRJ

BASEDIR=~/Dropbox/adm66/criterias/r2

PRJ=( [11]=kus [12]=seed [13]=diamonds [14]=pirun [15]=thaiinter [16]=provinces [17]=sport [18]=culture [21]=irr [22]=south [23]=mou [24]=vet [26]=sciex [50]=inter2 [51]=spe )

for num in "${!PRJ[@]}"; do
    echo $num ${PRJ[$num]}
    python export_major_criterias_as_json.py $num 2 >  $BASEDIR/$num-${PRJ[$num]}.json
done


