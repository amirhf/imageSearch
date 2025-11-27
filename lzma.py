try:
    from backports.lzma import *
    from backports.lzma import _encode_filter_properties, _decode_filter_properties
except ImportError:
    pass
