from django_bootstrap import bootstrap
bootstrap()

import json
import sys

from backoffice.models import MajorSlotStat

def main():
    year = sys.argv[1]
    json_filename = sys.argv[2]

    json_data = json.load(open(json_filename))

    count = 0

    for m in json_data['majors']:
        full_code = m['full_code']
        old_slot_stats = MajorSlotStat.objects.filter(year=year, full_code=full_code)
        if len(old_slot_stats) > 0:
            slot_stat = old_slot_stats[0]
        else:
            slot_stat = MajorSlotStat(year=year, full_code=full_code)

        slot_stat.json_data = json.dumps(m)
        slot_stat.save()

        count += 1

    print("Imported {} major slot stats for year {}".format(count, year))

if __name__ == '__main__':
    main()
