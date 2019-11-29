import qrcode
from qrcode.image.pure import PymagingImage
from PyCRC.CRCCCITT import CRCCCITT
from PIL import Image

from django.conf import settings
from django.contrib.staticfiles import finders

from suds import Client

def len2(st):
    return ('%02d' % len(st))

def generate_qr_code(ref1, ref2, amount):
    QR_CONFIG = settings.QR_CONFIG

    if ref2=='':
        ref2 = QR_CONFIG['REF2']
    
    merchant_subtags = [
        QR_CONFIG['AID'],
        QR_CONFIG['BILLER_ID'],
        '02' + len2(ref1) + ref1,
        '03' + len2(ref2) + ref2
    ]
    merchant_subtag_combined = ''.join(merchant_subtags)
    amount_str = '%.2f' % amount
    amount_tag = '54' + len2(amount_str) + amount_str
    tags = [
        QR_CONFIG['START'],
        '30' + len2(merchant_subtag_combined) + merchant_subtag_combined,
        QR_CONFIG['CURRENCY_CODE'],
        amount_tag,
        QR_CONFIG['COUNTRY_CODE'],
        QR_CONFIG['CRC_PREFIX']
    ]
    raw_code = ''.join(tags)
    #print(raw_code)
    crc = CRCCCITT(version='FFFF').calculate(raw_code)
    #print(crc)
    return raw_code + ('%04X' % crc)
    
def generate_qr(ref1, ref2, additional_payment, filename):
    code = generate_qr_code(ref1, ref2, additional_payment)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=3,
        image_factory=PymagingImage,
    )
    qr.add_data(code)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(open(filename + '-base.png','wb'))

    qr_in = Image.open(filename + '-base.png')

    logo_filename = finders.find('appl/payment/img/QR_Logo-03.png')
    logo = Image.open(logo_filename).resize((80,60))
    qr_in.paste(logo, box=(qr_in.width // 2 - 40, qr_in.height // 2 - 30), mask=logo)

    qr_in.save(filename + '.png')
    

def generate_ku_qr(applicant, application, additional_payment, filename):
    KU_QR_SERVICE_URL = settings.KU_QR_SERVICE_URL
    KU_QR_CALLBACK_URL = settings.KU_QR_CALLBACK_URL

    additional_payment = 1

    amount = "{:08.2f}".format(additional_payment)

    admission_project = application.admission_project
    project_round = admission_project.get_project_round_for(application.admission_round)
    deadline = project_round.payment_deadline
    deadline_str = "%02d%02d%02d" % (deadline.day,
                                     deadline.month,
                                     deadline.year % 100)
    
    ref1 = str(application.admission_round.number) + '000' + applicant.national_id
    ref2 = "{:06d}".format(application.get_number())
    
    client = Client(KU_QR_SERVICE_URL)

    callback_url = KU_QR_CALLBACK_URL % (ref2,)
    
    result = client.service.getOeaQr(expireDate=deadline_str,
                                     appCode='01',
                                     transactionId=ref2,
                                     amount=amount,
                                     ref1Prefix=ref1,
                                     ref2Prefix=ref2,
                                     billerSuffix='87',
                                     callbackUrl=callback_url)

    if result.success:
        img_base64 = result.qrResult.content[23:]

        import base64
        from PIL import Image
        from io import BytesIO

        im = Image.open(BytesIO(base64.b64decode(img_base64)))
        im = im.resize((390,390))
        im.save(filename + '.png', 'PNG')
    else:
        print(result)

    
