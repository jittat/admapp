from django.db import models

from appl.models import Payment


class QRConfirmation(models.Model):
    bill_payment_ref1 = models.CharField(max_length=30,
                                         blank=True)
    bill_payment_ref2 = models.CharField(max_length=30,
                                         blank=True)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    remote_addr = models.CharField(max_length=50)

    status = models.IntegerField(choices=((0,'Success'),
                                          (500,'Error')),
                                 default=0)

    payment = models.ForeignKey(Payment,
                                default=None,
                                null=True,
                                on_delete=models.SET_NULL)
    
    def __str__(self):
        if self.bill_payment_ref1:
            return '%s (%s)' % (self.bill_payment_ref1, str(self.created_at))
        else:
            return 'Confirmation (%s)' % str(self.created_at)


