def is_blank(next):
    return next in ' \t\n'

def is_notBlank(next):
    return not is_blank(next)

def is_binary(next):
    return next in '01'

def is_octal(next):
    return is_binary(next) or next in '234567'

def is_decimal(next):
    return is_octal(next) or next in '89'

def is_hexadecimal(next):
    return is_decimal(next) or next in 'abcdefABCDEF'

ENGLISH_LOWER = 'abcdefghijklmnopqrstuvwxyz'
ENGLISH_UPPER = ENGLISH_LOWER.upper()
ENGLISH = ENGLISH_LOWER + ENGLISH_UPPER

def is_nameStart(next):
    return next == '_' or next in ENGLISH

def is_nameInner(next):
    return is_nameStart(next) or is_decimal(next)
