# -*- coding: utf-8 -*-
import os, sys
import io
import csv
from datetime import datetime

from django.db import models

from regis.models import Applicant


class Campus(models.Model):
    title = models.CharField(max_length=100)
    short_title = models.CharField(max_length=50)

    class Meta:
        verbose_name_plural = 'campuses'

    def __str__(self):
        return self.short_title



class Faculty(models.Model):
    title = models.CharField(max_length=100)
    campus = models.ForeignKey('Campus')

    class Meta:
        verbose_name_plural = 'faculties'

    def __str__(self):
        return self.title

    

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

    is_available = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['rank']

        
    def __str__(self):
        if self.subround_number == 0:
            return 'รอบที่ %d' % (self.number,)
        else:
            return 'รอบที่ %d/%d' % (self.number, self.subround_number)

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
                               blank=True)
    
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

    max_num_selections = models.IntegerField(default=1,
                                             verbose_name='จำนวนสาขาที่เลือกได้')

    base_fee = models.IntegerField(default=0,
                                   verbose_name='ค่าสมัคร')
    
    def __str__(self):
        return self.title

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
        if len(project_rounds)==0:
            return None
        else:
            return project_rounds[0]
                    

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
    faculty = models.ForeignKey('Faculty')
    admission_project = models.ForeignKey('AdmissionProject')

    slots = models.IntegerField()
    slots_comments = models.TextField(blank=True)

    detail_items_csv = models.TextField()

    additional_fee_one_time = models.IntegerField(default=0,
                                                  verbose_name='ค่าสมัครเพิ่มเติม (ไม่คิดซ้ำ)')
    additional_fee_per_major = models.IntegerField(default=0,
                                                   verbose_name='ค่าสมัครเพิ่มเติม (คิดซ้ำสาขา)')
    
    class Meta:
        ordering = ['number']
    
    def __str__(self):
        return self.title

    @staticmethod
    def get_by_project_number(project, number):
        majors = Major.objects.filter(admission_project=project,
                                      number=number).all()
        if len(majors)==0:
            return None
        else:
            return majors[0]

        
    def get_detail_items(self):
        csv_io = io.StringIO(self.detail_items_csv)
        reader = csv.reader(csv_io)
        for row in reader:
            return row


class ProjectUploadedDocument(models.Model):
    admission_project = models.ForeignKey(AdmissionProject,
                                          on_delete=models.CASCADE,
                                          blank=True,
                                          null=True)
    rank = models.IntegerField()
    title = models.CharField(max_length=200)
    descriptions = models.TextField()
    specifications = models.CharField(max_length=100)

    allowed_extentions = models.CharField(max_length=50)

    is_required = models.BooleanField(default=True)
    can_have_multiple_files = models.BooleanField(default=False)

    file_prefix = models.CharField(max_length=50,
                                   blank=True)
    size_limit = models.IntegerField(default=2000000)

    class Meta:
        ordering = ['rank']

    def __str__(self):
        return self.title

    @staticmethod
    def get_common_documents():
        return ProjectUploadedDocument.objects.filter(admission_project=None).all()

    def get_uploaded_documents_for_applicant(self, applicant):
        return self.uploaded_document_set.filter(applicant=applicant).all()
    

def applicant_document_path(instance, filename):
    try:
        project_id = instance.admission_project.id
    except:
        project_id = 0
    return ('documents/applicant_{0}/project_{1}/doc_{2}/{3}'
            .format(instance.applicant.id,
                    project_id,
                    instance.project_uploaded_document.id,
                    filename))


class UploadedDocument(models.Model):
    applicant = models.ForeignKey(Applicant,
                                  on_delete=models.CASCADE)
    admission_project = models.ForeignKey(AdmissionProject,
                                          on_delete=models.CASCADE,
                                          blank=True,
                                          null=True)
    project_uploaded_document = models.ForeignKey(ProjectUploadedDocument,
                                                  on_delete=models.CASCADE,
                                                  related_name='uploaded_document_set')
    rank = models.IntegerField()
    original_filename = models.CharField(max_length=200)

    uploaded_file = models.FileField(upload_to=applicant_document_path)
    

    def __str__(self):
        return '%s (%s)' % (self.project_uploaded_document.title,
                            self.applicant)


class Province(models.Model):
    title = models.CharField(max_length=30)

    def __str__(self):
    	return "%s" % (self.name,)


class School(models.Model):
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=20,
                            blank=True)
    province = models.ForeignKey(Province,
                                 on_delete=models.CASCADE)

    def __str__(self):
        return "%s" % (self.name,)


class ProjectApplication(models.Model):
    applicant = models.ForeignKey(Applicant,
                                  on_delete=models.CASCADE,
                                  related_name='project_applications')
    admission_project = models.ForeignKey(AdmissionProject,
                                          on_delete=models.CASCADE)
    admission_round = models.ForeignKey(AdmissionRound)

    is_canceled = models.BooleanField(default=False)
    applied_at = models.DateTimeField()
    cancelled_at = models.DateTimeField(blank=True,
                                        null=True)

    def get_number(self):
        return 1003241 + self.id

    def get_verification_number(self):
        return str(1000000 + (self.id * 952183) % 951361)
    
    def is_active(self):
        return not self.is_canceled

    def admission_fee(self, major_selection=None):
        fee = self.admission_project.base_fee
        if not major_selection:
            try:
                major_selection = self.major_selection
            except:
                major_selection = None

        if major_selection:
            majors = major_selection.get_majors()
            one_time_fee = 0
            acc_fee = 0
            for m in majors:
                if m.additional_fee_one_time > one_time_fee:
                    one_time_fee = m.additional_fee_one_time
                acc_fee += m.additional_fee_per_major

            fee += one_time_fee + acc_fee

        return fee


class PersonalProfile(models.Model):
    applicant = models.ForeignKey(Applicant)
    mobile_phone = models.CharField(max_length=20,
                                    verbose_name='เบอร์โทรศัพท์มือถือ',
                                    blank=True)

    
class MajorSelection(models.Model):
    applicant = models.ForeignKey(Applicant)
    project_application = models.OneToOneField(ProjectApplication,
                                               related_name='major_selection')
    admission_project = models.ForeignKey(AdmissionProject)
    admission_round = models.ForeignKey(AdmissionRound)

    num_selected = models.IntegerField(default=0)
    major_list = models.CharField(max_length=50,
                                  blank=True)


    def __str__(self):
        return self.major_list

    def get_majors(self):
        try:
            return self.majors
        except:
            pass

        self.majors = []
        for num in self.major_list.split(','):
            self.majors.append(Major.get_by_project_number(self.admission_project,
                                                           num))
        return self.majors

    def set_majors(self, majors):
        self.majors = majors
        self.major_list = ','.join([str(m.number) for m in self.majors])
        self.num_selected = len(majors)
                            

class Payment(models.Model):
    applicant = models.ForeignKey(Applicant,
                                  null=True)
    admission_round = models.ForeignKey(AdmissionRound)

    national_id = models.CharField(max_length=20)
    verification_number = models.CharField(max_length=30)

    source_type = models.IntegerField(default=0)

    payment_name = models.CharField(max_length=100,
                                    blank=True)
    
    amount = models.FloatField(default=0)
    paid_at = models.DateTimeField()

    has_payment_error = models.BooleanField(default=False)
    

    def __str__(self):
        return '{0} ({1}/{2})'.format(self.amount, self.id, self.paid_at)


    @staticmethod
    def find_for_applicant_in_round(applicant, admission_round):
        return Payment.objects.filter(applicant=applicant,
                                      admission_round=admission_round).all()

    
