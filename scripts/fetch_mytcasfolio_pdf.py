from django_bootstrap import bootstrap
bootstrap()

import sys

from appl.models import UploadedDocument

def main():
    base_path = sys.argv[1]
    base_url = sys.argv[2]

    documents = UploadedDocument.objects.filter(document_url__contains='mytcas.com').all()

    for d in documents:
        if d.local_document_url != '':
            continue

        document_url = d.document_url
        if not document_url.startswith('https://folio.mytcas.com/'):
            print('ERROR: wrong url:', d.applicant, document_url)

        print(d.applicant, d.document_url)        

if __name__ == '__main__':
    main()
    
