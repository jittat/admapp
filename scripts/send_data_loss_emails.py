from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from admapp.emails import send_mail_to_applicant

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
        print("{},{}".format(a.email, a.first_name + ' ' + a.last_name))
        #send_mail_to_applicant(a, subject, body_template.format(fullname=a.first_name + ' ' + a.last_name))

        
if __name__ == '__main__':
    main()
    
