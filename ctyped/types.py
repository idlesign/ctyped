import ctypes

from .utils import str_to_char_p


class CObject(ctypes.c_void_p):
    """"""

# getattr to cheat type hints
CShort: int = getattr(ctypes, 'c_short')
CShortU: int = getattr(ctypes, 'c_ushort')
CLong: int = getattr(ctypes, 'c_long')
CLongU: int = getattr(ctypes, 'c_ulong')
CLongLong: int = getattr(ctypes, 'c_longlong')
CLongLongU: int = getattr(ctypes, 'c_ulonglong')

CInt: int = getattr(ctypes, 'c_int')
CIntU: int = getattr(ctypes, 'c_uint')
CInt8: int = getattr(ctypes, 'c_int8')
CInt8U: int = getattr(ctypes, 'c_uint8')
CInt16: int = getattr(ctypes, 'c_int16')
CInt16U: int = getattr(ctypes, 'c_uint16')
CInt32: int = getattr(ctypes, 'c_int32')
CInt32U: int = getattr(ctypes, 'c_uint32')
CInt64: int = getattr(ctypes, 'c_int64')
CInt64U: int = getattr(ctypes, 'c_uint64')

CPointer: CObject = getattr(ctypes, 'c_void_p')


class CStr:
    """Represents Python string as a C chars pointer."""

    @classmethod
    def from_param(cls, val):
        return str_to_char_p(val)
