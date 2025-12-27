from datetime import datetime
from random import choice

from django.conf import settings
from django.contrib.auth.hashers import check_password as check_hashed_password
from django.contrib.auth.hashers import make_password
from django.db import models


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

    confirmed_application = models.OneToOneField('appl.ProjectApplication',
                                                 related_name='confirmed_applicant',
                                                 null=True,
                                                 on_delete=models.SET_NULL)

    accepted_application = models.OneToOneField('appl.ProjectApplication',
                                                related_name='accepted_applicant',
                                                null=True,
                                                on_delete=models.SET_NULL)

    additional_data = models.CharField(max_length=50,
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
        application.verification_number = application.get_verification_number()
        application.save()
        
        return application

    def has_registered_with_passport(self):
        return self.national_id.startswith('999')
    
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

    def has_cupt_confirmation_result(self):
        return hasattr(self,'cupt_confirmation')

    def has_confirmed(self):
        if not self.has_cupt_confirmation_result():
            return False
        else:
            return self.cupt_confirmation.has_confirmed
                
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

    def get_all_exam_scores(self):
        from appl.models import ExamScoreProvider

        if not hasattr(self,'exam_score_provider'):
            self.exam_score_provider = ExamScoreProvider(self)
        
        return self.exam_score_provider

    def get_additional_data(self):
        if self.additional_data == '':
            return None
        else:
            import json
            try:
                return json.loads(self.additional_data)
            except:
                return {}

    
class CuptConfirmation(models.Model):
    applicant = models.OneToOneField(Applicant,
                                     related_name='cupt_confirmation',
                                     on_delete=models.CASCADE)
    national_id = models.CharField(max_length=16,
                                   blank=True)
    passport_number = models.CharField(max_length=20,
                                       blank=True)
    has_registered = models.BooleanField(default=False)
    has_confirmed = models.BooleanField(default=False)
    api_result_code = models.IntegerField(default=0)
    
    updated_at = models.DateTimeField()

    STATUS_NOT_REQUIRED = 0
    STATUS_WAIT = 1
    STATUS_FREE = 2
    STATUS_CONFIRMED = 3

    class CuptConfirmationStatus():
        def __init__(self, status, has_registered=False):
            self.status = status
            self.has_registered = has_registered

        def is_not_required(self):
            return self.status == CuptConfirmation.STATUS_NOT_REQUIRED

        def is_wait(self):
            return self.status == CuptConfirmation.STATUS_WAIT

        def is_free(self):    # must have registered
            if not self.has_registered:
                return False
            else:
                return self.status == CuptConfirmation.STATUS_FREE

        def is_confirmed(self):
            return self.status == CuptConfirmation.STATUS_CONFIRMED

        def is_registered(self):
            return self.has_registered
        
    def get_status(self):
        if self.has_confirmed:
            return self.CuptConfirmationStatus(self.STATUS_CONFIRMED, self.has_registered)
        else:
            return self.CuptConfirmationStatus(self.STATUS_FREE, self.has_registered)

    @classmethod
    def get_wait_status(cls):
        return cls.CuptConfirmationStatus(cls.STATUS_WAIT)
        
    @classmethod
    def get_not_required_status(cls):
        return cls.CuptConfirmationStatus(cls.STATUS_NOT_REQUIRED)
        

class CuptRequestQueueItem(models.Model):
    applicant = models.OneToOneField(Applicant,
                                     on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
    
    @staticmethod
    def create_for(applicant):
        try:
            item = CuptRequestQueueItem(applicant=applicant)
            item.save()
            return item
        except:
            return None
    
    
class LogItem(models.Model):
    applicant = models.ForeignKey(Applicant,
                                  blank=True,
                                  null=True,
                                  on_delete=models.SET_NULL)
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
            if ('REMOTE_ADDR' in request.META) and (request.META['REMOTE_ADDR'] != ""):
                log.request_ip = request.META['REMOTE_ADDR']
            elif 'HTTP_X_FORWARDED_FOR' in request.META:
                log.request_ip = request.META['HTTP_X_FORWARDED_FOR']

        log.save()
        return log

    @staticmethod
    def get_applicant_latest_log(applicant, prefix, limit=100):
        items = LogItem.objects.filter(applicant=applicant).all()
        c = 0
        for item in items:
            if item.message.startswith(prefix):
                return item
            c += 1
            if c > limit:
                return None
        return None

    @staticmethod
    def generate_log_key(applicant):
        import hashlib

        m = hashlib.md5()
        m.update(settings.APPL_LOG_APPLICANT_KEY.encode('utf-8'))
        m.update(str(applicant.id).encode('utf-8'))

        return m.hexdigest()
    
    def __str__(self):
        return '(%s) %s' % (self.created_at, self.message)


class CuptUpdatedName(models.Model):
    applicant = models.ForeignKey(Applicant,
                                  on_delete=models.CASCADE)

    field_name = models.CharField(max_length=20)
    updated_value = models.CharField(max_length=200)


    def apply_update(self, applicant, personal_profile):
        if applicant.id != self.applicant.id:
            return

        if self.field_name == 'first_name_th':
            applicant.first_name = self.updated_value
        elif self.field_name == 'last_name_th':
            applicant.last_name = self.updated_value
        elif self.field_name == 'first_name_en':
            personal_profile.first_name_english = self.updated_value
        elif self.field_name == 'last_name_en':
            personal_profile.last_name_english = self.updated_value


