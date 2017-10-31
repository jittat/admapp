# -*- coding: utf-8 -*-
import os, sys
from django.db import models

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from appl.models import Campus, Faculty, AdmissionProject, AdmissionRound, ProjectApplication
from regis.models import Applicant


class Profile(models.Model):
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

    created_at = models.DateTimeField(auto_now_add=True)
    
    body = models.TextField()
