DIGIT_READINGS = {
    '0':'ศูนย์',
    '1':'หนึ่ง',
    '2':'สอง',
    '3':'สาม',
    '4':'สี่',
    '5':'ห้า',
    '6':'หก',
    '7':'เจ็ด',
    '8':'แปด',
    '9':'เก้า',
}
ALPHA_READINGS = {
    'a':'เอ',
    'b':'บี',
    'c':'ซี',
    'd':'ดี',
    'e':'อี',
    'f':'เอฟ',
    'g':'จี',
    'h':'เอช',
    'i':'ไอ',
    'j':'เจ',
    'k':'เค',
    'l':'แอล',
    'm':'เอ็ม',
    'n':'เอ็น',
    'o':'โอ',
    'p':'พี',
    'q':'คิว',
    'r':'อาร์',
    's':'เอส',
    't':'ที',
    'u':'ยู',
    'v':'วี',
    'w':'ดับเบิลยู',
    'x':'เอ็กซ์',
    'y':'วาย',
    'z':'แซด',
}

def read_clearing_code(code):
    """
    >>> read_clearing_code('1234567890')
    'หนึ่ง-สอง-สาม-สี่-ห้า-หก-เจ็ด-แปด-เก้า-ศูนย์'
    >>> read_clearing_code('aBcDeFgHiJk')
    'เอเล็ก-บีใหญ่-ซีเล็ก-ดีใหญ่-อีเล็ก-เอฟใหญ่-จีเล็ก-เอชใหญ่-ไอเล็ก-เจใหญ่-เคเล็ก'
    >>> read_clearing_code('LmNoPqRsTuV')
    'แอลใหญ่-เอ็มเล็ก-เอ็นใหญ่-โอเล็ก-พีใหญ่-คิวเล็ก-อาร์ใหญ่-เอสเล็ก-ทีใหญ่-ยูเล็ก-วีใหญ่'
    >>> read_clearing_code('wXyZ')
    'ดับเบิลยูเล็ก-เอ็กซ์ใหญ่-วายเล็ก-แซดใหญ่'
    """
    items = []
    for a in code:
        if a in DIGIT_READINGS:
            items.append(DIGIT_READINGS[a])
        elif a in ALPHA_READINGS:
            items.append(ALPHA_READINGS[a]+'เล็ก')
        else:
            c = a.lower()
            if c in ALPHA_READINGS:
                items.append(ALPHA_READINGS[c]+'ใหญ่')
            else:
                items.append('?')
    return '-'.join(items)

            
