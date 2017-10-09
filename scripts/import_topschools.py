from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from django.core.exceptions import ObjectDoesNotExist

from appl.models import School
from supplements.models import TopSchool


def read_fix():
    fix = {}
    try:
        filename = sys.argv[2]
        with open(filename) as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for items in reader:
                old = items[0].strip()
                new = items[1].strip()
                fix[old] = new
    except:
        pass
    return fix


def main():
    fix = read_fix()
    filename = sys.argv[1]
    counter = 0
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            title = items[4].strip()
            if title in fix:
                title = fix[title]
            try:
                school = School.objects.get(title=title)
            except ObjectDoesNotExist:
                try:
                    school = School.objects.get(code=title)
                except ObjectDoesNotExist:
                    print('fail to import:', items)
                    continue
            try:
                old_topschool = TopSchool.objects.get(school=school)
                old_topschool.delete()
            except ObjectDoesNotExist:
                pass
            topschool = TopSchool(school=school)
            topschool.save()
            counter += 1
    print('Imported',counter,'top schools')


if __name__ == '__main__':
    main()
