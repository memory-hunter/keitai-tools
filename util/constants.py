ENCODINGS = ['cp932', 'utf-8']
EARLY_NULL_TYPE_OFFSETS = [
    (0x5C, 0x6C),
]
NULL_TYPE_OFFSETS = [
    (0x8C, 0xD4),
    (0xD4, 0x1C0),
    (0x94, 0xDC),
    (0xB8, 0x184),
    (0x94, 0x160),
    (0x11C, 0x224),
    (0x5C, 0x6C),
    (0x110, 0x218),
]
PLAINTEXT_CUTOFF_OFFSETS = [
    0x68C,
    0x990,
    0x9B4,
    0x9B8,
    0x5EBC,
    0x62C0,
    0x76C0,
]
MINIMAL_VALID_KEYWORDS = [
    'AppName',
    'PackageURL',
    'AppClass',
    'LastModified',
]
SH_TYPE_OFFSETS = [
    24,
    32,
    40,
]
SO_TYPE_OFFSETS = [
    0xD3C,
    0xD42,
    0xDF4,
    0xF84,
]