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
    created_by = models.CharField(max_length=30, blank=True)

    curriculum_majors_json = models.TextField(blank=True) 

    def get_all_score_criteria(self, criteria_type):
        return self.scorecriteria_set.filter(criteria_type=criteria_type, secondary_order=0).all()
    
    def get_all_required_score_criteria(self):
        return self.get_all_score_criteria('required')

    def get_all_scoring_score_criteria(self):
        return self.get_all_score_criteria('scoring')

    def save_curriculum_majors(self, curriculum_major_admission_criterias=None):
        import json
        
        if not curriculum_major_admission_criterias:
            curriculum_major_admission_criterias = self.curriculummajoradmissioncriteria_set.all()
        data = []
        for c in curriculum_major_admission_criterias:
            major_cupt_code = c.curriculum_major.cupt_code
            try:
                slots = int(float(c.slots))
            except:
                slots = 0
            data.append({'curriculum_major_id': c.curriculum_major.id,
                         'slots': slots,
                         'major_cupt_code_id': major_cupt_code.id,
                         'program_code': major_cupt_code.program_code,
                         'program_type_code': major_cupt_code.program_type_code,
                         'major_code': major_cupt_code.major_code})

        self.curriculum_majors_json = json.dumps(data)
        self.save()
        

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
    
    class Meta:
        ordering = ['primary_order', 'secondary_order']

    def __str__(self):
        if self.criteria_type == 'required':
            if self.value:
                return f'{self.description} {self.get_relation_display()} ไม่ต่ำกว่า {self.value:.2f} {self.unit}'
            else:
                return f'{self.description} {self.get_relation_display()}'
        elif self.criteria_type == 'scoring':
            if self.value:
                if self.secondary_order == 0:
                    return f'{self.description} {self.get_relation_display()} สัดส่วน {self.value:.2f}'
                else:
                    return f'{self.description} {self.get_relation_display()} สัดส่วนย่อย {self.value:.2f}'
            else:
                return f'{self.description} {self.get_relation_display()}'
        else:
            return self.description
        
    def has_children(self):
        return self.childs.count() != 0
        
    def get_relation_display(self):
        REQUIRED_REL_DISPLAY = {
            "OR": "ข้อใดข้อหนึ่ง",
            "AND": "ทุกข้อ",
            "SUM": "ใช้คะแนนรวม",
            "MAX": "ใช้คะแนนมากที่สุด",
        }         
        SCORING_REL_DISPLAY = {
            "MAX": "ใช้คะแนนมากที่สุด",
            "SUM": "ใช้คะแนนรวมตามสัดส่วน",
        }

        if self.relation:
            if self.criteria_type == 'required':
                return REQUIRED_REL_DISPLAY.get(self.relation, self.relation)
            else:
                return SCORING_REL_DISPLAY.get(self.relation, self.relation)
        else:
            return ''


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
    ('CW622','6.2 (รูปแบบที่ 2): **** ยังไม่ได้เลือก PAT7 **** กลุ่ม 6 - การท่องเที่ยวและการโรงแรม (รูปแบบที่ 2)'),
    ('CW62271','6.2 (รูปแบบที่ 2 PAT 7.1 ฝรั่งเศษ): กลุ่ม 6 - การท่องเที่ยวและการโรงแรม (รูปแบบที่ 2)'),
    ('CW62272','6.2 (รูปแบบที่ 2 PAT 7.2 เยอรมัน): กลุ่ม 6 - การท่องเที่ยวและการโรงแรม (รูปแบบที่ 2)'),
    ('CW62273','6.2 (รูปแบบที่ 2 PAT 7.3 ญี่ปุ่น): กลุ่ม 6 - การท่องเที่ยวและการโรงแรม (รูปแบบที่ 2)'),
    ('CW62274','6.2 (รูปแบบที่ 2 PAT 7.4 จีน): กลุ่ม 6 - การท่องเที่ยวและการโรงแรม (รูปแบบที่ 2)'),
    ('CW62275','6.2 (รูปแบบที่ 2 PAT 7.5 อาหรับ): กลุ่ม 6 - การท่องเที่ยวและการโรงแรม (รูปแบบที่ 2)'),
    ('CW62276','6.2 (รูปแบบที่ 2 PAT 7.6 บาลี): กลุ่ม 6 - การท่องเที่ยวและการโรงแรม (รูปแบบที่ 2)'),
    ('CW62277','6.2 (รูปแบบที่ 2 PAT 7.7 เกาหลี): กลุ่ม 6 - การท่องเที่ยวและการโรงแรม (รูปแบบที่ 2)'),
    ('CW701','7 (รูปแบบที่ 1): **** ยังไม่ได้เลือก PAT **** กลุ่ม 7 ครุศาสตร์ ศึกษาศาสตร์ พลศึกษา สุขศึกษา (รูปแบบที่ 1)'),
    ('CW7021','7 (รูปแบบที่ 2 PAT 1 คณิตศาสตร์): กลุ่ม 7 ครุศาสตร์ ศึกษาศาสตร์ พลศึกษา สุขศึกษา (รูปแบบที่ 2)'),
    ('CW7022','7 (รูปแบบที่ 2 PAT 2 วิทยาศาสตร์): กลุ่ม 7 ครุศาสตร์ ศึกษาศาสตร์ พลศึกษา สุขศึกษา (รูปแบบที่ 2)'),
    ('CW7023','7 (รูปแบบที่ 2 PAT 3 วิศวกรรมศาสตร์): กลุ่ม 7 ครุศาสตร์ ศึกษาศาสตร์ พลศึกษา สุขศึกษา (รูปแบบที่ 2)'),
    ('CW7024','7 (รูปแบบที่ 2 PAT 4 สถาปัตยกรรมศาสตร์): กลุ่ม 7 ครุศาสตร์ ศึกษาศาสตร์ พลศึกษา สุขศึกษา (รูปแบบที่ 2)'),
    ('CW7026','7 (รูปแบบที่ 2 PAT 6 ศิลปกรรมศาสตร์): กลุ่ม 7 ครุศาสตร์ ศึกษาศาสตร์ พลศึกษา สุขศึกษา (รูปแบบที่ 2)'),
    ('CW70271','7 (รูปแบบที่ 2 PAT 7.1 ฝรั่งเศส): กลุ่ม 7 ครุศาสตร์ ศึกษาศาสตร์ พลศึกษา สุขศึกษา (รูปแบบที่ 2)'),
    ('CW70272','7 (รูปแบบที่ 2 PAT 7.2 เยอรมัน): กลุ่ม 7 ครุศาสตร์ ศึกษาศาสตร์ พลศึกษา สุขศึกษา (รูปแบบที่ 2)'),
    ('CW70273','7 (รูปแบบที่ 2 PAT 7.3 ญี่ปุ่น): กลุ่ม 7 ครุศาสตร์ ศึกษาศาสตร์ พลศึกษา สุขศึกษา (รูปแบบที่ 2)'),
    ('CW70274','7 (รูปแบบที่ 2 PAT 7.4 จีน): กลุ่ม 7 ครุศาสตร์ ศึกษาศาสตร์ พลศึกษา สุขศึกษา (รูปแบบที่ 2)'),
    ('CW70275','7 (รูปแบบที่ 2 PAT 7.5 อาหรับ): กลุ่ม 7 ครุศาสตร์ ศึกษาศาสตร์ พลศึกษา สุขศึกษา (รูปแบบที่ 2)'),
    ('CW70276','7 (รูปแบบที่ 2 PAT 7.6 บาลี): กลุ่ม 7 ครุศาสตร์ ศึกษาศาสตร์ พลศึกษา สุขศึกษา (รูปแบบที่ 2)'),
    ('CW70277','7 (รูปแบบที่ 2 PAT 7.7 เกาหลี): กลุ่ม 7 ครุศาสตร์ ศึกษาศาสตร์ พลศึกษา สุขศึกษา (รูปแบบที่ 2)'),
    ('CW800','8: **** ยังไม่ได้เลือก PAT **** กลุ่ม 8 ศิลปกรรมศาสตร์'),
    ('CW8004','8: (เลือก PAT 4) กลุ่ม 8 ศิลปกรรมศาสตร์'),
    ('CW8006','8: (เลือก PAT 6) กลุ่ม 8 ศิลปกรรมศาสตร์'),
    ('CW910','9.1: กลุ่ม 9 มนุษย์ศาสตร์และสังคมศาสตร์ - พื้นฐานวิทยาศาสตร์'),
    ('CW921','9.2 (รูปแบบที่ 1): กลุ่ม 9 มนุษย์ศาสตร์และสังคมศาสตร์ - พื้นฐานศิลปศาสตร์ (รูปแบบที่ 1)'),
    ('CW922','9.2 (รูปแบบที่ 2): **** ยังไม่ได้เลือก PAT 7 **** กลุ่ม 9 มนุษย์ศาสตร์และสังคมศาสตร์ - พื้นฐานศิลปศาสตร์ (รูปแบบที่ 2)'),
    ('CW92271','9.2 (รูปแบบที่ 2 PAT 7.1 ฝรั่งเศส): กลุ่ม 9 มนุษย์ศาสตร์และสังคมศาสตร์ - พื้นฐานศิลปศาสตร์ (รูปแบบที่ 2)'),
    ('CW92272','9.2 (รูปแบบที่ 2 PAT 7.2 เยอรมัน): กลุ่ม 9 มนุษย์ศาสตร์และสังคมศาสตร์ - พื้นฐานศิลปศาสตร์ (รูปแบบที่ 2)'),
    ('CW92273','9.2 (รูปแบบที่ 2 PAT 7.3 ญี่ปุ่น): กลุ่ม 9 มนุษย์ศาสตร์และสังคมศาสตร์ - พื้นฐานศิลปศาสตร์ (รูปแบบที่ 2)'),
    ('CW92274','9.2 (รูปแบบที่ 2 PAT 7.4 จีน): กลุ่ม 9 มนุษย์ศาสตร์และสังคมศาสตร์ - พื้นฐานศิลปศาสตร์ (รูปแบบที่ 2)'),
    ('CW92275','9.2 (รูปแบบที่ 2 PAT 7.5 อาหรับ): กลุ่ม 9 มนุษย์ศาสตร์และสังคมศาสตร์ - พื้นฐานศิลปศาสตร์ (รูปแบบที่ 2)'),
    ('CW92276','9.2 (รูปแบบที่ 2 PAT 7.6 บาลี): กลุ่ม 9 มนุษย์ศาสตร์และสังคมศาสตร์ - พื้นฐานศิลปศาสตร์ (รูปแบบที่ 2)'),
    ('CW92277','9.2 (รูปแบบที่ 2 PAT 7.7 เกาหลี): กลุ่ม 9 มนุษย์ศาสตร์และสังคมศาสตร์ - พื้นฐานศิลปศาสตร์ (รูปแบบที่ 2)'),
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

    component_weight_type = models.CharField(max_length=10,
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
