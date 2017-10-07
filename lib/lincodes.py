BASE_MAT = [[ 9, 10, 4,  5,  0,  5,  8,  7,  8,
              5,  7,  7,  5,  7,  4,  8, 10,
              8,  2,  9,  7,  6, 10,  7],
            [ 4,  8, 10,  4,  0,  3,  6,  9,  7,
              8,  0,  4,  5,  8, 10,  8,  1,
              1,  2,  1,  2,  7,  7,  1],
            [ 1,  9,  0,  7,  1,  7,  4, 10,  7,
              5,  3,  5,  7,  6,  7,  9,  4,
              0,  2,  2,  2,  8,  8,  8],
            [ 2,  4,  7,  6,  3,  4,  5,  1,  1,
              0,  1,  9,  4,  8,  7,  5,  0,
              0,  2,  1, 10,  7,  9,  9],
            [ 8,  3,  2,  7,  4,  2,  5,  5,  4,
              4,  6,  7, 10,  1,  0,  6,  5,
              6,  3,  9,  5,  0,  1,  8],
            [ 1,  6,  0,  2,  7,  5,  7,  0, 10,
              9,  7,  8,  2,  5,  9,  2,  1,
              3,  4,  8,  0,  6,  7,  2]]
BASE_LENGTH = 24
NUM_MOD = 11

def mul_with_base(a):
    results = []
    for r in range(len(BASE_MAT)):
        s = sum([a[i] * BASE_MAT[r][i] for i in range(BASE_LENGTH)])
        s %= 11
        s %= 10
        results.append(s)
    return results

def check_digit(str):
    coeffs = [13, 12, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 5, 4, 3, 2, 1]
    s = sum([coeffs[i] * int(str[i]) for i in range(17)])
    s %= 11
    return (11 - s) % 10
    
def gen_verification(national_id, applicant_id, deadline_str):
    """
    >>> gen_verification("1234567890121","999000","71031")
    '999000703600710317'
    >>> gen_verification("1234567890121","998000","71031")
    '998000035159710310'
    >>> gen_verification("1324567890121","999000","71031")
    '999000291316710311'
    """

    vect = []
    for i in range(13):
        if i < len(national_id):
            vect.append(int(national_id[i]))
        else:
            vect.append(0)
    for i in range(6):
        vect.append(int(applicant_id[i]))
    for i in range(5):
        vect.append(int(deadline_str[i]))

    results = mul_with_base(vect)

    v = []
    for i in range(6):
        v.append(applicant_id[i])
    for i in range(6):
        v.append(str(results[i]))
    for i in range(5):
        v.append(deadline_str[i])

    vnum = ''.join(v)
    return vnum + str(check_digit(vnum))
