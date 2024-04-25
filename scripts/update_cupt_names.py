import sys
import csv

def main():
    input_filename = sys.argv[1]
    update_filename = sys.argv[2]
    output_filename = sys.argv[3]
    
    lines = []
    with open(input_filename) as f:
        reader = csv.DictReader(f)
        for items in reader:
            lines.append(items)

    updates = {}
    with open(update_filename) as f:
        reader = csv.reader(f)
        for items in reader:
            updates[items[0]] = {
                'data': items[2],
                'new_value': items[3],
                'org_value': items[1],
            }

    for l in lines:
        if l['citizen_id'] in updates:
            u = updates[l['citizen_id']]
            if l[u['data']] == u['org_value']:
                #print(l['citizen_id'], l[u['data']], u)
                l[u['data']] = u['new_value']
            else:
                print('not match', l['citizen_id'], u)


    with open(output_filename,'w') as f:
        writer = csv.DictWriter(f, fieldnames=lines[0].keys())
        writer.writeheader()
        for l in lines:
            writer.writerow(l)

            
if __name__ == '__main__':
    main()
