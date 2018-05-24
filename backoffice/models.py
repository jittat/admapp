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

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    faculty = models.ForeignKey(Faculty,
                                verbose_name='คณะที่สังกัด',
                                default=None,
                                null=True,
                                blank=True)
    is_admission_admin = models.BooleanField(verbose_name='ดูแลข้อมูลทุกคณะ',
                                             default=False)

    admission_projects = models.ManyToManyField(AdmissionProject,
                                                blank=True)
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

    applicant = models.ForeignKey(Applicant)
    project_application = models.OneToOneField(ProjectApplication,
                                               related_name='check_mark_group')
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
    applicant = models.ForeignKey(Applicant)
    project_application = models.ForeignKey(ProjectApplication,
                                            related_name='judge_comment_set')

    author_username = models.CharField(max_length=30,
                                       blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    body = models.TextField()

    is_deleted = models.BooleanField(default=False)
    is_shared_in_major = models.BooleanField(default=False)
    
    admission_project = models.ForeignKey(AdmissionProject,
                                          blank=True,
                                          null=True,
                                          default=None)
    admission_round = models.ForeignKey(AdmissionRound,
                                        blank=True,
                                        null=True,
                                        default=None)
    major = models.ForeignKey(Major,
                              blank=True,
                              null=True,
                              default=None)
    
    class Meta:
        ordering = ['-created_at']


class MajorInterviewCallDecision(models.Model):
    FLOAT_DELTA = 0.000001
    
    admission_project = models.ForeignKey(AdmissionProject)
    admission_round = models.ForeignKey(AdmissionRound)
    major = models.ForeignKey(Major)

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
    admission_project = models.ForeignKey(AdmissionProject)
    major = models.ForeignKey(Major)
    applicant = models.ForeignKey(Applicant)
    project_application = models.ForeignKey(ProjectApplication,
                                            null=True)
    admission_result = models.ForeignKey(AdmissionResult,
                                         null=True)
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
        if self.other_major_numbers == '':
            return []
        return [float(x) for x in self.other_major_scores.split(',')]
        
class ApplicantMajorScore(models.Model):
    admission_project = models.ForeignKey(AdmissionProject)
    major = models.ForeignKey(Major)
    applicant = models.ForeignKey(Applicant)

    exam_score = models.ForeignKey(ExamScore)
    
    class Meta:
        indexes = [
            models.Index(fields=['major','admission_project']),
            models.Index(fields=['applicant']),
            models.Index(fields=['major','admission_project','applicant']),
        ]
    
