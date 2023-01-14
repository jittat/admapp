from django.db import models

from criteria.models import AdmissionCriteria


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
        if getattr(self, 'cached_children', None) != None:
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
