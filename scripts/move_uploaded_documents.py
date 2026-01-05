from django_bootstrap import bootstrap
from django.conf import settings

bootstrap()

import sys
import glob
import os

def main():
    doc_type = int(sys.argv[1])
    target = sys.argv[2]

    pattern = os.path.join(settings.MEDIA_ROOT, f"documents/applicant_*/doc_{doc_type}")

    counter = 0
    for dname in glob.glob(pattern):
        items = dname.split("/")
        applicant_dir = items[-2]
        # move file dname to os.path.join(target, applicant_dir))
        target_dir = os.path.join(target, applicant_dir)
        os.makedirs(target_dir, exist_ok=True)
        # print(f"Moving {dname} to {target_dir}")
        os.rename(dname, os.path.join(target_dir, f'doc_{doc_type}'))

        counter += 1
        if counter % 1000 == 0:
            print(f"Moved {counter} dirs")

    print(f"Finished moving dirs. Total moved: {counter}")

if __name__ == "__main__":
    main()