from django_bootstrap import bootstrap
bootstrap()

import sys
import os.path
import os
from datetime import datetime

from appl.models import UploadedDocument

def main():
    last_id_filename = sys.argv[1]

    timestamp = str(int(datetime.now().timestamp()))

    SRC_BASE_DIR = ''
    DEST_BASE_DIR = '/home/jittat/prog/django/admapp/bbmm/'
    DEST_DIR = DEST_BASE_DIR + timestamp
    os.makedirs(DEST_DIR)

    start_id = int(open(last_id_filename).readline())

    last_id = start_id
    count = 0
    for d in UploadedDocument.objects.filter(id__gt=start_id):
        full_filename = d.uploaded_file.name
        if full_filename == '':
            continue
        
        print(d.id, full_filename, os.path.dirname(full_filename))

        dir = DEST_DIR + '/' + os.path.dirname(full_filename)
        os.makedirs(dir, exist_ok=True)

        if d.id > last_id:
            last_id = d.id

    if last_id == start_id:
        return

    with open(last_id_filename,'w') as f:
        print(last_id, file=f)
    
    tar_cmd = f'tar -zcvf {DEST_BASE_DIR}{timestamp}.tgz {DEST_BASE_DIR}{timestamp}'
    os.system(tar_cmd)

if __name__=='__main__':
    main()
