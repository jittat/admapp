from random import choice

from django.db import models
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password as check_hashed_password

from datetime import datetime

class Applicant(models.Model):
    national_id = models.CharField(max_length=16,
                                   unique=True)
    passport_number = models.CharField(max_length=20, 
                                       blank=True)
    prefix = models.CharField(max_length=10)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=200)
    
    email = models.EmailField()

    hashed_password = models.CharField(max_length=128,
                                       blank=True)
    
    class Meta:
        unique_together = ('national_id', 'passport_number')

    def __str__(self):
        if self.passport_number:
            handle = self.passport_number
        else:
            handle = self.national_id
        return "%s%s %s (%s)" % (self.prefix,
                                 self.first_name,
                                 self.last_name,
                                 handle)

    def get_full_name(self):
        return "{0}{1} {2}".format(self.prefix, self.first_name, self.last_name)
        
    def set_password(self, password):
        self.hashed_password = make_password(password)

    def random_password(self):
        alpha = '0123456789abcdefghijklmnopqrstuvwxyz'
        new_password = ''.join([choice(alpha) for i in range(6)])
        self.set_password(new_password)
        return new_password

    def check_password(self, password):
        return check_hashed_password(password, self.hashed_password)

    def get_personal_profile(self):
        try:
            profile = self.personalprofile
            return profile
        except:
            return None

    def get_educational_profile(self):
        try:
            profile = self.educationalprofile
            return profile
        except:
            return None

    def get_active_application(self, admission_round):
        applications = self.project_applications.filter(is_canceled=False, admission_round=admission_round).all()
        if len(applications) > 0:
            return applications[0]
        else:
            return None

    def get_all_active_applications(self):
        return self.project_applications.filter(is_canceled=False).all()

    def apply_to_project(self, admission_project, admission_round):
        from appl.models import ProjectApplication

        application = ProjectApplication(applicant=self,
                                         admission_project=admission_project,
                                         admission_round=admission_round)
        application.applied_at = datetime.now()
        application.save()
        
        return application

    def generate_random_national_id_and_save(self):
        applicants = Applicant.objects.filter(passport_number=self.passport_number).all()
        if len(applicants) != 0:
            return False
        else:
            while True:
                import random
            
                fake_national_id = '999'
                number = random.randint(0, 9999999)
                fake_national_id += str(number)
                zero = '0' * (13 - len(fake_national_id))
                fake_national_id += zero

                mul = 13
                total = 0
                for c in fake_national_id[:-1]:
                    total += mul * int(c)
                    mul -= 1
                r1 = total % 11
                checkdigit = (11 - r1) % 10
                fake_national_id = fake_national_id[:-1] + str(checkdigit)

                self.national_id = fake_national_id
                try:
                    self.save()
                    return True
                except:
                    continue
        
    @staticmethod
    def find_by_national_id(national_id):
        try:
            applicant = Applicant.objects.get(national_id=national_id)
            return applicant
        except Applicant.DoesNotExist:
            return None

    @staticmethod
    def find_by_passport_number(number):
        applicants = Applicant.objects.filter(passport_number=number).all()
        if len(applicants) != 0:
            return applicants[0]
        else:
            return None


    @staticmethod
    def find_by_query(query):
        items = query.split()
        if len(items) == 0:
            return []
        
        if (len(items) == 1) and (len(items[0]) == 13):
            a = Applicant.find_by_national_id(items[0])
            if a:
                return [a]
            else:
                return []

        results = []
        if len(items) == 2:
            results += Applicant.objects.filter(first_name__contains=items[0],
                                                last_name__contains=items[1]).all()

        else:
            q = items[0]
            results += Applicant.objects.filter(first_name__contains=q).all()
            results += Applicant.objects.filter(last_name__contains=q).all()
            results += Applicant.objects.filter(passport_number__contains=q).all()

        return results


class LogItem(models.Model):
    applicant = models.ForeignKey(Applicant,
                                  blank=True,
                                  null=True)
    message = models.CharField(max_length=200)
    
    request_ip = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @staticmethod
    def create(message, applicant=None, request=None):
        log = LogItem(applicant=applicant,
                      message=message)
        if request:
            if ('REMOTE_ADDR' in request.META) and (request.META['REMOTE_ADDR'] != "b''"):
                log.request_ip = request.META['REMOTE_ADDR']
            elif 'HTTP_X_FORWARDED_FOR' in request.META:
                log.request_ip = request.META['HTTP_X_FORWARDED_FOR']

        log.save()
        return log
    
    def __str__(self):
        return '(%s) %s' % (self.created_at, self.message)

