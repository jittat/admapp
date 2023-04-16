import sys
import csv

EXAM_FIELDS = {
    'tgattpat':[
        "tgat",
        "tgat1",
        "tgat2",
        "tgat3",
        "tpat1",
        "tpat11",
        "tpat12",
        "tpat13",
        "tpat2",
        "tpat21",
        "tpat22",
        "tpat23",
        "tpat3",
        "tpat4",
        "tpat5",
    ],
    'alevel':[
        "a_lv_61",
        "a_lv_62",
        "a_lv_63",
        "a_lv_64",
        "a_lv_65",
        "a_lv_66",
        "a_lv_70",
        "a_lv_81",
        "a_lv_82",
        "a_lv_83",
        "a_lv_84",
        "a_lv_85",
        "a_lv_86",
        "a_lv_87",
        "a_lv_88",
        "a_lv_89",
    ],
    'extra':[
        "vnet_51",
        "vnet_511",
        "vnet_512",
        "vnet_513",
        "vnet_514",
        "toefl_ibt",
        "toefl_pbt",
        "toefl_cbt",
        "toefl_ipt",
        "ielts",
        "toeic",
        "cutep",
        "tuget",
        "kept",
        "psutep",
        "kuept",
        "cmuetegs",
        "swu_set",
        "det",
        "mu_elt",
        "sat",
        "cefr",
    ]
}

BASE_FIELDS = [
    'citizen_id',
    'prefix',
    'first_name',
    'last_name',
]

BASE_FIELD_MAP = {
    'prefix': 'title',
    'first_name': 'first_name_th',
    'last_name': 'last_name_th',
}

ADDITIONAL_FIELDS = [
    'year'
]

def main():
    score_filename = sys.argv[1]
    base_filename = sys.argv[2]
    year = int(sys.argv[3])

    results = {}
    for extype in EXAM_FIELDS:
        results[extype] = []
    
    with open(score_filename) as f:
        reader = csv.DictReader(f)

        for row in reader:
            for extype in EXAM_FIELDS:
                result_row = {}
                for f in BASE_FIELDS:
                    if f in BASE_FIELD_MAP:
                        result_row[f] = row[BASE_FIELD_MAP[f]]
                    else:
                        result_row[f] = row[f]
                
                result_row['year'] = year

                for f in EXAM_FIELDS[extype]:
                    result_row[f] = row[f]

                results[extype].append(result_row)

    for extype in EXAM_FIELDS:
        result_filename = f'{base_filename}-{extype}.csv'
        fieldnames = BASE_FIELDS + ADDITIONAL_FIELDS + EXAM_FIELDS[extype]

        with open(result_filename, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for r in results[extype]:
                writer.writerow(r)

    print('Extracted', len(results[list(EXAM_FIELDS.keys())[0]]), 'rows')


if __name__ == '__main__':
    main()

        
    
