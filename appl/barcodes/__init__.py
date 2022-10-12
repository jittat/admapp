import os.path
import types

import barcode
from PIL import ImageFont
from barcode.writer import ImageWriter

PATH = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(PATH, 'fonts', 'DejaVuSansMono.ttf')

def mm2px(mm, dpi=300):
    return (mm * dpi) / 25.4

def paint_text(self, xpos, ypos):
    font = ImageFont.truetype(FONT, self.font_size * 3)
    updated_text = self.text.replace('\x0d',' ')
    width, height = font.getsize(updated_text)
    pos = (mm2px(xpos, self.dpi) - width // 2,
           mm2px(ypos, self.dpi) - height )
    self._draw.text(pos, updated_text, font=font, fill=self.foreground)


def generate(tax_id, nat_id, verification_code, amount, filename):
    amount = str(int(amount)) + '00'
    writer = ImageWriter()
    writer.hello = types.MethodType(paint_text, writer)
    writer.register_callback('paint_text', writer.hello)
    barcode_str = ('|' + tax_id + '\x0d' +
                   nat_id + '\x0d' +
                   verification_code + '\x0d'
                   + amount)
    c = barcode.get('code128', barcode_str, writer)
    c.save(filename)
