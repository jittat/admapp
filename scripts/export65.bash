#!/bin/bash

python export_cupt_cur_props.py r1.csv --empty --combine --r12 1 2 3 4 8 9 10
python export_cupt_cur_props.py r1-src-normal.csv --empty --combine --r12 --exclude เพศชาย 5 6 7
python export_cupt_cur_props.py r1-src-male.csv --empty --combine --r12 --include เพศชาย --postprocessing male 5 6 7

python export_cupt_cur_props.py r2.csv --empty --combine --r12 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26
python export_cupt_cur_props.py r2-src-normal.csv --empty --combine --r12 --exclude เพศชาย 27
python export_cupt_cur_props.py r2-src-male.csv --empty --combine --r12 --include เพศชาย --postprocessing male 27

