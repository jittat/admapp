from django_bootstrap import bootstrap
bootstrap()

import sys

from appl.models import AdmissionRound, Payment, AdmissionProjectRound, ProjectApplication
from datetime import timedelta, datetime

def main():
    payments = {}
    for p in Payment.objects.all():
        if p.applicant_id == None:
            continue

        app_id = p.applicant_id
        if app_id not in payments:
            payments[app_id] = []
        payments[app_id].append(p)

    all_dellist = []
    for app_id in payments:
        if len(payments[app_id]) == 1:
            continue

        ps = sorted([(p.paid_at, p.id, p) for p in payments[app_id]])
        ps.reverse()
        old = None
        dellist = []
        for d,id,p in ps:
            if old != None:
                #print(app_id, old,p, old.paid_at - p.paid_at)
                if (old.paid_at - p.paid_at < timedelta(0,1)) and (old.amount == p.amount):
                    dellist.append(p)
                else:
                    old = p
            else:
                old = p
        if len(dellist) != 0:
            for p in dellist:
                p.delete()

            all_dellist += [(app_id, dellist[0].applicant, p) for p in dellist]

    if len(all_dellist) != 0:
        print(datetime.now())
        for app_id, applicant, p in all_dellist:
            print(app_id, applicant, p)

                
if __name__ == '__main__':
    main()
