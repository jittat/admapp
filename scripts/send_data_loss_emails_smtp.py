from django_bootstrap import bootstrap
bootstrap()

import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header

#from admapp.emails import send_mail_to_applicant

from regis.models import Applicant
from appl.models import OldUploadedDocument, UploadedDocument

def main():
    app_ids = set()
    for d in OldUploadedDocument.objects.all():
        if d.applicant_id not in app_ids:
            app_ids.add(d.applicant_id)

    subject = 'กรุณาตรวจสอบข้อมูลและนำเข้าเอกสารอัพโหลดในการสมัคร KU Admission'
    body_template = '''เรียนคุณ{fullname} ผู้สมัคร KU Admission ปีการศึกษา 2565

ในช่วงเช้าวันที่ 20 ธันวาคม 2564 ระบบบันทึกข้อมูลของระบบรับสมัครมีปัญหา ทำให้มีข้อมูลเสียหาย

- ทั้งนี้นักเรียนที่ได้สมัครหรือทำการแก้ไขข้อมูลหลังเวลา 02:00 เมื่อระบบเปิดกลับมาให้บริการใหม่กรุณาตรวจสอบความถูกต้องของข้อมูล
- เนื่องจากข้อมูลเอกสารที่ผู้สมัครได้อัพโหลดเข้าไปในระบบได้เสียหายอย่างมาก ทางทีมงานระบบรับสมัครต้องขอรบกวนให้ผู้สมัครอัพโหลดข้อมูลอีกครั้ง

ทีมงานต้องขออภัยหาท่านได้เข้าไปและอัพโหลดข้อมูลใหม่เรียบร้อยแล้ว

ทีมงานระบบรับสมัครต้องขออภัยในความไม่สะดวกนี้อย่างสูง และจะดำเนินการปรับปรุงระบบสำรองข้อมูลให้สมบูรณ์ขึ้นเพื่อไม่ให้เกิดปัญหาเช่นนี้อีก

ด้วยความเคารพ
-ทีมงานระบบรับสมัคร KU Admission
'''

    for id in app_ids:
        a = Applicant.objects.get(pk=id)

        if UploadedDocument.objects.filter(applicant=a).count() != 0:
            continue

        print(a.email)
        continue
    
        body =  body_template.format(fullname=a.first_name + ' ' + a.last_name)

        msg = MIMEMultipart('alternative')
        msg['Subject'] = "%s" % Header(subject, 'utf-8')
        msg['From'] = "KU Admission <admission@ku.ac.th>"
        msg['To'] = a.email

        htmlpart = MIMEText(body, 'html', 'UTF-8')
        textpart = MIMEText(body, 'plain', 'UTF-8')
        msg.attach(htmlpart)
        msg.attach(textpart)

        context = ssl.create_default_context()
        with smtplib.SMTP('nontri.ku.ac.th', 587) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login('admission@ku.ac.th','PASSWORD')
            server.sendmail('admission@ku.ac.th','jittat@gmail.com',msg.as_string())
        
if __name__ == '__main__':
    main()
    
