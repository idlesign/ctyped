import ctypes

from .utils import str_to_char_p, str_to_wchar_p, str_from_char_p, str_from_wchar_p


class CastedTypeBase:

    from_param = None
    to_result = None


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


class CChars(CastedTypeBase):
    """Represents a Python string as a C chars pointer."""

    from_param = str_to_char_p
    to_result = str_from_char_p


class CCharsW(CastedTypeBase):
    """Represents a Python string as a C wide chars pointer."""

    from_param = str_to_wchar_p
    to_result = str_from_wchar_p
