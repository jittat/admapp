def is_valid_national_id(national_id):
    if len(national_id) != 13:
        return False
    mul = 13
    total = 0
    for c in national_id[:-1]:
        if not '0' <= c <= '9':
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
        elif '0' <= c <= '9':
            continue
        elif 'A' <= c <= 'Z' or 'a' <= c <= 'z':
            continue
        else:
            return False
    return True
