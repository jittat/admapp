import qrcode
from qrcode.image.pure import PymagingImage
from PyCRC.CRCCCITT import CRCCCITT
from PIL import Image

from django.conf import settings
from django.contrib.staticfiles import finders

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
    
