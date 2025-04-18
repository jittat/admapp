# -*- coding: utf-8 -*-
import csv
import io
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from admapp import settings
from regis.models import Applicant

validate_phonenumber = RegexValidator(r'^\+?[0-9#-]+$',
                                      'เบอร์โทรศัพท์สามารถประกอบด้วยตัวเลข 0-9 สามารถใช้เครื่องหมาย - เพื่อแบ่งกลุ่มตัวเลข และอาจเริ่มต้นด้วยเครื่องหมาย +')


class Campus(models.Model):
    title = models.CharField(max_length=100)
    short_title = models.CharField(max_length=50)

    class Meta:
        verbose_name_plural = 'campuses'

    def __str__(self):
        return self.short_title

    def title_trans(self):
        return _(self.title)


class Faculty(models.Model):
    title = models.CharField(max_length=100)
    campus = models.ForeignKey('Campus',
                               on_delete=models.CASCADE)

    ku_code = models.CharField(max_length=10, blank=True)
    cupt_code = models.CharField(max_length=10, blank=True)

    class Meta:
        verbose_name_plural = 'faculties'

    def __str__(self):
        return self.title

    def title_trans(self):
        return _(self.title)


class AdmissionRound(models.Model):
    number = models.IntegerField()
    subround_number = models.IntegerField(default=0)
    rank = models.IntegerField()

    short_descriptions = models.CharField(max_length=400,
                                          blank=True,
                                          verbose_name='รายละเอียดสั้น ๆ (แสดงในหน้าแรก)')
    admission_dates = models.CharField(max_length=200,
                                       blank=True,
                                       verbose_name='กำหนดการ')

    is_available = models.BooleanField(default=False,
                                       verbose_name='แสดงเป็นรอบการรับสมัครต่อผู้สมัคร')
    is_application_available = models.BooleanField(default=False,
                                                   verbose_name='ยังแสดงใบสมัครจากรอบนี้ในรอบสมัครอื่น ๆ')

    clearing_house_description = models.TextField(blank=True,
                                                  verbose_name='ข้อมูลการยืนยันสิทธิ์')
    acceptance_result_date = models.DateField(verbose_name='วันที่ประกาศผลการคัดเลือก (สำหรับแจ้งในข้อความ)')
    clearing_house_dates = models.CharField(max_length=50,
                                            blank=True,
                                            verbose_name='วันที่ยืนยันสิทธิ์ในระบบทปอ. (สำหรับแจ้งในข้อความ)')
    clearing_house_dates_short = models.CharField(max_length=50,
                                                  blank=True,
                                                  verbose_name='วันที่ยืนยันสิทธิ์ในระบบทปอ.แบบสั้น (สำหรับแจ้งในข้อความ)')

    class Meta:
        ordering = ['rank']

    def __str__(self):
        if self.subround_number == 0:
            return 'รอบที่ %d' % (self.number,)
        else:
            return 'รอบที่ %d/%d' % (self.number, self.subround_number)

    def title_trans(self):
        return _(str(self))

    def get_full_number(self):
        if self.subround_number == 0:
            return '%d' % (self.number,)
        else:
            return '%d/%d' % (self.number, self.subround_number)

    @staticmethod
    def get_available():
        rounds = AdmissionRound.objects.filter(is_available=True).all()
        if len(rounds) > 0:
            return rounds[0]
        else:
            return None

    def get_available_projects(self):
        return self.admissionproject_set.filter(is_available=True).all()


class AdmissionProject(models.Model):
    title = models.CharField(max_length=400)
    short_title = models.CharField(max_length=200)
    admission_rounds = models.ManyToManyField('AdmissionRound',
                                              through='AdmissionProjectRound')
    campus = models.ForeignKey('Campus',
                               null=True,
                               blank=True,
                               on_delete=models.SET_NULL)

    general_conditions = models.TextField(blank=True)
    column_descriptions = models.TextField(blank=True)

    descriptions = models.TextField(blank=True,
                                    verbose_name='รายละเอียดโครงการ')
    short_descriptions = models.CharField(max_length=400,
                                          blank=True,
                                          verbose_name='รายละเอียดโครงการ (สั้น) แสดงในหน้าแรก')
    applying_confirmation_warning = models.TextField(blank=True,
                                                     verbose_name='รายละเอียดโครงการ แจ้งยืนยันก่อนสมัคร')

    slots = models.IntegerField(default=0,
                                verbose_name='จำนวนรับ')

    major_detail_visible = models.BooleanField(default=False,
                                               verbose_name='แสดงรายละเอียดสาขา')

    is_available = models.BooleanField(default=False)
    is_visible_in_backoffice = models.BooleanField(default=False)

    is_custom_score_criteria_allowed = models.BooleanField(default=True,
                                                           verbose_name='อนุญาตให้ป้อนเงื่อนไขได้อย่างอิสระ')
    is_custom_curriculum_type_allowed = models.BooleanField(default=False,
                                                            verbose_name='อนุญาตให้แก้ไขประเภทหลักสูตรโรงเรียนได้')
    is_custom_add_limit_criteria = models.BooleanField(default=False,
                                                       verbose_name='ให้ระบุจำนวนรับเพิ่มในกรณีที่ผู้สมัครเกินและมีคะแนนเท่ากัน')
    is_custom_graduate_year_allowed = models.BooleanField(default=False,
                                                          verbose_name='อนุญาตให้เลือกรูปแบบปีที่จบการศึกษาของผู้สมัคร')
    
    is_criteria_edit_allowed = models.BooleanField(default=True,
                                                   verbose_name='อนุญาตให้ผู้ดูแลโครงการแก้ไขเงื่อนไขการรับ')

    is_custom_interview_date_allowed = models.BooleanField(default=False,
                                                           verbose_name='อนุญาติให้เลือกวันสัมภาษณ์ได้')
    custom_interview_start_date = models.DateField(verbose_name='วันสัมภาษณ์วันแรก',
                                                   blank=True,
                                                   null=True)
    custom_interview_end_date = models.DateField(verbose_name='วันสัมภาษณ์วันสุดท้าย',
                                                 blank=True,
                                                 null=True)
    
    max_num_selections = models.IntegerField(default=1,
                                             verbose_name='จำนวนสาขาที่เลือกได้')

    has_selections_with_no_ranks = models.BooleanField(default=False)
    cross_majors_acceptance_visible = models.BooleanField(default=False)
    applicant_details_hidden = models.BooleanField(default=False)

    base_fee = models.IntegerField(default=0,
                                   verbose_name='ค่าสมัคร')

    cupt_code = models.CharField(max_length=10, blank=True)

    is_cupt_export_only_major_list = models.BooleanField(default=True,
                                                         verbose_name='ส่งข้อมูลทปอ.เป็นรายการสาขาเท่านั้น')

    is_auto_select_single_major = models.BooleanField(default=False,
                                                      verbose_name='มีสาขาเดียวและเลือกสาขานั้นโดยอัตโนมัติ')
    
    display_rank = models.IntegerField(default=0,
                                       verbose_name='สำหรับใช้เรียงรายการ')

    # basic admission criteria (student types / school types)

    SCHOOL_TYPE_CHOICES = [
        (1, 'ไม่ระบุเงื่อนไข (รับทุกรูปแบบ)'),
        (2, 'รับเฉพาะ รร.หลักสูตรแกนกลาง'),
        (3, 'รับเฉพาะ รร.หลักสูตรนานาชาติ'),
        (4, 'รับเฉพาะ รร.หลักสูตรอาชีวะ'),
        (5, 'รับเฉพาะ รร.หลักสูตรตามอัธยาศัย (กศน.)'),
        (6, 'รับเฉพาะ รร.หลักสูตร GED'),
    ]

    STUDENT_TYPE_CHOICES = [
        (1, 'รับเฉพาะนักเรียนม. 6 ในปีนี้'),
        (2, 'รับม. 6 และผู้จบการศึกษา'),
    ]

    admission_student_type = models.IntegerField(default=1,
                                                 choices=STUDENT_TYPE_CHOICES)
    admission_school_type = models.IntegerField(default=1,
                                                choices=SCHOOL_TYPE_CHOICES)

    def __str__(self):
        return self.title

    def title_trans(self):
        return _(self.title)

    def get_admission_rounds_display(self):
        return ','.join([str(r) for r in self.admission_rounds.all()])

    def is_deadline_passed(self):
        started = False
        for around in self.admissionprojectround_set.all():
            if around.is_started:
                started = True
                if around.is_open():
                    return False
        if started:
            return True
        else:
            return False

    def is_open(self):
        for around in self.admissionprojectround_set.all():
            if around.is_open():
                return True
        return False

    def get_project_round_for(self, admission_round):
        project_rounds = self.admissionprojectround_set.filter(admission_round=admission_round).all()
        if len(project_rounds) == 0:
            return None
        else:
            return project_rounds[0]

    def get_major_description_list_template(self):
        from .header_utils import table_header_as_list_template

        return table_header_as_list_template(self.column_descriptions)

    def get_major_description_table_header(self):
        from .header_utils import table_header

        return table_header(self.column_descriptions, tr_class="table-active")

    def get_majors_as_dict(self, with_faculty=False):
        if not with_faculty:
            return dict([(m.number, m) for m in self.major_set.all()])
        else:
            return dict([(m.number, m) for m in self.major_set.select_related('faculty').all()])


class AdmissionProjectRound(models.Model):
    admission_round = models.ForeignKey('AdmissionRound',
                                        on_delete=models.CASCADE)
    admission_project = models.ForeignKey('AdmissionProject',
                                          on_delete=models.CASCADE)
    admission_dates = models.CharField(max_length=100)

    is_auto_start = models.BooleanField(default=False)

    is_started = models.BooleanField(default=False,
                                     verbose_name='เปิดรับสมัครแล้ว')
    applying_start_time = models.DateTimeField(blank=True,
                                               null=True,
                                               verbose_name='เวลาเริ่มเปิดรับสมัคร')
    applying_deadline = models.DateTimeField(blank=True,
                                             null=True,
                                             verbose_name='เวลาปิดรับสมัคร')
    payment_deadline = models.DateField(blank=True,
                                        null=True,
                                        verbose_name='วันชำระค่าสมัครวันสุดท้าย')

    applicant_info_viewable = models.BooleanField(default=False,
                                                  verbose_name='สามารถดูรายละเอียดผู้สมัครได้')
    criteria_check_required = models.BooleanField(default=False,
                                                  verbose_name='มีการตรวจเกณฑ์พื้นฐานก่อน')
    multimajor_criteria_check_required = models.BooleanField(default=False,
                                                             verbose_name='มีการตรวจเกณฑ์พื้นฐานสำหรับการสมัครหลายสาขา')
    criteria_check_frozen = models.BooleanField(default=False,
                                                verbose_name='ปิดการแก้ไขผลการตรวจเกณฑ์พื้นฐาน')
    criteria_edit_only_staff_allowed = models.BooleanField(default=False,
                                                          verbose_name='อนุญาตให้เจ้าหน้าที่แก้ไขผลการตรวจเกณฑ์พื้นฐานเท่านั้น')

    applicant_score_viewable = models.BooleanField(default=False,
                                                   verbose_name='แสดงคะแนนสำหรับการคัดเลือก')

    only_bulk_interview_acceptance = models.BooleanField(default=False,
                                                         verbose_name='เรียกสัมภาษณ์ตามคะแนนเท่านั้น')

    accepted_for_interview_result_frozen = models.BooleanField(default=False,
                                                               verbose_name='ปิดการแก้ไขผลการเรียกสัมภาษณ์')
    accepted_for_interview_result_shown = models.BooleanField(default=False,
                                                              verbose_name='แสดงผลการเรียกสัมภาษณ์กับผู้สมัคร')

    accepted_for_interview_instructions = models.TextField(blank=True,
                                                           verbose_name='รายละเอียดแสดงกับผู้สมัครที่ผ่านการคัดเลือก')

    accepted_result_frozen = models.BooleanField(default=False,
                                                 verbose_name='ปิดการแก้ไขผลการรับเข้าศึกษากับผู้สมัคร')
    accepted_result_shown = models.BooleanField(default=False,
                                                verbose_name='แสดงผลการรับเข้าศึกษากับผู้สมัคร')

    accepted_instructions = models.TextField(blank=True,
                                             verbose_name='รายละเอียดแสดงกับผู้สมัครที่ได้รับการคัดเลือกเข้าศึกษา')

    class Meta:
        ordering = ['admission_round', 'admission_project']

    def __str__(self):
        return "{0} ({1})".format(self.admission_project.title, str(self.admission_round))

    def is_deadline_passed(self):
        if self.applying_deadline:
            return datetime.now() > self.applying_deadline
        else:
            return True

    def is_open(self):
        return self.is_started and (not self.is_deadline_passed())


class Major(models.Model):
    number = models.IntegerField()
    title = models.CharField(max_length=200)
    faculty = models.ForeignKey('Faculty',
                                on_delete=models.CASCADE)
    admission_project = models.ForeignKey('AdmissionProject',
                                          on_delete=models.CASCADE)

    slots = models.IntegerField()
    slots_comments = models.TextField(blank=True)

    detail_items_csv = models.TextField()

    additional_fee_one_time = models.IntegerField(default=0,
                                                  verbose_name='ค่าสมัครเพิ่มเติม (ไม่คิดซ้ำ)')
    additional_fee_per_major = models.IntegerField(default=0,
                                                   verbose_name='ค่าสมัครเพิ่มเติม (คิดซ้ำสาขา)')

    ku_code = models.CharField(max_length=10, blank=True)
    study_type = models.CharField(max_length=20, blank=True)
    cupt_code = models.CharField(max_length=10, blank=True)
    cupt_study_type_code = models.CharField(max_length=10, blank=True)
    cupt_full_code = models.CharField(max_length=20, blank=True)

    is_forced_individual_interview_call = models.BooleanField(default=False,
                                                              verbose_name='ให้เรียกสัมภาษณ์ไม่ตามคะแนน')

    class Meta:
        ordering = ['number']

    def __str__(self):
        return self.title

    def title_trans(self):
        return _(self.title)

    def title_with_faculty(self):
        return '{} ({})'.format(self.title, self.faculty.title)

    @staticmethod
    def get_by_project_number(project, number):
        majors = Major.objects.filter(admission_project=project,
                                      number=number).all()
        if len(majors) == 0:
            return None
        else:
            return majors[0]

    def get_detail_items(self):
        csv_io = io.StringIO(self.detail_items_csv)
        reader = csv.reader(csv_io)
        for row in reader:
            return row

    def get_detail_items_as_list_display(self):
        items = [item.replace("\n", "<br />") for item in self.get_detail_items()]
        return self.admission_project.get_major_description_list_template().format(*items)

    def get_full_major_cupt_code(self,
                                 admission_project=None,
                                 faculty=None):
        if self.cupt_full_code:
            return self.cupt_full_code

        if not admission_project:
            admission_project = self.admission_project
        if not faculty:
            faculty = self.faculty

        major_cupt_code = '{0:0>3}'.format(self.cupt_code)
        study_type_code = self.cupt_study_type_code

        full_major_code = ('002' +
                           admission_project.cupt_code +
                           faculty.cupt_code +
                           major_cupt_code +
                           study_type_code)
        return full_major_code


class ProjectUploadedDocument(models.Model):
    admission_projects = models.ManyToManyField(AdmissionProject,
                                                blank=True)
    rank = models.IntegerField()
    title = models.CharField(max_length=200)
    descriptions = models.TextField()
    specifications = models.CharField(max_length=100)

    notes = models.CharField(max_length=100,
                             blank=True)

    allowed_extentions = models.CharField(max_length=50)
    file_prefix = models.CharField(max_length=50,
                                   blank=True)
    size_limit = models.IntegerField(default=2000000)

    is_url_document = models.BooleanField(default=False)

    is_required = models.BooleanField(default=True)
    is_detail_required = models.BooleanField(default=False)
    can_have_multiple_files = models.BooleanField(default=False)

    is_common_document = models.BooleanField(default=False,
                                             verbose_name='ใช้ทุกโครงการ')
    is_interview_document = models.BooleanField(default=False,
                                                verbose_name='ใช้สำหรับสัมภาษณ์')

    document_key = models.CharField(max_length=30,
                                    blank=True)

    requirement_key = models.CharField(max_length=10,
                                       blank=True,
                                       default='')

    class Meta:
        ordering = ['rank']

    def __str__(self):
        if self.notes == '':
            return self.title
        else:
            return '{0} ({1})'.format(self.title, self.notes)

    @staticmethod
    def get_common_documents():
        return ProjectUploadedDocument.objects.filter(is_common_document=True).all()

    def get_uploaded_documents_for_applicant(self, applicant):
        return self.uploaded_document_set.filter(applicant=applicant).all()


def applicant_document_path(instance, filename):
    return ('documents/applicant_{0}/doc_{1}/{2}'
            .format(instance.applicant.id,
                    instance.project_uploaded_document.id,
                    filename))


class UploadedDocument(models.Model):
    applicant = models.ForeignKey(Applicant,
                                  on_delete=models.CASCADE)
    project_uploaded_document = models.ForeignKey(ProjectUploadedDocument,
                                                  on_delete=models.CASCADE,
                                                  related_name='uploaded_document_set')
    rank = models.IntegerField()
    detail = models.CharField(default='', blank=True, max_length=200)

    uploaded_file = models.FileField(upload_to=applicant_document_path,
                                     blank=True)
    original_filename = models.CharField(max_length=200,
                                         blank=True)

    document_url = models.URLField(blank=True)

    def __str__(self):
        return '%s (%s)' % (self.project_uploaded_document.title,
                            self.applicant)

    def is_pdf(self):
        if self.uploaded_file:
            return self.uploaded_file.name.lower().endswith('pdf')
        else:
            return False


class OldUploadedDocument(models.Model):
    applicant = models.ForeignKey(Applicant,
                                  on_delete=models.CASCADE)
    project_uploaded_document = models.ForeignKey(ProjectUploadedDocument,
                                                  on_delete=models.CASCADE,
                                                  related_name='old_uploaded_document_set')
    rank = models.IntegerField()
    detail = models.CharField(default='', blank=True, max_length=200)

    uploaded_file = models.FileField(upload_to=applicant_document_path,
                                     blank=True)
    original_filename = models.CharField(max_length=200,
                                         blank=True)

    document_url = models.URLField(blank=True)


class Province(models.Model):
    title = models.CharField(max_length=30)

    def __str__(self):
        return "%s" % (self.title)


class School(models.Model):
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=20,
                            blank=True)
    province = models.ForeignKey(Province,
                                 on_delete=models.CASCADE)

    def __str__(self):
        return "%s" % (self.title,)


class EducationalProfile(models.Model):
    EDUCATION_LEVEL_CHOICES = [
        (1, _('กำลังศึกษาชั้นมัธยมศึกษาปีที่ 6 หรือเทียบเท่า')),
        (2, _('จบการศึกษาชั้นมัธยมศึกษาปีที่ 6 หรือเทียบเท่า')),
    ]
    EDUCATION_PLAN_CHOICES = [
        (1, _('วิทย์-คณิต')),
        (2, _('ศิลป์-คำนวณ')),
        (3, _('ศิลป์-ภาษา')),
        (6, _('ศิลป์-สังคม')),
        (4, _('อาชีวศึกษา')),
        (5, _('ไม่ระบุ')),
    ]

    applicant = models.OneToOneField(Applicant,
                                     on_delete=models.CASCADE)
    education_level = models.IntegerField(choices=EDUCATION_LEVEL_CHOICES,
                                          verbose_name=_('ระดับการศึกษา'))
    education_plan = models.IntegerField(choices=EDUCATION_PLAN_CHOICES,
                                         verbose_name=_('แผนการศึกษา'))
    sci_credit = models.FloatField(default=0,
                                   verbose_name=_('หน่วยกิตกลุ่มสาระวิทยาศาสตร์และเทคโนโลยี'))
    math_credit = models.FloatField(default=0,
                                    verbose_name=_('หน่วยกิตกลุ่มสาระคณิตศาสตร์'))
    lang_credit = models.FloatField(default=0,
                                    verbose_name=_('หน่วยกิตกลุ่มสาระภาษาต่างประเทศ'))

    gpa = models.FloatField(default=0,
                            verbose_name='GPAX',
                            validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
                            help_text=_(
                                'ในกรณีที่กำลังศึกษาชั้นม.6 ให้กรอกเกรดเฉลี่ย 5 ภาคการศึกษา แต่ถ้าคะแนนภาคต้นยังไม่เรียบร้อย สามารถกรอกแค่ 4 ภาคการศึกษาได้ ถ้าจบการศึกษาแล้วให้กรอกเกรดเฉลี่ย 6 ภาคการศึกษา'))
    # help_text='สำหรับการคัดเลือก TCAS รอบ 5 <b>ให้กรอกเกรดเฉลี่ย 6 ภาคการศึกษา</b>')
    province = models.ForeignKey(Province,
                                 verbose_name=_('จังหวัด'),
                                 on_delete=models.CASCADE)
    school_title = models.CharField(max_length=80,
                                    verbose_name=_('โรงเรียน'))
    school_code = models.CharField(max_length=20,
                                   blank=True,
                                   default='')

    def get_education_level_display(self):
        try:
            return dict(self.EDUCATION_LEVEL_CHOICES)[self.education_level]
        except:
            return ''

    def get_education_plan_display(self):
        try:
            return dict(self.EDUCATION_PLAN_CHOICES)[self.education_plan]
        except:
            return ''


class PersonalProfile(models.Model):
    TITLE_CHOICES = (
        ('Mr.', 'Mr.'),
        ('Mrs.', 'Mrs.'),
        ('Miss', 'Miss'),
    )
    applicant = models.OneToOneField(Applicant,
                                     on_delete=models.CASCADE)
    prefix_english = models.CharField(max_length=4,
                                      choices=TITLE_CHOICES,
                                      verbose_name=_('คำนำหน้า (อังกฤษ)'),
                                      default='Mr.')
    first_name_english = models.CharField(max_length=100,
                                          verbose_name=_('ชื่อ (อังกฤษ)'))
    middle_name_english = models.CharField(max_length=100,
                                           verbose_name=_('ชื่อกลาง (อังกฤษ, ถ้ามี)'),
                                           blank=True)
    last_name_english = models.CharField(max_length=200,
                                         verbose_name=_('นามสกุล (อังกฤษ)'))
    passport_number = models.CharField(max_length=20,
                                       verbose_name=_('หมายเลข Passport (ถ้ามี)'),
                                       blank=True)
    birthday = models.DateField(verbose_name=_('วันเดือนปีเกิด'))
    father_prefix = models.CharField(max_length=10,
                                     verbose_name=_('คำนำหน้าชื่อบิดา'))
    father_first_name = models.CharField(max_length=100,
                                         verbose_name=_('ชื่อบิดา'))
    father_last_name = models.CharField(max_length=200,
                                        verbose_name=_('นามสกุลบิดา'))
    mother_prefix = models.CharField(max_length=10,
                                     verbose_name=_('คำนำหน้าชื่อมารดา'))
    mother_first_name = models.CharField(max_length=100,
                                         verbose_name=_('ชื่อมารดา'))
    mother_last_name = models.CharField(max_length=200,
                                        verbose_name=_('นามสกุลมารดา'))
    house_number = models.CharField(max_length=10,
                                    verbose_name=_('บ้านเลขที่'))
    village_number = models.CharField(max_length=10,
                                      verbose_name=_('หมู่'),
                                      blank=True)
    avenue = models.CharField(max_length=100,
                              verbose_name=_('ซอย'),
                              blank=True)
    road = models.CharField(max_length=100,
                            verbose_name=_('ถนน'),
                            blank=True)
    sub_district = models.CharField(max_length=100,
                                    verbose_name=_('ตำบล/แขวง'))
    district = models.CharField(max_length=100,
                                verbose_name=_('อำเภอ/เขต'))
    province = models.CharField(max_length=100,
                                verbose_name=_('จังหวัด'))
    postal_code = models.CharField(max_length=10,
                                   verbose_name=_('รหัสไปรษณีย์'))

    contact_phone = models.CharField(max_length=20,
                                     verbose_name=_('เบอร์โทรศัพท์ที่ติดต่อได้'),
                                     help_text='หากเป็นเบอร์ติดต่อภายใน ให้ใช้ # คั่น เช่น 034-567-890#111',
                                     validators=[validate_phonenumber])
    mobile_phone = models.CharField(max_length=20,
                                    verbose_name=_('เบอร์โทรศัพท์มือถือ'),
                                    blank=True,
                                    validators=[validate_phonenumber])

    def get_full_address(self):
        if 'กรุงเทพ' in self.province:
            sub_district_prefix = 'แขวง'
            district_prefix = 'เขต'
        else:
            sub_district_prefix = 'ตำบล'
            district_prefix = 'อำเภอ'

        addr_items = []
        addr_fields = ['house_number',
                       'village_number',
                       'avenue',
                       'road',
                       'sub_district',
                       'district',
                       'province']
        prefixes = ['บ้านเลขที่',
                    'หมู่',
                    'ซอย',
                    'ถนน',
                    sub_district_prefix,
                    district_prefix,
                    'จังหวัด']
        for f, pre in zip(addr_fields, prefixes):
            v = getattr(self, f).strip()
            if v == '' or v == '-':
                continue
            if v.startswith(pre):
                addr_items.append(v)
            else:
                if v[0].isdigit():
                    addr_items.append(pre + ' ' + v)
                else:
                    if pre != 'หมู่':
                        addr_items.append(pre + v)
                    else:
                        addr_items.append('หมู่บ้าน' + v)

        return ' '.join(addr_items)


class ProjectApplication(models.Model):
    applicant = models.ForeignKey(Applicant,
                                  on_delete=models.CASCADE,
                                  related_name='project_applications')
    admission_project = models.ForeignKey(AdmissionProject,
                                          on_delete=models.CASCADE)
    admission_round = models.ForeignKey(AdmissionRound,
                                        on_delete=models.CASCADE)

    is_canceled = models.BooleanField(default=False)
    applied_at = models.DateTimeField()
    cancelled_at = models.DateTimeField(blank=True,
                                        null=True)

    verification_number = models.CharField(max_length=20,
                                           blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['verification_number']),
        ]

    ID_OFFSET_MAGIC = 104341

    def get_number(self):
        return self.ID_OFFSET_MAGIC + self.id

    @staticmethod
    def find_by_number(number):
        try:
            id = int(number) - ProjectApplication.ID_OFFSET_MAGIC
            app = ProjectApplication.objects.get(pk=id)
            return app
        except:
            return None

    def get_verification_number(self, deadline_str=None):
        project_round = self.admission_project.get_project_round_for(self.admission_round)
        if not deadline_str:
            deadline = project_round.payment_deadline
            deadline_str = "%d%02d%02d" % (deadline.year % 10,
                                           deadline.month,
                                           deadline.day)

        from lib.lincodes import gen_verification

        try:
            return gen_verification(self.applicant.national_id,
                                    str(self.get_number()),
                                    deadline_str)
        except:
            return ''

    def is_active(self):
        return not self.is_canceled

    def admission_fee(self,
                      major_selection=None,
                      project_base_fee=None,
                      majors=None):
        if project_base_fee != None:
            fee = project_base_fee
        else:
            fee = self.admission_project.base_fee

        if not majors:
            if not major_selection:
                try:
                    major_selection = self.major_selection
                except:
                    major_selection = None

        if majors or major_selection:
            if not majors:
                majors = major_selection.get_majors()
            one_time_fee = 0
            acc_fee = 0
            for m in majors:
                if m.additional_fee_one_time > one_time_fee:
                    one_time_fee = m.additional_fee_one_time
                acc_fee += m.additional_fee_per_major

            fee += one_time_fee + acc_fee

        if majors:
            applicant = self.applicant
            applicant_additional_data = applicant.get_additional_data()
            if applicant_additional_data:
                if 'p' in applicant_additional_data:
                    if ((self.admission_project_id == applicant_additional_data['p']) and
                            (majors[0].number in applicant_additional_data['m'])):
                        return 0
        return fee

    def get_major_selection(self):
        try:
            ms = self.major_selection
            return ms
        except:
            return None

    def has_paid(self):
        paid_amount = sum([p.amount for p in Payment.find_for_applicant_in_round(self.applicant, self.admission_round)])
        return paid_amount >= self.admission_fee()

    def has_paid_min(self, amount):
        paid_amount = sum([p.amount for p in Payment.find_for_applicant_in_round(self.applicant, self.admission_round)])
        return paid_amount >= amount

    def has_applied_to_faculty(self, faculty):
        if hasattr(self, 'major_selection'):
            major_selection = self.major_selection
            return major_selection.has_applied_to_faculty(faculty)
        else:
            return False

    def has_applied_to_major(self, major):
        if hasattr(self, 'major_selection'):
            major_selection = self.major_selection
            return major_selection.has_applied_to_major(major)
        else:
            return False

    @staticmethod
    def find_for_project_and_round(admission_project,
                                   admission_round,
                                   with_selection=False):
        results = (ProjectApplication.objects
                   .select_related('applicant')
                   .filter(admission_project=admission_project,
                           admission_round=admission_round,
                           is_canceled=False))
        if with_selection:
            results = results.select_related('major_selection')

        return results.all()


class MajorSelection(models.Model):
    applicant = models.ForeignKey(Applicant,
                                  on_delete=models.CASCADE)
    project_application = models.OneToOneField(ProjectApplication,
                                               related_name='major_selection',
                                               on_delete=models.CASCADE)
    admission_project = models.ForeignKey(AdmissionProject,
                                          on_delete=models.CASCADE)
    admission_round = models.ForeignKey(AdmissionRound,
                                        on_delete=models.CASCADE)

    num_selected = models.IntegerField(default=0)
    major_list = models.CharField(max_length=50,
                                  blank=True)

    def __str__(self):
        return self.major_list

    def get_majors(self, major_dict=None):
        try:
            return self.majors
        except:
            pass

        self.majors = []

        if self.admission_project_id != None:
            for num in self.major_list.split(','):
                if major_dict:
                    self.majors.append(major_dict[int(num)])
                else:
                    self.majors.append(Major.get_by_project_number(self.admission_project,
                                                                   num))
        return self.majors

    def set_majors(self, majors):
        self.majors = majors
        self.major_list = ','.join([str(m.number) for m in self.majors])
        self.num_selected = len(majors)

    def get_major_numbers(self):
        if self.major_list:
            return [int(num) for num in self.major_list.split(',')]
        else:
            return []

    def has_applied_to_faculty(self, faculty):
        for m in self.get_majors():
            if m.faculty.id == faculty.id:
                return True
        return False

    def has_applied_to_major(self, major):
        return major.number in self.get_major_numbers()

    def contains_major_number(self, number):
        if (not self.major_list) or (self.major_list == ''):
            return False
        number = str(number)
        return number in self.major_list.split(",")

    
class Payment(models.Model):
    applicant = models.ForeignKey(Applicant,
                                  null=True,
                                  on_delete=models.SET_NULL)
    admission_round = models.ForeignKey(AdmissionRound,
                                        on_delete=models.CASCADE)

    national_id = models.CharField(max_length=20)
    verification_number = models.CharField(max_length=30)

    source_type = models.IntegerField(default=0)

    payment_name = models.CharField(max_length=100,
                                    blank=True)

    amount = models.FloatField(default=0)
    paid_at = models.DateTimeField()

    has_payment_error = models.BooleanField(default=False)
    updated_at = models.DateTimeField(null=True)

    def __str__(self):
        return '{0} ({1}/{2})'.format(self.amount, self.id, self.paid_at)

    @staticmethod
    def find_for_applicant_in_round(applicant, admission_round):
        return Payment.objects.filter(applicant=applicant,
                                      admission_round=admission_round).all()


class AdmissionResult(models.Model):
    applicant = models.ForeignKey(Applicant,
                                  on_delete=models.CASCADE)
    application = models.ForeignKey(ProjectApplication,
                                    on_delete=models.CASCADE)
    admission_project = models.ForeignKey(AdmissionProject,
                                          on_delete=models.CASCADE)
    admission_round = models.ForeignKey(AdmissionRound,
                                        on_delete=models.CASCADE)

    major = models.ForeignKey(Major,
                              on_delete=models.CASCADE)
    major_rank = models.IntegerField(default=1)

    is_criteria_passed = models.BooleanField(default=None,
                                             null=True)
    updated_criteria_passed_at = models.DateTimeField(null=True)

    is_accepted_for_interview = models.BooleanField(default=None,
                                                    null=True)
    updated_accepted_for_interview_at = models.DateTimeField(null=True)
    interview_rank = models.IntegerField(default=0)

    is_tcas_result = models.BooleanField(default=False)
    tcas_acceptance_round_number = models.IntegerField(blank=True,
                                                       null=True)
    is_tcas_confirmed = models.BooleanField(default=None,
                                            null=True)
    is_tcas_canceled = models.BooleanField(default=None,
                                           null=True)

    is_interview_absent = models.BooleanField(default=None,
                                              null=True)
    is_accepted = models.BooleanField(default=None,
                                      null=True)
    updated_accepted_at = models.DateTimeField(null=True)

    clearing_house_code = models.CharField(max_length=10,
                                           blank=True)
    clearing_house_code_number = models.IntegerField(default=0)

    calculated_score = models.FloatField(default=0)

    has_confirmed = models.BooleanField(default=None,
                                        null=True)

    class Meta:
        indexes = [
            models.Index(fields=['application', 'major']),
            models.Index(fields=['admission_round', 'major']),
            models.Index(fields=['major']),
            models.Index(fields=['admission_project']),
            models.Index(fields=['applicant']),
        ]
        unique_together = (('applicant', 'admission_project', 'major'),)

    def has_interview_rank(self):
        return self.interview_rank != 0

    def read_clearing_house_code(self):
        if self.clearing_house_code:
            from appl.clearing_utils import read_clearing_code
            return read_clearing_code(self.clearing_house_code)
        else:
            return ''

    def scoring_criteria_passed(self):
        if self.is_criteria_passed != False:
            return self.calculated_score >= 0

    def is_interview_callable(self):
        return self.scoring_criteria_passed()

    def criteria_failed_display(self):
        error_map = {
            -10000: 'gpa',
            -20000: 'แผนการเรียน',
            -31000: 'onet',
            -32000: 'gatpat/udat',
            -40000: 'ไม่ใช่ม.6',
        }
        if int(self.calculated_score) in error_map:
            return error_map[int(self.calculated_score)]
        else:
            return 'ไม่ผ่านเกณฑ์'

    def calculated_score_display(self):
        if self.calculated_score < 0:
            return 'ไม่ผ่านเกณฑ์'
        else:
            return '%.3f' % (self.calculated_score,)

    @staticmethod
    def find_by_admission_round_and_major(admission_round, major):
        return AdmissionResult.objects.filter(admission_round=admission_round,
                                              major=major)

    @staticmethod
    def accepted_for_interview_count(admission_round, major):
        return len([result for result
                    in AdmissionResult.find_by_admission_round_and_major(admission_round,
                                                                         major)
                    if result.is_accepted_for_interview])

    @staticmethod
    def accepted_count(admission_round, major):
        return len([result for result
                    in AdmissionResult.find_by_admission_round_and_major(admission_round,
                                                                         major)
                    if result.is_accepted])

    @staticmethod
    def get_for_application_and_major(application, major):
        results = AdmissionResult.objects.filter(application=application,
                                                 major=major).all()
        if len(results) > 0:
            return results[0]
        else:
            return None

    @staticmethod
    def find_by_application(application):
        return AdmissionResult.objects.filter(application=application).all()


class MajorInterviewDescription(models.Model):
    major = models.ForeignKey(Major,
                              on_delete=models.CASCADE)
    admission_round = models.ForeignKey(AdmissionRound,
                                        on_delete=models.CASCADE)
    descriptions = models.TextField()

    has_free_acceptance = models.BooleanField(default=False,
                                              verbose_name='รับโดยไม่ต้องมีกระบวนการอื่น')

    has_onsite_interview = models.BooleanField(default=False,
                                               verbose_name='มีสอบสัมภาษณ์ที่สถานที่')
    has_online_interview = models.BooleanField(default=True,
                                               verbose_name='มีสอบสัมภาษณ์ออนไลน์')

    has_document_requirements = models.BooleanField(default=False,
                                                    verbose_name='มีเอกสารต้องส่งหรืออัพโหลด')
    has_upload_requirements = models.BooleanField(default=False,
                                                  verbose_name='มีเอกสารให้อัพโหลดในระบบ')

    class Meta:
        indexes = [
            models.Index(fields=['admission_round', 'major']),
            models.Index(fields=['major']),
        ]

    @staticmethod
    def find_by_major_and_admission_round(major, admission_round):
        descs = MajorInterviewDescription.objects.filter(major=major,
                                                         admission_round=admission_round).all()
        if len(descs) > 0:
            return descs[0]
        else:
            return None


class Eligibility(object):
    def __init__(self, project=None, applicant=None):
        self.is_eligible = True
        self.is_hidden = False
        self.notice_text = ''
        self._project = project
        self._applicant = applicant
        self._setting = getattr(settings, 'ELIGIBILITY_CHECK', {})

    @classmethod
    def check(cls, project, applicant):
        self = cls(project, applicant)
        if self._project.title in self._setting:
            getattr(self, self._setting[self._project.title])()
        return self

    def white_elephant(self):
        from supplements.models import TopSchool
        self.is_eligible = False
        self.is_hidden = False
        self.notice_text = 'โครงการนี้ผู้สมัครต้องอยู่ในโรงเรียนที่เข้าข่าย กรุณากรอกข้อมูลการศึกษาก่อน'

        if not hasattr(self._applicant, 'educationalprofile'):
            return

        school_code = self._applicant.educationalprofile.school_code
        try:
            school = School.objects.get(code=school_code)
        except ObjectDoesNotExist:
            return
        try:
            topschool = TopSchool.objects.get(school=school)
        except ObjectDoesNotExist:
            return

        self.is_eligible = True
        self.is_hidden = False

    def advanced_placement(self):
        from supplements.models import AdvancedPlacementApplicant
        self.is_eligible = False
        self.is_hidden = False
        self.notice_text = 'โครงการนี้ผู้สมัครต้องผ่านการเข้าร่วมโครงการเรียนล่วงหน้าของม.เกษตรศาสตร์ รุ่นที่ 15-19 ปีการศึกษา 2563-2567'

        try:
            app = AdvancedPlacementApplicant.objects.get(national_id=self._applicant.national_id)
        except ObjectDoesNotExist:
            return

        self.is_eligible = True
        self.is_hidden = False


class ExamScore(models.Model):
    applicant = models.ForeignKey(Applicant,
                                  on_delete=models.CASCADE)
    exam_type = models.CharField(max_length=20)
    exam_round = models.CharField(max_length=20)

    exam_list = models.TextField(blank=True)
    score_list = models.TextField(blank=True)

    NO_SCORE = -1

    class Meta:
        indexes = [
            models.Index(fields=['applicant', 'exam_type']),
        ]
        unique_together = (('applicant', 'exam_type', 'exam_round'),)
        ordering = ['exam_round']

    def extract_scores(self):
        self._exams = []
        self._scores = []
        self._exam_scores = {}

        if self.exam_list:
            eitems = self.exam_list.split(',')
        else:
            eitems = []

        if self.score_list:
            sitems = self.score_list.split(',')
        else:
            sitems = []

        for i in range(len(eitems)):
            self._exams.append(eitems[i])
            if sitems[i] == '-':
                sc = ExamScore.NO_SCORE
            elif sitems[i] == '':
                sc = ExamScore.NO_SCORE
            else:
                try:
                    sc = float(sitems[i])
                except:
                    sc = sitems[i]
            self._scores.append(sc)
            self._exam_scores[eitems[i]] = sc

    def get_exams(self):
        if not hasattr(self, '_exams'):
            self.extract_scores()

        return self._exams

    def get_scores(self):
        if not hasattr(self, '_scores'):
            self.extract_scores()

        return self._scores

    def get_exam_score(self, exam):
        if not hasattr(self, '_exam_scores'):
            self.extract_scores()

        return self._exam_scores.get(exam, ExamScore.NO_SCORE)


class ExamScoreProvider(object):
    def __init__(self, applicant, scores=None):
        self.applicant = applicant
        self.load_scores(scores)

    def process_pat7(self, arr):
        scores = []
        for i in range(self.get_gatpat_round_count()):
            items = []
            for j in range(1, 8):
                key = 'pat7_' + str(j)
                if key in arr:
                    if arr[key][i] != -1:
                        items.append('7.' + str(j) + '=' + ('%.2f' % arr[key][i]))
            if len(items) > 0:
                scores.append(','.join(items))
            else:
                scores.append('-')
        return scores

    def process_alevel8x(self, arr):
        scores = []
        items = []
        for j in range(3, 10):
            key = 'a_lv_8' + str(j)
            if key in arr:
                if arr[key][0] != -1:
                    items.append('8' + str(j) + '=' + ('%.2f' % arr[key][0]))
        if len(items) > 0:
            scores.append(', '.join(items))
        else:
            scores.append('-')
        return scores

    def load_scores(self, scores=None):
        if scores == None:
            self.scores = self.applicant.examscore_set.all()
        else:
            self.scores = scores
        for s in self.scores:
            if not hasattr(self, s.exam_type):
                setattr(self, s.exam_type, {})
                setattr(self, s.exam_type + '_array', {})

            for ex in s.get_exams():
                if '.' in ex:
                    ex = ex.replace('.', '_')
                d = getattr(self, s.exam_type)
                d[ex] = s.get_exam_score(ex)
                darr = getattr(self, s.exam_type + '_array')
                if ex not in darr:
                    darr[ex] = []
                darr[ex].append(s.get_exam_score(ex))

        # self.gatpat_rounds = [s.exam_round
        #                       for s in self.scores
        #                       if s.exam_type == 'gatpat']

        if hasattr(self, 'alevel'):
            ar = getattr(self, 'alevel_array')
            ar['a_lv_8x'] = self.process_alevel8x(ar)

    def get_gatpat_round_count(self):
        return len(self.gatpat_rounds)


class MajorInterviewDescriptionCache(models.Model):
    major = models.ForeignKey('Major',on_delete=models.CASCADE)
    interview_description = models.ForeignKey('backoffice.InterviewDescription', on_delete=models.CASCADE)

    @staticmethod
    def get_interview_description_by_major(major):
        caches = MajorInterviewDescriptionCache.objects.filter(major=major)
        if len(caches) > 0:
            return caches[0].interview_description
        else:
            return None

            
