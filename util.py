import sys
import binascii
import re

def bytes_to_uint32_le(bytes):
    return  (int(bytes[3], 16) << 24) | (int(bytes[2], 16) << 16) | (int(bytes[1], 16) <<  8) | (int(bytes[0], 16) <<  0)

def uint32_to_bytes_le(uint32):
    return [(uint32 >> 0)  & 0xff, 
            (uint32 >> 8)  & 0xff, 
            (uint32 >> 16) & 0xff, 
            (uint32 >> 24) & 0xff]

def uint16_to_bytes_le(value):
    return [(value >> 0 & 0xFF),
            (value >> 8 & 0xFF)]

def zero_pad_array_le(data, padsize):
    for i in range(0, padsize):
        data.insert(0, 0)

def crc32_unsigned(bytestring):
    return binascii.crc32(bytestring) % (1 << 32)

def mac_string_to_uint(mac):
    parts = list(re.match('(..):(..):(..):(..):(..):(..)', mac).groups())
    ints = list(map(lambda x: int(x, 16), parts))

    res = 0
    for i in range(0, len(ints)):
        res += (ints[len(ints)-1 - i] << 8*i)

    return res

def uint_to_mac_string(mac):
    ints = [0, 0, 0, 0, 0, 0]
    for i in range(0, len(ints)):
        ints[len(ints)-1 - i] = (mac >> 8*i) & 0xff

    return ':'.join(map(lambda x: '{:02x}'.format(x).upper(), ints))

# print(a nice console progress bar)
def print_progress(iteration, total, prefix = '', suffix = '', decimals = 1, barLength = 100):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        barLength   - Optional  : character length of bar (Int)
    """
    formatStr       = "{0:." + str(decimals) + "f}"
    percents        = formatStr.format(100 * (iteration / float(total)))
    filledLength    = int(round(barLength * iteration / float(total)))
    bar             = 'x' * filledLength + '-' * (barLength - filledLength)
    sys.stdout.write('\r%s |%s| %s%s %s (%d of %d bytes)' % (prefix, bar, percents, '%', suffix, iteration, total)),
    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()
