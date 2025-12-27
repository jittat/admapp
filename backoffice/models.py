# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from appl.models import AdmissionProject, AdmissionRound, ProjectApplication
from appl.models import Campus, Faculty
from appl.models import Major, AdmissionResult, ExamScore
from criteria.models import MajorCuptCode
from regis.models import Applicant

from .ui_models import ProjectMenuConfig

class Profile(models.Model):
    ANY_MAJOR = 0

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    faculty = models.ForeignKey(
        Faculty,
        verbose_name="คณะที่สังกัด",
        default=None,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    is_campus_admin = models.BooleanField(verbose_name="ดูแลข้อมูลในวิทยาเขต", default=False)
    campus = models.ForeignKey(
        Campus,
        verbose_name="วิทยาเขต",
        default=None,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    is_admission_admin = models.BooleanField(verbose_name="ดูแลข้อมูลทุกคณะ", default=False)

    admission_projects = models.ManyToManyField(AdmissionProject, blank=True)

    is_number_adjustment_admin = models.BooleanField(verbose_name="สำหรับปรับจำนวน", default=False)
    major_number = models.IntegerField(
        default=ANY_MAJOR, verbose_name="หมายเลขสาขา (กรณีที่ดูแลโครงการเดียว)"
    )
    adjustment_major_number = models.CharField(max_length=20, blank=True)

    has_criteria_check_permission = models.BooleanField(verbose_name="สามารถตรวจสอบเกณฑ์พื้นฐานได้พิเศษ", 
                                                        default=False)

    def __str__(self):
        if self.faculty:
            return self.user.get_full_name() + " (" + str(self.faculty) + ")"
        elif self.is_admission_admin:
            return self.user.get_full_name() + " (ADMADMIN)"
        else:
            return self.user.get_full_name()

    @staticmethod
    def get_profile_for(user):
        try:
            return user.profile
        except:
            return None


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)


class CheckMarkGroup(models.Model):
    NUM_CHECK_MARKS = 6

    COLORS = [
        "text-primary",
        "text-success",
        "text-warning",
        "text-danger",
        "text-secondary",
        "text-dark",
    ]

    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE)
    project_application = models.OneToOneField(
        ProjectApplication, related_name="check_mark_group", on_delete=models.CASCADE
    )
    check_marks = models.CharField(default="", max_length=20)

    # This is for global criteria check.  
    # We keep them here because CheckMarkGroup is created for each project application
    # and is shared by all selected majors of the applicant.
    is_multimajor_criteria_passed = models.BooleanField(default=None,
                                                        null=True)
    updated_multimajor_criteria_passed_at = models.DateTimeField(null=True)

    def is_checked(self, num):
        if len(self.check_marks) >= num:
            return self.check_marks[num - 1] == "1"

    def init_marks(self):
        self.check_marks = "".join(["0" for i in range(self.NUM_CHECK_MARKS)])

    def set_check(self, num):
        self.check_marks = self.check_marks[: (num - 1)] + "1" + self.check_marks[num:]

    def set_uncheck(self, num):
        self.check_marks = self.check_marks[: (num - 1)] + "0" + self.check_marks[num:]

    def get_check_mark_list(self):
        marks = []
        for i in range(self.NUM_CHECK_MARKS):
            marks.append(
                {
                    "number": i + 1,
                    "is_checked": self.is_checked(i + 1),
                    "text_color": self.COLORS[i],
                }
            )
        return marks

    def __str__(self):
        return "{0} - {1}".format(self.applicant.national_id, self.check_marks)


class JudgeComment(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE)
    project_application = models.ForeignKey(
        ProjectApplication, related_name="judge_comment_set", on_delete=models.CASCADE
    )

    author_username = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    body = models.TextField()

    is_deleted = models.BooleanField(default=False)
    is_shared_in_major = models.BooleanField(default=False)

    admission_project = models.ForeignKey(
        AdmissionProject, blank=True, null=True, default=None, on_delete=models.SET_NULL
    )
    admission_round = models.ForeignKey(
        AdmissionRound, blank=True, null=True, default=None, on_delete=models.SET_NULL
    )
    major = models.ForeignKey(Major, blank=True, null=True, default=None, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["-created_at"]

    def report_display(self):
        if self.author_username:
            return self.body + " - " + self.author_username
        else:
            return self.body


class MajorInterviewCallDecision(models.Model):
    FLOAT_DELTA = 0.000001

    admission_project = models.ForeignKey(AdmissionProject, on_delete=models.CASCADE)
    admission_round = models.ForeignKey(AdmissionRound, on_delete=models.CASCADE)
    major = models.ForeignKey(Major, on_delete=models.CASCADE)

    interview_call_count = models.IntegerField(default=0)
    interview_call_min_score = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["major", "admission_round"]),
            models.Index(fields=["admission_round", "admission_project"]),
        ]
        unique_together = (("major", "admission_round"),)

    @staticmethod
    def get_for(major, admission_round):
        decisions = MajorInterviewCallDecision.objects.filter(
            major=major, admission_round=admission_round
        ).all()
        if len(decisions) > 0:
            return decisions[0]
        else:
            return None


class ApplicantMajorResult(models.Model):
    admission_project = models.ForeignKey(AdmissionProject, on_delete=models.CASCADE)
    major = models.ForeignKey(Major, on_delete=models.CASCADE)
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE)
    project_application = models.ForeignKey(
        ProjectApplication, null=True, on_delete=models.SET_NULL
    )
    admission_result = models.ForeignKey(AdmissionResult, null=True, on_delete=models.SET_NULL)
    other_major_numbers = models.CharField(max_length=30, blank="", default="")
    other_major_scores = models.CharField(max_length=50, blank="", default="")

    class Meta:
        indexes = [
            models.Index(fields=["major", "admission_project"]),
            models.Index(fields=["applicant"]),
            models.Index(fields=["admission_project", "applicant"]),
            models.Index(fields=["major", "admission_project", "applicant"]),
        ]
        unique_together = (("major", "admission_project", "applicant"),)

    def get_other_major_numbers(self):
        if self.other_major_numbers == "":
            return []
        return [int(x) for x in self.other_major_numbers.split(",")]

    def get_other_major_scores(self):
        if self.other_major_scores == "":
            return []
        return [float(x) for x in self.other_major_scores.split(",")]


class ApplicantMajorScore(models.Model):
    admission_project = models.ForeignKey(AdmissionProject, on_delete=models.CASCADE)
    major = models.ForeignKey(Major, on_delete=models.CASCADE)
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE)

    exam_score = models.ForeignKey(ExamScore, on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=["major", "admission_project"]),
            models.Index(fields=["applicant"]),
            models.Index(fields=["major", "admission_project", "applicant"]),
        ]


class AdjustmentMajor(models.Model):
    full_code = models.CharField(max_length=20, unique=True)

    major_code = models.CharField(max_length=20)
    study_type_code = models.CharField(max_length=3)

    title = models.CharField(max_length=200)

    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class AdjustmentMajorSlot(models.Model):
    adjustment_major = models.ForeignKey(
        AdjustmentMajor, on_delete=models.CASCADE, related_name="slots"
    )
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    admission_round = models.ForeignKey(AdmissionRound, on_delete=models.CASCADE)

    admission_round_number = models.IntegerField()

    major_full_code = models.CharField(max_length=20)
    cupt_code = models.CharField(max_length=30, blank=True)

    admission_project_title = models.CharField(max_length=200)

    original_slots = models.IntegerField()
    current_slots = models.IntegerField()

    is_frozen = models.BooleanField(default=False)
    is_confirmed_by_faculty = models.BooleanField(default=False)

    confirmed_slots = models.IntegerField(default=0)
    confirmed_canceled_slots = models.IntegerField(default=0)
    is_final = models.BooleanField(default=False)

    class Meta:
        ordering = ["admission_round_number", "cupt_code"]

    def __str__(self):
        return "%s (%s) (%d) %s" % (
            self.adjustment_major,
            self.admission_project_title,
            self.current_slots,
            self.cupt_code,
        )

    def project_code(self):
        return self.cupt_code[:3]

    def project_full_code(self):
        return self.cupt_code[:5]

    def is_editable(self):
        return (not self.is_frozen) and (not self.is_final) and (not self.is_confirmed_by_faculty)

    def is_adjusted(self):
        return self.original_slots != self.current_slots

    def latest_confirmed_slots(self):
        return self.confirmed_slots - self.confirmed_canceled_slots

    def additional_project_message(self):
        if self.cupt_code[:3] != 'C28':
            return ''
        else:
            if self.cupt_code[:5] == 'C2800':
                return ''
            msg = self.admission_project_title
            cutwords = ['ใช้คะแนน', 'รับนักเรียน']
            for w in cutwords:
                if w in msg:
                    idx = msg.find(w)
                    return '(' + msg[idx:]
            return msg
    
    @staticmethod
    def get_adjusted_slots():
        return [
            slot
            for slot in AdjustmentMajorSlot.objects.all()
            if slot.original_slots != slot.current_slots
        ]


def interview_preparation_image_path(instance, filename):
    return "documents/interview_description_{0}/preparation/{1}".format(instance.id, filename)


def interview_description_image_path(instance, filename):
    return "documents/interview_description_{0}/description/{1}".format(instance.id, filename)


class InterviewDescription(models.Model):
    OPTION_NO_INTERVIEW = 0
    OPTION_ONLINE_INTERVIEW = 1
    OPTION_OFFLINE_INTERVIEW = 2

    OPTION_DOC_NO_NEW_DOC = 0
    OPTION_DOC_UPLOAD_ON_ADMAPP = 1
    OPTION_DOC_UPLOAD_OTHER = 2

    OPTION_SPAN_NO_SPAN = 0
    OPTION_SPAN_SAME_PROJECT = 1
    OPTION_SPAN_SAME_CUPT_CODE = 2
    OPTION_SPAN_INDIVIDUAL = 3
    
    admission_round = models.ForeignKey(AdmissionRound,
                                        on_delete=models.CASCADE)

    admission_project = models.ForeignKey(AdmissionProject,
                                          on_delete=models.CASCADE,
                                          blank=True,
                                          null=True)
    major = models.ForeignKey(Major,
                              on_delete=models.CASCADE,
                              blank=True,
                              null=True)

    span_option = models.IntegerField(verbose_name='การเชื่อมโยงรายละเอียดการสัมภาษณ์',
                                      default=OPTION_SPAN_NO_SPAN,
                                      choices=[
                                          (OPTION_SPAN_NO_SPAN, 'ไม่มีการเชื่อมโยงไปยังสาขาหรือโครงการอื่น'),
                                          (OPTION_SPAN_SAME_PROJECT, 'เชื่อมโยงทุกสาขาในโครงการนี้'),
                                          (OPTION_SPAN_SAME_CUPT_CODE, 'เชื่อมโยงทุกโครงการของสาขานี้'),
                                          (OPTION_SPAN_INDIVIDUAL, 'เชื่อมโยงโดยระบุโครงการ-สาขา'),
                                      ])
    
    faculty = models.ForeignKey(Faculty,
                                on_delete=models.CASCADE)

    interview_options = models.IntegerField(
        verbose_name="ทางเลือกการสัมภาษณ์",
        choices=[
            (OPTION_NO_INTERVIEW, "ไม่มีการสัมภาษณ์"),
            (OPTION_ONLINE_INTERVIEW, "สัมภาษณ์ออนไลน์"),
            (OPTION_OFFLINE_INTERVIEW, "สัมภาษณ์ที่สถานที่"),
        ],
    )

    video_conference_platform = models.TextField(
        blank=True, verbose_name="ช่องทางการสัมภาษณ์ออนไลน์",
        choices=[
            ("webex", "Cisco Webex"),
            ("zoom", "Zoom"),
            ("google-meet", "Google Meet"),
            ("other", "โปรแกรมอื่น (กรุณาระบุในรายละเอียด)"),
            ("", "ไม่ระบุ"),
        ]
    )

    interview_date = models.DateTimeField(
        verbose_name="วันและเวลาการสัมภาษณ์", blank=True, null=True
    )

    additional_documents_option = models.IntegerField(
        verbose_name="การส่งเอกสารเพิ่มเติม",
        default=OPTION_DOC_NO_NEW_DOC,
        choices=[
            (
                OPTION_DOC_NO_NEW_DOC,
                "ไม่มี"
            ),
            (
                OPTION_DOC_UPLOAD_ON_ADMAPP,
                "ต้องส่งเอกสารหรือส่งลิงก์เพิ่มเติม (อัพโหลดในระบบ, กรุณาแจ้งรายละเอียดในการเตรียมตัว)",
            ),
            (
                OPTION_DOC_UPLOAD_OTHER,
                "ต้องส่งเอกสารหรือส่งลิงก์เพิ่มเติม (ส่งช่องทางอื่น, กรุณาแจ้งในรายละเอียดในการเตรียมตัว)",
            ),
        ],
    )

    preparation_descriptions = models.TextField(blank=True, verbose_name="รายละเอียดการเตรียมตัว")
    preparation_image = models.FileField(
        upload_to=interview_preparation_image_path, blank=True, verbose_name="รูปประกอบการเตรียมตัว")

    descriptions = models.TextField(blank=True, verbose_name="รายละเอียดการสัมภาษณ์")
    description_image = models.FileField(
        upload_to=interview_description_image_path, blank=True, verbose_name="รูปประกอบการสัมภาษณ์")

    contacts = models.JSONField(blank=True, default=list, verbose_name="ข้อมูลการติดต่อ")

    def get_additional_documents_option_user_display(self):
        mesgs = {
            InterviewDescription.OPTION_DOC_NO_NEW_DOC: 'ไม่มีเอกสารต้องอัพโหลดเพิ่มเติม',
            InterviewDescription.OPTION_DOC_UPLOAD_ON_ADMAPP: 'ต้องอัพโหลดเอกสารเพิ่มเติม โดยอัพโหลดในระบบ อ่านรายละเอียดในส่วนการเตรียมตัว',
            InterviewDescription.OPTION_DOC_UPLOAD_OTHER: 'ต้องส่งเอกสารเพิ่มเติม โดยส่งทางช่องทางที่ระบุในรายละเอียดส่วนการเตรียมตัว',
        }
        if self.additional_documents_option in mesgs:
            return mesgs[self.additional_documents_option]
        else:
            return ''

    @staticmethod
    def get_interview_description_id_hash(id):
        return (id * 683789 + 963046) % 1001933

class AdmissionProjectMajorCuptCodeInterviewDescription(models.Model):
    admission_project = models.ForeignKey(AdmissionProject,
                                          on_delete=models.CASCADE,
                                          db_constraint=False)

    major_cupt_code = models.ForeignKey(MajorCuptCode,
                                        on_delete=models.CASCADE,
                                        db_constraint=False)

    interview_description = models.ForeignKey(InterviewDescription,
                                              on_delete=models.CASCADE,
                                              related_name="admission_prject_major_cupt_code")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["admission_project", "major_cupt_code"],
                name="unique_admission_project_major_cupt_code",
            )
        ]

    
class APIToken(models.Model):
    token = models.CharField(max_length=64,
                             unique=True)
    description = models.CharField(max_length=200,
                                   blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.description