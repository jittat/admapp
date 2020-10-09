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


COMPONENT_WEIGHT_TYPE_CHOICES = [
    ('CW110','1.1: กลุ่ม 1 วิทยาศาสตร์สุขภาพ - สัตวแพทย์ศาสตร์ สหเวชศาสตร์ สาธารณสุขศาสตร์ เทคนิคการแพทย์ พยาบาลศาสตร์ วิทยาศาสตร์การกีฬา'),
    ('CW120','1.2: กลุ่ม 1 วิทยาศาสตร์สุขภาพ - ทันตแพทย์ศาสตร์'),
    ('CW130','1.3: กลุ่ม 1 วิทยาศาสตร์สุขภาพ - เภสัชศาสตร์'),
    ('CW210','2.1: กลุ่ม 2 วิทยาศาสตร์กายภาพและชีวภาพ - วิทยาศาสตร์ ทรัพยากรธรรมชาติ'),
    ('CW220','2.2: กลุ่ม 2 วิทยาศาสตร์กายภาพและชีวภาพ - เทคโนโลยีสารสนเทศ'),
    ('CW300','3: กลุ่ม 3 วิศวกรรมศาสตร์'),
    ('CW400','4: กลุ่ม 4 สถาปัตยกรรมศาสตร์'),
    ('CW500','5: กลุ่ม 5 เกษตรศาสตร์ - เกษตรศาสตร์ อุตสาหกรรมเกษตร วนศาสตร์ เทคโนโลยีการเกษตร'),
    ('CW610','6.1: กลุ่ม 6 - บริหารธุรกิจ พาณิชยศาสตร์ การบัญชี เศรษฐศาสตร์'),
    ('CW621','6.2 (รูปแบบที่ 1): กลุ่ม 6 - การท่องเที่ยวและการโรงแรม (รูปแบบที่ 1)'),
    ('CW622','6.2 (รูปแบบที่ 2): กลุ่ม 6 - การท่องเที่ยวและการโรงแรม (รูปแบบที่ 2)'),
    ('CW701','7 (รูปแบบที่ 1): กลุ่ม 7 ครุศาสตร์ ศึกษาศาสตร์ พลศึกษา สุขศึกษา (รูปแบบที่ 1)'),
    ('CW702','7 (รูปแบบที่ 2): กลุ่ม 7 ครุศาสตร์ ศึกษาศาสตร์ พลศึกษา สุขศึกษา (รูปแบบที่ 2)'),
    ('CW800','8: กลุ่ม 8 ศิลปกรรมศาสตร์'),
    ('CW910','9.1: กลุ่ม 9 มนุษย์ศาสตร์และสังคมศาสตร์ - พื้นฐานวิทยาศาสตร์'),
    ('CW921','9.2 (รูปแบบที่ 1): กลุ่ม 9 มนุษย์ศาสตร์และสังคมศาสตร์ - พื้นฐานศิลปศาสตร์ (รูปแบบที่ 1)'),
    ('CW922','9.2 (รูปแบบที่ 2): กลุ่ม 9 มนุษย์ศาสตร์และสังคมศาสตร์ - พื้นฐานศิลปศาสตร์ (รูปแบบที่ 2)'),
]
        
class MajorCuptCode(models.Model):
    program_code = models.CharField(max_length=30)
    program_type = models.CharField(max_length=30)
    program_type_code = models.CharField(max_length=5)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    major_code = models.CharField(max_length=5,
                                  blank=True)
    title = models.TextField()
    major_title = models.TextField(null=True, blank=True)

    component_weight_type = models.CharField(max_length=5,
                                             blank=True)

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

    def get_component_weight_type_choices(self):
        component_weight_type = self.cupt_code.component_weight_type

        if component_weight_type.endswith('0'):
            prefix = 'CW' + component_weight_type[0]
        else:
            prefix = 'CW' + component_weight_type
        
        choices = [ch for ch in COMPONENT_WEIGHT_TYPE_CHOICES
                   if ch[0].startswith(prefix)]
        return choices

    @staticmethod
    def get_component_weight_type_choices_unique(curriculum_majors):
        added = set()
        choices = []
        for m in curriculum_majors:
            for ch in m.get_component_weight_type_choices():
                if ch[0] not in added:
                    choices.append(ch)
                    added.add(ch[0])
        return choices
        
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
