from django import forms
from django.db import transaction

from backoffice.models import (
    InterviewDescription,
    AdmissionProjectMajorCuptCodeInterviewDescription,
)


class InterviewDescriptionForm(forms.ModelForm):
    admission_round_id = None
    faculty_id = None

    project_majors = forms.MultipleChoiceField(choices=(), widget=forms.CheckboxSelectMultiple, required=False)

    class Meta:
        model = InterviewDescription
        fields = [
            "span_option",
            "interview_options",
            "video_conference_platform",
            "interview_date",
            "additional_documents_option",
            "preparation_descriptions",
            "preparation_image",
            "descriptions",
            "description_image",
            "contacts",
        ]
        widgets = {
            "span_option": forms.RadioSelect(),
            "interview_options": forms.Select(attrs={"class": "form-control"}),
            "interview_date": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "additional_documents_option": forms.Select(attrs={"class": "form-control"}),
            "preparation_descriptions": forms.Textarea(
                attrs={"class": "form-control", "rows": "2"}
            ),
            "preparation_image": forms.FileInput(
                attrs={"class": "custom-file-input img-file-controls", "data-img-id": "prepImgId"}
            ),
            "descriptions": forms.Textarea(attrs={"class": "form-control", "rows": "3"}),
            "description_image": forms.FileInput(
                attrs={"class": "custom-file-input img-file-controls", "data-img-id": "descImgId"}
            ),
            "contacts": forms.HiddenInput(),
            "video_conference_platform": forms.RadioSelect(
                choices=[
                    ("webex", "Cisco Webex"),
                    ("zoom", "Zoom"),
                    ("google-meet", "Google Meet"),
                    ("other", "โปรแกรมอื่น (กรุณาระบุในรายละเอียด)"),
                ]
            ),
        }
        help_texts = {
            "descriptions": "ป้อนลายละเอียด เช่น ลิงก์สำหรับสัมภาษณ์ รหัสผ่าน",
            "description_image": "รูปจะปรากฏด้านขวาของข้อความ",
            "preparation_image": "รูปจะปรากฏด้านขวาของข้อความ",
        }

    def save(self, commit=True):
        with transaction.atomic():
            interview_description = super(InterviewDescriptionForm, self).save(commit=False)
            interview_description.admission_round_id = self.admission_round_id
            interview_description.faculty_id = self.faculty_id

            selected_project_majors = list()
            
            for project_major in self.cleaned_data["project_majors"]:
                major_cupt_code_id, admission_project_id = project_major.split("_")[0:2]
                selected_project_majors.append((major_cupt_code_id, admission_project_id))

            # cast it to set to removing duplictae pair of (major, project)
            selected_project_majors = set(selected_project_majors)
            
            if commit:
                interview_description.save()
                print(interview_description, interview_description.interview_date)
                AdmissionProjectMajorCuptCodeInterviewDescription.objects.filter(
                    interview_description=interview_description
                ).delete()
                for major_cupt_code_id, admission_project_id in selected_project_majors:
                    interview_relation = (
                        AdmissionProjectMajorCuptCodeInterviewDescription(
                            admission_project_id=admission_project_id,
                            major_cupt_code_id=major_cupt_code_id,
                            interview_description=interview_description,
                        )
                    )
                    interview_relation.save()

        return interview_description
