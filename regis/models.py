from django.db import models
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password as check_hashed_password

class Applicant(models.Model):
    national_id = models.CharField(max_length=16,
                                   unique=True)
    prefix = models.CharField(max_length=10)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=200)
    
    email = models.EmailField()

    hashed_password = models.CharField(max_length=128,
                                       blank=True)
    
    def __str__(self):
        return "%s%s %s (%s)" % (self.prefix,
                                 self.first_name,
                                 self.last_name,
                                 self.national_id)

    @staticmethod
    def find_by_national_id(national_id):
        try:
            applicant = Applicant.objects.get(national_id=national_id)
            return applicant
        except Applicant.DoesNotExist:
            return None

    def set_password(self, password):
        self.hashed_password = make_password(password)
        
    def check_password(self, password):
        return check_hashed_password(password, self.hashed_password)
