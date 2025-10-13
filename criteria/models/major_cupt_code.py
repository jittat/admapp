from django.db import models

from appl.models import Faculty


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

    def get_program_major_code_as_str(self):
        if self.major_code == '':
            return self.program_code
        else:
            return f'{self.program_code}0{self.major_code}'
    
    @staticmethod
    def get_from_full_code(full_code):
        if len(full_code) > 15:
            program_code = full_code[:-2]
            major_code = full_code[-1:]
        else:
            program_code = full_code
            major_code = ''
        
        try:
            cupt_code = MajorCuptCode.objects.get(program_code=program_code, major_code=major_code)
            return cupt_code
        except MajorCuptCode.DoesNotExist:
            return None
