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


def send_payment_email(applicant, amount, paid_at):
    subject = 'แจ้งการได้รับการชำระค่าสมัคร ' + ADMISSION_SHORT_TITLE
    body = """
เรียนผู้สมัคร {full_name}

อีเมลนี้แจ้งว่าโครงการได้รับเงินค่าสมัครจากผู้สมัครแล้ว

จำนวนเงิน: {amount}
ชำระเมื่อ: {paid_at}

ขอขอบคุณที่ให้ความสนใจสมัครเข้าศึกษาต่อในมหาวิทยาลัยเกษตรศาสตร์
-ทีมงานระบบรับสมัคร
""".format(full_name=applicant.get_full_name(),
           amount=amount,
           paid_at=paid_at)


    send_mail_to_applicant(applicant,
                           subject,
                           body)

    
def send_clearing_house_email(applicant, result, clearing_code, username):
    from appl.clearing_utils import read_clearing_code
    subject = 'แจ้งเตือนการยืนยันสิทธิ์เคลียริงเฮาส์ ' + ADMISSION_SHORT_TITLE
    body = """
เรียนผู้สมัคร {full_name}

ผู้สมัครผ่านการคัดเลือกมีสิทธิ์เข้าศึกษาต่อในสาขาวิชา: {major_title} ({major_faculty})
ในปีการศึกษา 2561 ผ่านทางการคัดเลือกในรอบ 1/2

ผู้สมัครจะต้องยืนยันสิทธิ์ผ่านระบบยืนยันสิทธิ์ของทปอ. http://app.cupt.net/tcas/
ระหว่างวันที่ 19 - 22 มี.ค. 2561
โดยใช้เลขประจำตัวประชาชนหรือหมายเลขพาสปอร์ต (กรณีไม่มีเลขประจำตัวประชาชน)
และรหัสผ่านดังนี้

เลขประจำตัวประชาชน {username}
รหัสผ่าน {clearing_code}
(คำอ่านของรหัสผ่าน {clearing_code_read})

ขอขอบคุณที่ให้ความสนใจสมัครเข้าศึกษาต่อในมหาวิทยาลัยเกษตรศาสตร์
และหวังว่าจะได้พบกับผู้สมัครในภาคต้นปีการศึกษา 2561 ต่อไป

ยินดีต้อนรับสู่รั้วนนทรี
-ทีมงานระบบรับสมัคร
""".format(full_name=applicant.get_full_name(),
           major_title=result.major.title,
           major_faculty=result.major.faculty,
           username=username,
           clearing_code=clearing_code,
           clearing_code_read=read_clearing_code(clearing_code))

    send_mail_to_applicant(applicant,
                           subject,
                           body)

    
def send_major_confirmation_email(applicant, application, majors):
    if len(majors)==1:
        major_str = '{major} ({fac})'.format(major=majors[0].title, fac=majors[0].faculty)
    else:
        items = []
        count = 1
        for m in majors:
            items.append('{count}. {major} ({fac})'.format(count=count, major=m.title, fac=m.faculty))
            count += 1
        major_str = "\n".join(items)
    
    subject = 'แจ้งยืนยันสาขาที่สมัคร ' + ADMISSION_SHORT_TITLE
    body = """
เรียนผู้สมัคร {full_name}

ผู้สมัครได้สมัครเข้าศึกษาต่อมหาวิทยาลัยเกษตรศาสตร์ ผ่านทางโครงการ {project}
โดยเลือกสาขาวิชาดังนี้
{major_str}

กรุณาตรวจสอบสาขาที่สมัครดังกล่าว ถ้ามีปัญหากรุณาติดต่อฝ่ายรับเข้าศึกษา สำนักทะเบียนและประมวลผล 
ภายในวันที่ 30 มี.ค. 2561 ทางอีเมล admission@ku.ac.th 
หรือทาง Facebook https://www.facebook.com/kuadmission
หรือทาง โทร. 02 118 0100 ต่อ 8046-8050

-ทีมงานระบบรับสมัคร
""".format(full_name=applicant.get_full_name(),
           project=str(application.admission_project),
           major_str=major_str)

    send_mail_to_applicant(applicant,
                           subject,
                           body)

    
