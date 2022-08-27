from django.db import models

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

    additional_description = models.CharField(max_length=100, blank=True)
    additional_condition = models.CharField(max_length=500, blank=True)
    additional_interview_condition = models.TextField(blank=True)
    
    curriculum_majors_json = models.TextField(blank=True) 

    def get_all_score_criteria(self, criteria_type):
        if getattr(self,'cached_score_criteria',None) == None:
            self.cached_score_criteria = self.scorecriteria_set.all()
        return [c for c in self.cached_score_criteria
                if c.criteria_type==criteria_type and c.secondary_order==0]

    def get_all_required_score_criteria(self):
        if getattr(self,'cached_required_score_criteria',None) == None:
            self.cached_required_score_criteria = list(self.get_all_score_criteria('required'))
        return self.cached_required_score_criteria

    def get_all_scoring_score_criteria(self):
        if getattr(self,'cached_scoring_score_criteria',None) == None:
            self.cached_scoring_score_criteria = list(self.get_all_score_criteria('scoring'))
        return self.cached_scoring_score_criteria

    def required_score_criteria_includes(self, conds):
        criteria = self.get_all_required_score_criteria()
        for c in criteria:
            for cond in conds:
                if cond in c.description:
                    return True
        return False
    
    def required_score_criteria_exclude(self, conds):
        criteria = self.get_all_required_score_criteria()
        for c in criteria:
            for cond in conds:
                if cond in c.description:
                    return False
        return True
    
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

    def cache_score_criteria_children(self):
        required = self.get_all_required_score_criteria()
        scoring = self.get_all_scoring_score_criteria()

        all_score_criterias = self.cached_score_criteria
        for lst in [required, scoring]:
            for sc in lst:
                sc.cache_children(all_score_criterias)

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

    def __str__(self, relation_display=None):
        if relation_display == None:
            relation_display = self.get_relation_display()
            
        if self.criteria_type == 'required':
            if self.value:
                return f'{self.description} {relation_display} ไม่ต่ำกว่า {self.value:.2f} {self.unit}'
            else:
                return f'{self.description} {relation_display}'
        elif self.criteria_type == 'scoring':
            if self.value:
                if self.secondary_order == 0:
                    return f'{self.description} {relation_display} สัดส่วน {self.value:.2f}'
                else:
                    return f'{self.description} {relation_display} สัดส่วนย่อย {self.value:.2f}'
            else:
                return f'{self.description} {relation_display}'
        else:
            return self.description

    def display_with_short_relation(self):
        if self.relation == 'AND':
            relation_display = ''
        else:
            relation_display = self.get_relation_display()

        return self.__str__(relation_display)

    def cache_children(self, score_criterias):
        self.cached_children = []
        for c in score_criterias:
            if c.parent_id == self.id:
                self.cached_children.append(c)
        
    def has_children(self):
        if getattr(self,'cached_children',None) != None:
            return self.cached_children != []
        else:
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

    def display_title(self):
        type_code_map = {'A': '',
                         'B': ' (ภาคพิเศษ)',
                         'D': ' (หลักสูตรภาษาอังกฤษ)',
                         'E': ' (นานาชาติ)',
                         'G': ' (Double Degree - นานาชาติ)'}
        
        if self.major_title:
            return f'{self.title} {self.major_title}{type_code_map[self.program_type_code]}'
        else:
            return f'{self.title}{type_code_map[self.program_type_code]}'

    def get_program_major_code(self):
        return (self.program_code, self.major_code)

    
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
