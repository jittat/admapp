from django import forms

from backoffice.models import (
    InterviewDescription,
    AdmissionProjectMajorCuptCodeInterviewDescription,
)
from django.db import transaction


class InterviewForm(forms.Form):
    project_majors = forms.MultipleChoiceField(choices=(), widget=forms.CheckboxSelectMultiple)
    interview_type = forms.ChoiceField(
        choices=[
            ("no_interview", "ไม่มีการสัมภาษณ์"),
            ("online_interview", "สัมภาษณ์ออนไลน์"),
            ("on_site_interview", "สัมภาษณ์ที่สถานที่"),
        ],
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    additional_doc = forms.ChoiceField(
        choices=[
            ("no_doc", "ไม่มี"),
            (
                "has_doc",
                "ต้องส่งเอกสารหรือส่งลิงก์เพิ่มเติม (กรุณาแจ้งรายละเอียดในส่วนการสัมภาษณ์ด้วย)",
            ),
        ],
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    datetime = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
        required=False,
    )
    prep_detail = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": "2"}),
        required=False,
    )
    prep_img = forms.ImageField(
        widget=forms.FileInput(
            attrs={"class": "custom-file-input img-file-controls", "data-img-id": "prepImgId"}
        ),
        required=False,
    )
    app_type = forms.ChoiceField(
        choices=[
            ("webex", "Cisco Webex"),
            ("zoom", "Zoom"),
            ("google-meet", "Google Meet"),
            ("other", "โปรแกรมอื่น (กรุณาระบุในรายละเอียด)"),
        ],
        widget=forms.RadioSelect,
        required=False,
    )
    interview_detail = forms.CharField(
        label="รายละเอียด",
        help_text="ป้อนลายละเอียด เช่น ลิงก์สำหรับสัมภาษณ์ รหัสผ่าน",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": "3"}),
        required=False,
    )
    interview_img = forms.ImageField(
        label="รูปประกอบ",
        help_text="รูปจะปรากฏด้านขวาของข้อความ",
        widget=forms.FileInput(
            attrs={"class": "custom-file-input img-file-controls", "data-img-id": "descImgId"}
        ),
        required=False,
    )

    # TODO: connect to the model once model is ready
    # class Meta:
    #     model = Interview
    #     fields = ['interviewType', 'additionalDoc', 'datetime', 'prep_detail', 'prep_img', 'app_type']

    # InterviewFormInlineFormSet = inlineformset_factory(Interview, ContactPerson, form=ContactPersonForm, extra=1,
    #                                                    can_delete=True)


class InterviewDescriptionForm(forms.ModelForm):
    project_majors = forms.MultipleChoiceField(choices=(), widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = InterviewDescription
        fields = [
            "admission_round",
            "admission_project",
            "faculty",
            "interview_options",
            "interview_date",
            "is_additional_documents_required",
            "preparation_descriptions",
            "preparation_image",
            "descriptions",
            "description_image",
            "contacts",
        ]

    def save(self, commit=True):
        interview_description = super(InterviewDescriptionForm, self).save(commit=commit)

        with transaction.atomic():
            for project_major in self.project_majors:
                admission_project_id, major_cupt_code_id = project_major.split("_")[0:2]
                interview_relation = AdmissionProjectMajorCuptCodeInterviewDescription(
                    admission_project_id=admission_project_id,
                    major_cupt_code_id=major_cupt_code_id,
                    interview_description=interview_description,
                )
                interview_relation.save()

        return interview_description
