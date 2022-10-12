from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from criteria.models import MajorCuptCode

def main():
    filename = sys.argv[1]
    counter = 0
    
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)
        
        for items in reader:
            print(items[0],items[1])

            mcodes = MajorCuptCode.objects.filter(program_code=items[0], major_code=items[1]).all()
            if len(mcodes)!=1:
                print('ERROR')
                continue

            mcode = mcodes[0]
            mcode.component_weight_type = items[2].strip()
            mcode.save()
            
            counter += 1
        
    print('Imported',counter)
        

if __name__ == '__main__':
    main()
    
