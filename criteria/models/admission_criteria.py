from django.db import models

from appl.models import AdmissionProject, Faculty


def criteria_as_str(criteria):
    items = []
    for c in criteria:
        items.append(str(c))
        if c.has_children():
            for child in c.childs.all():
                items.append('  - ' + str(child))
    return '\n'.join(items)


class AdmissionCriteria(models.Model):
    INITIAL_CURR_TYPE_FLAG = '*'
    DEFAULT_TYPE_FLAG = '1,2,3,4,5'

    STUDENT_CURRICULUM_TYPE_CHOICES = {
        1: ('formal', 'หลักสูตรแกนกลาง', 'แกนกลาง', 'badge-primary'),
        2: ('international', 'หลักสูตรนานาชาติ', 'นานาชาติ', 'badge-secondary'),
        3: ('vocational', 'หลักสูตรอาชีวะ', 'อาชีวะ', 'badge-success'),
        4: ('non_formal', 'หลักสูตรตามอัธยาศัย (กศน.)', 'กศน.', 'badge-danger'),
        5: ('ged', 'หลักสูตร GED', 'GED', 'badge-dark'),
    }
    STUDENT_CURRICULUM_TYPE_CHOICE_COUNT = 5

    INITIAL_GRADUATE_YEAR_FLAG = '*'
    DEFAULT_GRADUATE_YEAR_FLAG = '1,2'
    
    STUDENT_GRADUATE_YEAR_CHOICES = {
        1: ('current','กำลังศึกษา ม.6', 'ม.6', 'badge-success'),
        2: ('graduated','จบ ม.6 ในปีที่แล้ว', 'จบปีก่อน', 'badge-warning'),
    }
    STUDENT_GRADUATE_YEAR_CHOICE_COUNT = 2
    
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

    accepted_student_curriculum_type_flags = models.CharField(max_length=10,
                                                              default=INITIAL_CURR_TYPE_FLAG,
                                                              blank=True)
    accepted_graduate_year_flags = models.CharField(max_length=10,
                                                    default=INITIAL_GRADUATE_YEAR_FLAG,
                                                    blank=True)

    curriculum_majors_json = models.TextField(blank=True)

    interview_date = models.DateField(verbose_name='วันสัมภาษณ์',
                                      blank=True,
                                      null=True)
    
    def get_all_score_criteria(self, criteria_type):
        if getattr(self, 'cached_score_criteria', None) is None:
            self.cached_score_criteria = self.scorecriteria_set.all()
        return [c for c in self.cached_score_criteria
                if c.criteria_type == criteria_type and c.secondary_order == 0]

    def get_all_required_score_criteria(self):
        if getattr(self, 'cached_required_score_criteria', None) is None:
            self.cached_required_score_criteria = list(self.get_all_score_criteria('required'))
        return self.cached_required_score_criteria

    def get_all_required_score_criteria_as_str(self):
        return criteria_as_str(self.get_all_required_score_criteria())

    def get_all_scoring_score_criteria(self):
        if getattr(self, 'cached_scoring_score_criteria', None) is None:
            self.cached_scoring_score_criteria = list(self.get_all_score_criteria('scoring'))
        return self.cached_scoring_score_criteria

    def get_all_scoring_score_criteria_as_str(self):
        return criteria_as_str(self.get_all_scoring_score_criteria())

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

    def get_flag_ids(self, flags, initial, default):
        if flags == initial:
            flags = default

        if flags == '':
            return []
        else:
            return [int(x.strip()) for x in flags.split(',')]

    def get_accepted_student_curriculum_type_ids(self):
        return self.get_flag_ids(self.accepted_student_curriculum_type_flags,
                                 AdmissionCriteria.INITIAL_CURR_TYPE_FLAG,
                                 AdmissionCriteria.DEFAULT_TYPE_FLAG)

    def get_accepted_graduate_year_ids(self):
        return self.get_flag_ids(self.accepted_graduate_year_flags,
                                 AdmissionCriteria.INITIAL_GRADUATE_YEAR_FLAG,
                                 AdmissionCriteria.DEFAULT_GRADUATE_YEAR_FLAG)

    def get_accepted_student_curriculum_types(self):
        return [AdmissionCriteria.STUDENT_CURRICULUM_TYPE_CHOICES[i] for i in
                self.get_accepted_student_curriculum_type_ids()]

    def get_choices_with_acceptance(self, choices, accepted_choices):
        return [(k, k in accepted_choices, v) for k, v in choices]
        
    def get_curriculum_type_choices_with_acceptance(self):
        return self.get_choices_with_acceptance(AdmissionCriteria.STUDENT_CURRICULUM_TYPE_CHOICES.items(),
                                                self.get_accepted_student_curriculum_type_ids())
    
    def get_accepted_graduate_years(self):
        return [AdmissionCriteria.STUDENT_GRADUATE_YEAR_CHOICES[i] for i in
                self.get_accepted_graduate_year_ids()]

    def get_graduate_year_choices_with_acceptance(self):
        return self.get_choices_with_acceptance(AdmissionCriteria.STUDENT_GRADUATE_YEAR_CHOICES.items(),
                                                self.get_accepted_graduate_year_ids())
    
    def is_curriculum_type_accepted(self, curriculum_type):
        if self.accepted_student_curriculum_type_flags == AdmissionCriteria.INITIAL_CURR_TYPE_FLAG:
            flags = AdmissionCriteria.DEFAULT_TYPE_FLAG
        else:
            flags = self.accepted_student_curriculum_type_flags
        return str(curriculum_type) in flags

    def is_all_curriculum_types_accepted(self):
        if self.accepted_student_curriculum_type_flags == AdmissionCriteria.INITIAL_CURR_TYPE_FLAG:
            return True
        else:
            ts = self.accepted_student_curriculum_type_flags.split(',')
            return len(ts) == AdmissionCriteria.STUDENT_CURRICULUM_TYPE_CHOICE_COUNT

    def toggle_accepted_curriculum_type(self, cur_type):
        accepted_types = self.get_accepted_student_curriculum_type_ids()
        if cur_type in accepted_types:
            accepted_types = [t for t in accepted_types if t != cur_type]
        else:
            accepted_types.append(cur_type)
        self.accepted_student_curriculum_type_flags = ','.join([str(t) for t in sorted(accepted_types)])

    def toggle_accepted_graduate_year(self, year):
        accepted_years = self.get_accepted_graduate_year_ids()
        if year in accepted_years:
            accepted_years = [t for t in accepted_years if t != year]
        else:
            accepted_years.append(year)
        self.accepted_graduate_year_flags = ','.join([str(t) for t in sorted(accepted_years)])
