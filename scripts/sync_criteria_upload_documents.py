"""Syncs criteria upload fields into ProjectUploadedDocument slots for every
project in an admission round.

usage: python sync_criteria_upload_documents.py <admission_round_id>
"""
from django_bootstrap import bootstrap
bootstrap()
import sys

from appl.models import AdmissionRound, AdmissionProjectRound
from criteria.upload_documents import sync_criteria_upload_documents


def main():
    admission_round = AdmissionRound.objects.get(pk=sys.argv[1])

    project_rounds = (AdmissionProjectRound.objects
                      .filter(admission_round=admission_round)
                      .select_related('admission_project'))
    for project_round in project_rounds:
        admission_project = project_round.admission_project
        summary = sync_criteria_upload_documents(admission_project)
        if (summary.created or summary.updated or summary.deleted or summary.unlinked or
                summary.duplicate_keys or summary.fields_without_majors):
            print(admission_project.id, admission_project, '-', summary.as_notice())


if __name__ == '__main__':
    main()
