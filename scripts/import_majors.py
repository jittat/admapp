from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
import io

from appl.models import Campus, Faculty, AdmissionProject, Major

def main():
    project_id = sys.argv[1]

    project = AdmissionProject.objects.get(pk=project_id)

    for major in project.major_set.all():
        major.delete()
    
    filename = sys.argv[2]
    counter = 0
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        lines = [l for l in reader]

        project.general_conditions = lines[0][0]
        project.column_descriptions = lines[1][0]
        project.save()
        
        for items in lines[2:]:
            
            if len(items) < 5:
                continue

            number = items[0]
            faculty_title = items[1].strip()

            candidate_titles = [faculty_title,
                                'คณะ' + faculty_title]

            faculty = None
            for t in candidate_titles:
                try:
                    faculty = Faculty.objects.filter(title=t).first()
                    if faculty != None:
                        break
                except:
                    pass

            if faculty == None:
                print('ERROR:',faculty_title,'NOT FOUND!!')
                continue
                
            title = items[2].strip()
            slots = int(items[3])
            slots_comments = items[4]

            details_items = items[5:]

            csv_output = io.StringIO()
            writer = csv.writer(csv_output)
            writer.writerow(details_items)
            
            major = Major(number=number,
                          title=title,
                          faculty=faculty,
                          admission_project=project,
                          slots=slots,
                          slots_comments=slots_comments,
                          detail_items_csv=csv_output.getvalue())

            major.save()

            counter += 1

    print('Imported',counter,'majors')
        

if __name__ == '__main__':
    main()
    
