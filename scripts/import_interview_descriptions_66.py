from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
import os
import shutil

from appl.models import AdmissionRound, Major, MajorInterviewDescription

DESCIPTION_FIELDS = [
    'has_free_acceptance',
    'has_onsite_interview',
    'has_online_interview',
    'has_document_requirements',
    'has_upload_requirements',
]

DESCRIPTION_CHOICES = {
    1: ( True, False, False, False, False),
    2: (False, False,  True, False, False),
    3: (False, False,  True,  True,  True),
    4: (False, False, False,  True,  True),
    5: (False, False, False,  True, False),
    6: (False, False,  True,  True, False),
}

def random_str():
    from random import choice
    alpha = 'abcdefghijklmnopqrstuvwxyz'
    return ''.join([choice(alpha) for i in range(10)])

def main():
    filename = sys.argv[1]
    admission_round_id = sys.argv[2]
    src_base_dir = sys.argv[3].strip().rstrip("/")
    media_base_dir = sys.argv[4].strip().rstrip("/")
    base_url = sys.argv[5].strip().rstrip("/")


    
    counter = 0
    admission_round = AdmissionRound.objects.get(pk=admission_round_id)
    
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)
        for items in reader:
            if len(items) < 4:
                continue

            project_id = int(items[0])
            major_number = int(items[2])
            majors = Major.objects.filter(admission_project_id=project_id,
                                          number=major_number)

            if len(majors) == 0:
                print('MAJOR NOT FOUND', major_number)
                continue
            
            major = majors[0]

            old_descs = MajorInterviewDescription.objects.filter(major=major).all()
            if len(old_descs) > 0:
                desc = old_descs[0]
            else:
                desc = MajorInterviewDescription(major=major,
                                                 admission_round=admission_round)

            desc.admission_round=admission_round
            choice = int(2)

            for f,v in zip(DESCIPTION_FIELDS, DESCRIPTION_CHOICES[choice]):
                setattr(desc, f, v)

            interview_src_filename = items[5].strip()
            if not interview_src_filename:
                continue

            random_folder = random_str()

            os.mkdir(f'{media_base_dir}/{random_folder}')
            shutil.copyfile(f'{src_base_dir}/{interview_src_filename}', f'{media_base_dir}/{random_folder}/{interview_src_filename}')
            file_url = f'{base_url}/{random_folder}/{interview_src_filename}'
            desc.descriptions = f'อ่านรายละเอียดได้ทีนี่ <a target="_blank" class="btn btn-sm btn-outline-secondary" href="{file_url}">ดาวน์โหลด</a>'
            desc.save()
            print(f'{major.admission_project} - {major}')
            print(desc.descriptions)

            counter += 1

    print('Imported',counter,'majors')
        

if __name__ == '__main__':
    main()
    
