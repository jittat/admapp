from django_bootstrap import bootstrap
bootstrap()

from appl.models import AdmissionRound

def main():
    rounds = [
        (1,1,1,1,'','การรับด้วย Portfolio (ช่วงที่หนึ่ง)'),
        (2,1,2,2,'','การรับด้วย Portfolio (ช่วงที่สอง)'),
        (3,2,0,3,'','การรับระบบโควตา'),
        (4,3,0,4,'','การรับตรงร่วมกัน'),
        (5,4,0,5,'','การรับระบบกลาง Admissions'),
        (6,5,0,6,'','การรับตรงอิสระ'),
    ]

    for r in AdmissionRound.objects.all():
        r.delete()

    for rraw in rounds:
        r = AdmissionRound(id=rraw[0],
                           number=rraw[1],
                           subround_number=rraw[2],
                           rank=rraw[3],
                           admission_dates=rraw[4],
                           short_descriptions=rraw[5])
        r.save()

if __name__ == '__main__':
    main()
