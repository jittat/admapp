#!/bin/bash

. ./export_env.bash

for p in 11 12 13 14 16 17 18 23 24 34 35 50; do echo $p; python export_project_applicants_tcas.py $p 2 2_2568 > $APP_BASEDIR/r2/applicants-r2-$p.csv; done

