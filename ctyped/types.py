import ctypes
from typing import Callable, Type, Any, Tuple, Optional


class CastedTypeBase:

    _ct_typ: Optional[Type[ctypes._SimpleCData]] = None

    @classmethod
    def _ct_res(cls, result: Any, func: Callable, args: Tuple) -> Any:
        raise NotImplementedError

    @classmethod
    def from_param(cls, val: Any) -> Any:
        raise NotImplementedError


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

CPointer: Any = getattr(ctypes, 'c_void_p')


class CObject(CastedTypeBase):
    """Helper to represent a C pointer as a link to a Python object."""

    _ct_typ = ctypes.c_void_p
    _ct_val: Any = None  # Object attribute.

    @classmethod
    def _ct_res(cls, result: bytes, func: Callable, args: Tuple):

        obj = cls()
        # todo The following binding may be too late when __init__ depends on it.
        obj._ct_val = result

        return obj

    @classmethod
    def from_param(cls, obj: 'CObject'):
        return ctypes.c_void_p(obj._ct_val)


class CChars(CastedTypeBase):
    """Represents a Python string as a C chars pointer."""

    _ct_typ = ctypes.c_char_p

    @classmethod
    def _ct_res(cls, result: bytes, func: Callable, args: Tuple):
        return result.decode('utf-8')

    @classmethod
    def from_param(cls, val: str):
        return ctypes.c_char_p(val.encode('utf-8'))


class CCharsW(CastedTypeBase):
    """Represents a Python string as a C wide chars pointer."""

    _ct_typ = ctypes.c_wchar_p

    @classmethod
    def _ct_res(cls, result: bytes, func: Callable, args: Tuple):
        return result

    @classmethod
    def from_param(cls, val: str):
        return ctypes.c_wchar_p(val)
