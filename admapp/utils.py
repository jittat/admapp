def number_to_thai_text(num):
    """
    >>> number_to_thai_text(1)
    'หนึ่ง'
    >>> number_to_thai_text(10)
    'สิบ'
    >>> number_to_thai_text(11)
    'สิบเอ็ด'
    >>> number_to_thai_text(14073)
    'หนึ่งหมื่นสี่พันเจ็ดสิบสาม'
    >>> number_to_thai_text(98765)
    'เก้าหมื่นแปดพันเจ็ดร้อยหกสิบห้า'
    >>> number_to_thai_text(43521)
    'สี่หมื่นสามพันห้าร้อยยี่สิบเอ็ด'
    """
    digit_ends = ['','เอ็ด','สอง','สาม','สี่','ห้า','หก','เจ็ด','แปด','เก้า']
    digit_ten = ['','','ยี่','สาม','สี่','ห้า','หก','เจ็ด','แปด','เก้า']
    digits = ['ศูนย์','หนึ่ง','สอง','สาม','สี่','ห้า','หก','เจ็ด','แปด','เก้า']
    
    
    if num < 10:
        return digits[num]
    if num < 100:
        return digit_ten[num // 10] + 'สิบ' + digit_ends[num % 10]

    items = []
    base = 10000
    level_map = { 10000: 'หมื่น',
                  1000: 'พัน',
                  100: 'ร้อย'}

    while base >= 100:
        if num >= base:
            items.append(digits[num // base] + level_map[base])
            num %= base
        base //= 10

    if num > 0:
        items.append(number_to_thai_text(num))

    return ''.join(items)

    
