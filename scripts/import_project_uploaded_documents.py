from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
import io

from appl.models import ProjectUploadedDocument, AdmissionProject

FIELD_MAP = [
    (1, 'rank'),
    (2, 'title'),
    (3, 'document_key'),
    (4, 'descriptions'),
    (5, 'specifications'),
    (6, 'notes'),
    (7, 'allowed_extentions'),
    (8, 'file_prefix'),
]

def main():
    filename = sys.argv[1]
    counter = 0
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        lines = [l for l in reader]

        for items in lines[1:]:
            if items[0].strip() == '':
                continue
            document_key = items[3]

            old_documents = ProjectUploadedDocument.objects.filter(document_key=document_key).all()
            if old_documents:
                document = old_documents[0]
            else:
                document = ProjectUploadedDocument()

            for idx, f in FIELD_MAP:
                setattr(document, f, items[idx])

            document.size_limit = int(items[9])
            document.is_url_document = (items[10].strip() == '1')
            document.is_required = (items[11].strip() == '1')
            document.is_detail_required = (items[12].strip() == '1')
            document.can_have_multiple_files = (items[13].strip() == '1')
        
            document.save()

            project_ids = items[0].strip().split(',')
            for p in project_ids:
                project = AdmissionProject.objects.get(pk=p)
                document.admission_projects.add(project)
            
            counter += 1

    print('Imported',counter,'project documents')
        

if __name__ == '__main__':
    main()
    
