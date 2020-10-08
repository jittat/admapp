from django.db import models

# Create your models here.
from appl.models import AdmissionProject, AdmissionRound, ProjectApplication
from appl.models import Major, Faculty


class AdmissionCriteria(models.Model):
    admission_project = models.ForeignKey(AdmissionProject,
                                          on_delete=models.CASCADE)
    faculty = models.ForeignKey(
        Faculty, on_delete=models.CASCADE, null=True, blank=False)
    version = models.IntegerField(default=1)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class ScoreCriteria(models.Model):
    admission_criteria = models.ForeignKey(AdmissionCriteria,
                                           on_delete=models.CASCADE)
    version = models.IntegerField(default=1)
    primary_order = models.IntegerField()
    secondary_order = models.IntegerField(default=0)
    criteria_type = models.CharField(max_length=30)
    score_type = models.CharField(max_length=30)
    value = models.DecimalField(
        decimal_places=4, max_digits=12, null=True, blank=True)
    unit = models.CharField(max_length=30, default="")
    description = models.TextField(default="")
    parent = models.ForeignKey('self', null=True, blank=True,
                               on_delete=models.CASCADE, related_name='childs')
    relation = models.CharField(max_length=30, null=True, blank=True)


class MajorCuptCode(models.Model):
    program_code = models.CharField(max_length=30)
    program_type = models.CharField(max_length=30)
    program_type_code = models.CharField(max_length=5)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    major = models.ForeignKey(
        Major, on_delete=models.CASCADE, blank=True, null=True)
    major_code = models.CharField(max_length=5,
                                  blank=True)
    title = models.TextField()
    major_title = models.TextField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['program_code','major_code'], name='unique_program_major')
        ]
        ordering = ['program_type_code', 'program_code']
    
    def __str__(self):
        if self.major_title:
            return f'{self.title} {self.major_title} ({self.program_type})'
        else:
            return f'{self.title} ({self.program_type})'

COMPONENT_WEIGHT_TYPE_CHOICES = [
    ('CW1010','1.1: กลุ่ม 1 วิทยาศาสตร์สุขภาพ - สัตวแพทย์ศาสตร์ สหเวชศาสตร์ สาธารณสุขศาสตร์ เทคนิคการแพทย์ พยาบาลศาสตร์ วิทยาศาสตร์การกีฬา'),
    ('CW1020','1.2: กลุ่ม 1 วิทยาศาสตร์สุขภาพ - ทันตแพทย์ศาสตร์'),
    ('CW1030','1.3: เภสัชศาสตร์'),
    ('CW2010','2.1: กลุ่ม 2 วิทยาศาสตร์กายภาพและชีวภาพ - วิทยาศาสตร์ ทรัพยากรธรรมชาติ'),
    ('CW2020','2.2: กลุ่ม 2 วิทยาศาสตร์กายภาพและชีวภาพ - เทคโนโลยีสารสนเทศ'),
    ('CW3000','3: กลุ่ม 3 วิศวกรรมศาสตร์'),
    ('CW4000','4: กลุ่ม 4 สถาปัตยกรรมศาสตร์'),
    ('CW5000','5: กลุ่ม 5 เกษตรศาสตร์ - เกษตรศาสตร์ อุตสาหกรรมเกษตร วนศาสตร์ เทคโนโลยีการเกษตร'),
    ('CW6010','6.1: กลุ่ม 6 - บริหารธุรกิจ พาณิชยศาสตร์ การบัญชี เศรษฐศาสตร์'),
    ('CW6021','6.2 (รูปแบบที่ 1): กลุ่ม 6 - การท่องเที่ยวและการโรงแรม (รูปแบบที่ 1)'),
    ('CW6022','6.2 (รูปแบบที่ 2): กลุ่ม 6 - การท่องเที่ยวและการโรงแรม (รูปแบบที่ 2)'),
    ('CW7001','7 (รูปแบบที่ 1): กลุ่ม 7 ครุศาสตร์ ศึกษาศาสตร์ พลศึกษา สุขศึกษา (รูปแบบที่ 1)'),
    ('CW7002','7 (รูปแบบที่ 2): กลุ่ม 7 ครุศาสตร์ ศึกษาศาสตร์ พลศึกษา สุขศึกษา (รูปแบบที่ 2)'),
    ('CW8000','8: กลุ่ม 8 ศิลปกรรมศาสตร์'),
    ('CW9010','9.1: กลุ่ม 9 มนุษย์ศาสตร์และสังคมศาสตร์ - พื้นฐานวิทยาศาสตร์'),
    ('CW9021','9.2 (รูปแบบที่ 1): กลุ่ม 9 มนุษย์ศาสตร์และสังคมศาสตร์ - พื้นฐานศิลปศาสตร์ (รูปแบบที่ 1)'),
    ('CW9021','9.2 (รูปแบบที่ 2): กลุ่ม 9 มนุษย์ศาสตร์และสังคมศาสตร์ - พื้นฐานศิลปศาสตร์ (รูปแบบที่ 2)'),
]
        
class CurriculumMajor(models.Model):
    admission_project = models.ForeignKey(AdmissionProject,
                                          on_delete=models.CASCADE)
    cupt_code = models.ForeignKey(MajorCuptCode,
                                  on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    major = models.ForeignKey(Major,
                              on_delete=models.CASCADE, null=True)
    admission_criterias = models.ManyToManyField(
        AdmissionCriteria, through='CurriculumMajorAdmissionCriteria')

    def is_with_some_admission_criteria(self):
        return self.admission_criterias.filter(is_deleted=False).count() != 0

    class Meta:
        ordering = ['cupt_code']

class CurriculumMajorAdmissionCriteria(models.Model):
    """
    This is the join table.
    """
    curriculum_major = models.ForeignKey(
        CurriculumMajor, on_delete=models.CASCADE)
    admission_criteria = models.ForeignKey(
        AdmissionCriteria, on_delete=models.CASCADE)
    slots = models.IntegerField()
    version = models.IntegerField(default=1)
