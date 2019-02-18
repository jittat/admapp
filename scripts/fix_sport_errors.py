from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
import io
from datetime import datetime

from appl.models import Campus, Faculty, AdmissionProject, Major, ProjectApplication
from regis.models import LogItem

MMAP = {
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    5: 5,
    6: 6,
    7: 7,
    8: -1,
    9: 8,
    10: 9,
    11: 10,
    12: 11,
    13: 12,
    14: 13,
    15: 14,
    16: 15,
    17: 16,
    18: 17,
    19: -1,
    20: 18,
    21: 19,
    22: 20,
    23: 22,
    24: 23,
    25: 24,
    26: 26,
    27: -1,
    28: -1,
    29: 28,
    30: 29,
    31: 30,
    32: 31,
    33: 32,
    34: 33,
    35: 34,
    36: 35,
    37: 36,
    38: 37,
    39: 38,
    40: 39,
    41: 40,
    42: 41,
    43: 42,
    44: 43,
    45: 44,
    46: 45,
    47: 46,
    48: 47,
    49: 48,
    50: 49,
    51: 50,
    52: 52,
    53: 53,
}

def main():
    cutoff = datetime(2019,2,12,11,54)
    
    project = AdmissionProject.objects.get(pk=11)
    applications = ProjectApplication.objects.filter(admission_project=project, is_canceled=False)

    for a in applications:
        applicant = a.applicant
        logs = [l for l in LogItem.objects.filter(applicant_id=applicant.id)
                if l.startswith('Major selection')]

        last_log = logs[0]
        if last_log.created_at < cutoff:
            print(a)

        
        
