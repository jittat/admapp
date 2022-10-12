import csv
import sys


def main():
    app_filename = sys.argv[1]
    code_filename = sys.argv[2]

    codes = {}
    
    with open(code_filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            if len(items) < 5:
                continue

            cupt_full_code = items[6].strip()
            codes[cupt_full_code] = {
                'full_fact_title': items[9].strip(),
                'full_major_title': items[10].strip(),
            }

    with open(app_filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            if len(items) < 5:
                continue
            
            output = items
            c = items[0]
            output[1] = codes[c]['full_fact_title']
            output[2] = codes[c]['full_major_title']

            print(','.join(['"' + x + '"' for x in output]))

if __name__ == "__main__":
    main()
