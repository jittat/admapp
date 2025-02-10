from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
import io

from appl.models import Faculty, AdmissionProject, Major

def validate_titles(lines):
    titles = set()
    for items in lines:
        if len(items) < 4:
            continue

        title = (items[2].strip() + "-" + items[1].strip()).replace(" ","")
        if title in titles:
            print("Dupplicated title:", title)
            return False
        titles.add(title)
    return True

def main():
    project_id = sys.argv[1]

    project = AdmissionProject.objects.get(pk=project_id)

    if project.major_set.count() != 0:
        if (len(sys.argv) != 4) or (sys.argv[3] != '--remove'):
            print("This will remove old majors.  Abort.  To actually ddo so, call with option --remove")
            quit()
            
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
        
        if not validate_titles(lines[2:]):
            print("Error majors with same title")
            quit()

        for items in lines[2:]:
            
            if len(items) < 4:
                continue

            if len(items) == 4:
                items.append('')

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
            if items[3].strip() != '-':
                slots = int(items[3].strip())
            else:
                slots = 0
            
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
    
