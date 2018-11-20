import qrcode
from qrcode.image.pure import PymagingImage

def generate_qr(ref1, ref2, additional_payment, filename):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
        image_factory=PymagingImage,
    )
    qr.add_data('5798743597435987435987439574397594385'+ref1+ref2)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(open(filename + '.png','wb'))
