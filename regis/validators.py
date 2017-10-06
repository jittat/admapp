def is_valid_national_id(national_id):
    if len(national_id) != 13:
        return False

    mul = 13
    total = 0
    for c in national_id[:-1]:
        if c > '9' or c < '0':
            return False
        total += mul * int(c)
        mul -= 1
    r1 = total % 11
    checkdigit = (11 - r1) % 10

    return national_id[-1] == str(checkdigit)
    
def is_valid_passport_number(passport_number):
    for c in passport_number:
        if c == ' ':
            return False
        elif c >= '0' and c <= '9':
            continue
        elif (c >= 'A' and c <= 'Z') or (c >= 'a' and c <= 'z'):
            continue
        else:
            return False

    return True