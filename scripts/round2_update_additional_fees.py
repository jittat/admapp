from django_bootstrap import bootstrap
bootstrap()

from appl.models import AdmissionProject, Major

def main():
    project_majors = {
        13: [
            (65,'ศศ.บ. สาขาวิชาดนตรีไทย',300),
            (66,'ศศ.บ. สาขาวิชาดนตรีตะวันตก',300),
        ],
        16: [
            (46,'ศษ.บ. สาขาวิชาพลศึกษา',100),
        ],
    }

    for pid in project_majors:
        project = AdmissionProject.objects.get(pk=pid)
        for m, title, fee in project_majors[pid]:
            majors = Major.objects.filter(admission_project=project,
                                          number=m)
            if len(majors) != 1:
                print('ERROR', m, title, majors)
                continue

            major = majors[0]

            if major.title != title:
                print('ERROR wrong title', m, title, major.title)
                continue
            
            major.additional_fee_per_major = fee
            major.save()

            print('DONE',project, major, fee)

if __name__ == '__main__':
    main()

