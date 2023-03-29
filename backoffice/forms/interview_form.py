from django import forms
from django.db import transaction

from backoffice.models import (
    InterviewDescription,
    AdmissionProjectMajorCuptCodeInterviewDescription,
)


class InterviewDescriptionForm(forms.ModelForm):
    admission_round_id = None
    faculty_id = None
    project_majors = forms.MultipleChoiceField(choices=(), widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = InterviewDescription
        fields = [
            # TODO: remove the top 3 fields
            "interview_options",
            "interview_date",
            "is_additional_documents_required",
            "preparation_descriptions",
            "preparation_image",
            "descriptions",
            "description_image",
            "contacts",
        ]

    def save(self):
        with transaction.atomic():
            interview_description = super(InterviewDescriptionForm, self).save(commit=False)
            interview_description.admission_round_id = self.admission_round_id
            interview_description.faculty_id = self.faculty_id
            interview_description.save()
            AdmissionProjectMajorCuptCodeInterviewDescription.objects.filter(
                interview_description=interview_description
            ).delete()
            for project_major in self.cleaned_data["project_majors"]:
                major_cupt_code_id, admission_project_id = project_major.split("_")[0:2]
                interview_relation = AdmissionProjectMajorCuptCodeInterviewDescription(
                    admission_project_id=admission_project_id,
                    major_cupt_code_id=major_cupt_code_id,
                    interview_description=interview_description,
                )
                interview_relation.save()

        return interview_description
