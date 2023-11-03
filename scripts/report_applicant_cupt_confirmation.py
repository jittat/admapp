from django_bootstrap import bootstrap
bootstrap()

from regis.models import Applicant, CuptConfirmation, CuptRequestQueueItem

def main():
    print('Applicants: ', Applicant.objects.count())
    print('Queue: ', CuptRequestQueueItem.objects.count())

    counters = {}
    for a in Applicant.objects.prefetch_related('cupt_confirmation').all():
        if a.has_cupt_confirmation_result():
            code = a.cupt_confirmation.api_result_code
        else:
            code = -1
        if code not in counters:
            counters[code] = 0
        counters[code] += 1
    print(counters)

if __name__ == '__main__':
    main()
