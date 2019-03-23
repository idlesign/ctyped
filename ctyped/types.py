import ctypes
from typing import Callable, Any, Tuple, Optional


class CastedTypeBase:

    @classmethod
    def _ct_res(cls, cobj: Any, *args, **kwargs) -> Any:  # pragma: nocover
        raise NotImplementedError

    @classmethod
    def from_param(cls, val: Any) -> Any:  # pragma: nocover
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


class CObject(CastedTypeBase, ctypes.c_void_p):
    """Helper to represent a C pointer as a link to a Python object."""

    @classmethod
    def _ct_res(cls, cobj: 'CObject', *args, **kwargs):
        return cobj

    @classmethod
    def from_param(cls, obj: 'CObject'):
        return obj


class CRef(CastedTypeBase):
    """Reference helper."""

    @classmethod
    def carray(cls, typecls: Any, *, size: int = 1) -> 'CRef':
        """Alternative constructor. Creates a reference to array."""

        typecls = {

            int: ctypes.c_int,
            str: ctypes.c_char,
            bool: ctypes.c_bool,
            float: ctypes.c_float,

        }.get(typecls, typecls)

        val = (typecls * (size or 1))()

        return cls(val)

    @classmethod
    def cbool(cls, value: bool = False) -> 'CRef':
        """Alternative constructor. Creates a reference to boolean."""
        return cls(ctypes.c_bool(value))

    @classmethod
    def cint(cls, value: int = 0) -> 'CRef':
        """Alternative constructor. Creates a reference to integer."""
        return cls(ctypes.c_int(value))

    @classmethod
    def cfloat(cls, value: float = 0.0) -> 'CRef':
        """Alternative constructor. Creates a reference to float."""
        return cls(ctypes.c_float(value))

    @classmethod
    def from_param(cls, obj: 'CRef'):
        return ctypes.byref(obj._ct_val)

    def __init__(self, cval: Any):
        self._ct_val = cval

    def __iter__(self):
        # Allows iteration for arrays.
        return iter(self._ct_val)

    def __str__(self):
        return self._ct_val.value.decode('utf-8')

    def __int__(self):
        return self._ct_val.value

    def __float__(self):
        return self._ct_val.value

    def __bool__(self):
        return self._ct_val.value

    def __eq__(self, other):
        return self._ct_val.value == other

    def __ne__(self, other):
        return self._ct_val.value != other

    def __lt__(self, other):
        return self._ct_val.value < other

    def __gt__(self, other):
        return self._ct_val.value > other

    def __le__(self, other):
        return self._ct_val.value <= other

    def __ge__(self, other):
        return self._ct_val.value >= other


class CChars(CastedTypeBase, ctypes.c_char_p):
    """Represents a Python string as a C chars pointer."""

    @classmethod
    def _ct_res(cls, cobj: 'CChars', *args, **kwargs) -> Optional[str]:
        value = cobj.value

        if not value:
            return ''

        return value.decode('utf-8')

    @classmethod
    def from_param(cls, val: str):
        return ctypes.c_char_p(val.encode('utf-8'))


class CCharsW(CastedTypeBase, ctypes.c_wchar_p):
    """Represents a Python string as a C wide chars pointer."""

    @classmethod
    def _ct_res(cls, cobj: 'CCharsW', *args, **kwargs) -> Optional[str]:
        return cobj.value

    @classmethod
    def from_param(cls, val: str):
        return ctypes.c_wchar_p(val)
