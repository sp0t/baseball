import math

def decimalToAmerian(dec):
    american = 0
    if dec >= 2:
       american = (dec - 1) * 100
    elif dec < 2:
       american = -100 / (dec - 1)

    if american >= 0:
        return math.floor(american + 0.5)
    else:
        return math.ceil(american - 0.5)

def americanToDecimal(american):
    dec = 0
    if american > 0:
       dec = (american / 100) + 1
    elif american < 0:
       dec = (100 / abs(american)) + 1

    return round(dec, 2)
