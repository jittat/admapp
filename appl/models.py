import io
import csv

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

    class Meta:
        ordering = ['rank']

        
    def __str__(self):
        if self.subround_number == 0:
            return 'รอบที่ %d' % (self.number,)
        else:
            return 'รอบที่ %d/%d' % (self.number, self.subround_number)


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
    slots = models.IntegerField(default=0,
                                verbose_name='จำนวนรับ')

    major_detail_visible = models.BooleanField(default=False,
                                               verbose_name='แสดงรายละเอียดสาขา')
    
    def __str__(self):
        return self.title



class AdmissionProjectRound(models.Model):
    admission_round = models.ForeignKey('AdmissionRound',
                                        on_delete=models.CASCADE)
    admission_project = models.ForeignKey('AdmissionProject',
                                          on_delete=models.CASCADE)
    admission_dates = models.CharField(max_length=100)

    
class Major(models.Model):
    number = models.IntegerField()
    title = models.CharField(max_length=200)
    faculty = models.ForeignKey('Faculty')
    admission_project = models.ForeignKey('AdmissionProject')

    slots = models.IntegerField()
    slots_comments = models.TextField(blank=True)

    detail_items_csv = models.TextField()

    class Meta:
        ordering = ['number']
    
    def __str__(self):
        return self.title

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
                                                  on_delete=models.CASCADE)
    rank = models.IntegerField()
    original_filename = models.CharField(max_length=200)

    uploaded_file = models.FileField(upload_to=applicant_document_path)
    

    def __str__(self):
        return '%s (%s)' % (self.project_upload_document.title,
                            self.applicant)
