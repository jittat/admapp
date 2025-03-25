#!/bin/bash

. ./export_env.bash

for p in 1 2 3 4 8 9 32; do python export_project_applicants_tcas.py $p 1 1_2568 > $APP_BASEDIR/r1/applicants-r1-$p.csv; done
for p in 101 103 109 33; do python export_project_applicants_tcas.py $p 5 1_2568 > $APP_BASEDIR/r1/applicants-r1-$p.csv; done

