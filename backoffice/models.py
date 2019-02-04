# -*- coding: utf-8 -*-
import os, sys
from django.db import models

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from regis.models import Applicant
from appl.models import Campus, Faculty
from appl.models import AdmissionProject, AdmissionRound, ProjectApplication 
from appl.models import Major, AdmissionResult, ExamScore

class Profile(models.Model):
    ANY_MAJOR = 0

    user = models.OneToOneField(User,
                                on_delete=models.CASCADE)

    faculty = models.ForeignKey(Faculty,
                                verbose_name='คณะที่สังกัด',
                                default=None,
                                null=True,
                                blank=True,
                                on_delete=models.SET_NULL)
    is_admission_admin = models.BooleanField(verbose_name='ดูแลข้อมูลทุกคณะ',
                                             default=False)

    admission_projects = models.ManyToManyField(AdmissionProject,
                                                blank=True)

    is_number_adjustment_admin = models.BooleanField(verbose_name='สำหรับปรับจำนวน',
                                                     default=False)
    major_number = models.IntegerField(default=ANY_MAJOR,
                                       verbose_name='หมายเลขสาขา (กรณีที่ดูแลโครงการเดียว)')

    def __str__(self):
        if self.faculty:
            return self.user.get_full_name() + ' (' + str(self.faculty) + ')'
        elif self.is_admission_admin:
            return self.user.get_full_name() + ' (ADMADMIN)'
        else:
            return self.user.get_full_name()

    @staticmethod
    def get_profile_for(user):
        try:
            return user.profile
        except:
            return None

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)


class CheckMarkGroup(models.Model):
    NUM_CHECK_MARKS = 6

    COLORS = ['text-primary',
              'text-success',
              'text-warning',
              'text-danger',
              'text-secondary',
              'text-dark']

    applicant = models.ForeignKey(Applicant,
                                  on_delete=models.CASCADE)
    project_application = models.OneToOneField(ProjectApplication,
                                               related_name='check_mark_group',
                                               on_delete=models.CASCADE)
    check_marks = models.CharField(default='',
                                   max_length=20)


    def is_checked(self, num):
        if len(self.check_marks) >= num:
            return self.check_marks[num-1] == '1'

    def init_marks(self):
        self.check_marks = ''.join(['0' for i in range(self.NUM_CHECK_MARKS)])

    def set_check(self, num):
        self.check_marks = self.check_marks[:(num-1)] + '1' + self.check_marks[num:]

    def set_uncheck(self, num):
        self.check_marks = self.check_marks[:(num-1)] + '0' + self.check_marks[num:]

    def get_check_mark_list(self):
        marks = []
        for i in range(self.NUM_CHECK_MARKS):
            marks.append({ 'number': i+1,
                           'is_checked': self.is_checked(i+1),
                           'text_color': self.COLORS[i], })
        return marks

    def __str__(self):
        return '{0} - {1}'.format(self.applicant.national_id, self.check_marks)


class JudgeComment(models.Model):
    applicant = models.ForeignKey(Applicant,
                                  on_delete=models.CASCADE)
    project_application = models.ForeignKey(ProjectApplication,
                                            related_name='judge_comment_set',
                                            on_delete=models.CASCADE)

    author_username = models.CharField(max_length=30,
                                       blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    body = models.TextField()

    is_deleted = models.BooleanField(default=False)
    is_shared_in_major = models.BooleanField(default=False)
    
    admission_project = models.ForeignKey(AdmissionProject,
                                          blank=True,
                                          null=True,
                                          default=None,
                                          on_delete=models.SET_NULL)
    admission_round = models.ForeignKey(AdmissionRound,
                                        blank=True,
                                        null=True,
                                        default=None,
                                        on_delete=models.SET_NULL)
    major = models.ForeignKey(Major,
                              blank=True,
                              null=True,
                              default=None,
                              on_delete=models.SET_NULL)
    
    class Meta:
        ordering = ['-created_at']

    def report_display(self):
        if self.author_username:
            return self.body + ' - ' + self.author_username
        else:
            return self.body


class MajorInterviewCallDecision(models.Model):
    FLOAT_DELTA = 0.000001
    
    admission_project = models.ForeignKey(AdmissionProject,
                                          on_delete=models.CASCADE)
    admission_round = models.ForeignKey(AdmissionRound,
                                        on_delete=models.CASCADE)
    major = models.ForeignKey(Major,
                              on_delete=models.CASCADE)

    interview_call_count = models.IntegerField(default=0)
    interview_call_min_score = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=['major','admission_round']),
            models.Index(fields=['admission_round','admission_project']),
        ]
        unique_together = (('major','admission_round'),)
    
    @staticmethod
    def get_for(major, admission_round):
        decisions = MajorInterviewCallDecision.objects.filter(major=major,
                                                              admission_round=admission_round).all()
        if len(decisions) > 0:
            return decisions[0]
        else:
            return None


class ApplicantMajorResult(models.Model):
    admission_project = models.ForeignKey(AdmissionProject,
                                          on_delete=models.CASCADE)
    major = models.ForeignKey(Major,
                              on_delete=models.CASCADE)
    applicant = models.ForeignKey(Applicant,
                                  on_delete=models.CASCADE)
    project_application = models.ForeignKey(ProjectApplication,
                                            null=True,
                                            on_delete=models.SET_NULL)
    admission_result = models.ForeignKey(AdmissionResult,
                                         null=True,
                                         on_delete=models.SET_NULL)
    other_major_numbers = models.CharField(max_length=30,
                                           blank='',
                                           default='')
    other_major_scores = models.CharField(max_length=50,
                                          blank='',
                                          default='')

    class Meta:
        indexes = [
            models.Index(fields=['major','admission_project']),
            models.Index(fields=['applicant']),
            models.Index(fields=['admission_project','applicant']),
            models.Index(fields=['major','admission_project','applicant']),
        ]
        unique_together = (('major','admission_project','applicant'),)

    def get_other_major_numbers(self):
        if self.other_major_numbers == '':
            return []
        return [int(x) for x in self.other_major_numbers.split(',')]
        
    def get_other_major_scores(self):
        if self.other_major_scores == '':
            return []
        return [float(x) for x in self.other_major_scores.split(',')]
        
class ApplicantMajorScore(models.Model):
    admission_project = models.ForeignKey(AdmissionProject,
                                          on_delete=models.CASCADE)
    major = models.ForeignKey(Major,
                              on_delete=models.CASCADE)
    applicant = models.ForeignKey(Applicant,
                                  on_delete=models.CASCADE)

    exam_score = models.ForeignKey(ExamScore,
                                   on_delete=models.CASCADE)
    
    class Meta:
        indexes = [
            models.Index(fields=['major','admission_project']),
            models.Index(fields=['applicant']),
            models.Index(fields=['major','admission_project','applicant']),
        ]
    
class AdjustmentMajor(models.Model):
    full_code = models.CharField(max_length=10,
                                 unique=True)

    major_code = models.CharField(max_length=5)
    study_type_code = models.CharField(max_length=3)
    
    title = models.CharField(max_length=200)

    faculty = models.ForeignKey(Faculty,
                                on_delete=models.CASCADE)

    def __str__(self):
        return self.title
    
    
class AdjustmentMajorSlot(models.Model):
    adjustment_major = models.ForeignKey(AdjustmentMajor,
                                         on_delete=models.CASCADE,
                                         related_name='slots')
    faculty = models.ForeignKey(Faculty,
                                on_delete=models.CASCADE)
    admission_round = models.ForeignKey(AdmissionRound,
                                        on_delete=models.CASCADE)

    admission_round_number = models.IntegerField()

    major_full_code = models.CharField(max_length=10)
    cupt_code = models.CharField(max_length=30,
                                 blank=True)
    
    admission_project_title = models.CharField(max_length=100)

    original_slots = models.IntegerField()
    current_slots = models.IntegerField()

    is_frozen = models.BooleanField(default=False)
    is_confirmed_by_faculty = models.BooleanField(default=False)

    confirmed_slots = models.IntegerField(default=0)
    is_final = models.BooleanField(default=False)

    class Meta:
        ordering = ['admission_round_number', 'cupt_code']
    
    def __str__(self):
        return '%s (%s) (%d) %s' % (self.adjustment_major,
                                    self.admission_project_title,
                                    self.current_slots,
                                    self.cupt_code)

    def is_editable(self):
        return (not self.is_frozen) and (not self.is_final) and (not self.is_confirmed_by_faculty)

