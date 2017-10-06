from django.core.mail import send_mail
from django.conf import settings

ADMISSION_TITLE = settings.ADMISSION_TITLE
ADMISSION_SHORT_TITLE = settings.ADMISSION_SHORT_TITLE

ADM_EMAIL_FROM = settings.ADM_EMAIL_FROM


def send_mail_to_applicant(applicant, subject, body):
    email = applicant.email
    send_mail(subject,
              body,
              ADM_EMAIL_FROM,
              [ email ])


def send_registration_email(applicant):
    if applicant.national_id[0:3] == '999':
      data_message = "เลขที่หนังสือเดินทาง {passport_number}".format(passport_number=applicant.passport_number)
    else:
      data_message = "รหัสประชาชน {national_id}".format(national_id=applicant.national_id)
    subject = 'แจ้งการลงทะเบียนสมัคร ' + ADMISSION_SHORT_TITLE
    body = """
เรียนผู้สมัคร {full_name}

อีเมลนี้แจ้งการลงทะเบียนเข้าใช้ระบบรับสมัคร {admission_title} ของ {full_name}
ในการลงทะเบียนใช้อีเมล {email}

ผู้สมัครสามารถเข้าใช้ระบบเพื่อสมัครโครงการคัดเลือกนักเรียนเข้าศึกษาต่อโครงการต่าง โดยป้อน
{data_message}
และใช้รหัสเข้าระบบตามที่ได้ลงทะเบียนไว้

ขอขอบคุณที่ให้ความสนใจสมัครเข้าศึกษาต่อในมหาวิทยาลัยเกษตรศาสตร์
-ทีมงานระบบรับสมัคร
""".format(full_name=applicant.get_full_name(),
           admission_title=ADMISSION_TITLE,
           email=applicant.email,
           national_id=applicant.national_id,
           passport_number=applicant.passport_number,
           data_message=data_message)

    send_mail_to_applicant(applicant,
                           subject,
                           body)

    
def send_forget_password_email(applicant, new_password):
    subject = 'แจ้งการขอรหัสผ่านใหม่ {0} ({1})'.format(ADMISSION_SHORT_TITLE,
                                                   applicant.get_full_name())
    body = """
เรียนผู้สมัคร {full_name}

อีเมลนี้แจ้งการขอรหัสผ่านใหม่ {admission_title} ของ {full_name}
ในการลงทะเบียนใช้อีเมล {email}  รหัสผ่านใหม่ในการเข้าใช้งานคือ

{password}

ผู้สมัครสามารถเข้าใช้ระบบเพื่อสมัครโครงการคัดเลือกนักเรียนเข้าศึกษาต่อโครงการต่าง โดยป้อน
รหัสประชาชน {national_id}
และใช้รหัสผ่าน {password}

ขอขอบคุณที่ให้ความสนใจสมัครเข้าศึกษาต่อในมหาวิทยาลัยเกษตรศาสตร์
-ทีมงานระบบรับสมัคร
""".format(full_name=applicant.get_full_name(),
           admission_title=ADMISSION_TITLE,
           email=applicant.email,
           national_id=applicant.national_id,
           password=new_password)

    send_mail_to_applicant(applicant,
                           subject,
                           body)


    
