import ctypes
import inspect
from difflib import get_close_matches
from typing import Any, NamedTuple
from ctypes import get_errno, CFUNCTYPE
from errno import errorcode
from os import strerror
from collections.abc import Callable

from . import types as ctyped_types
from .exceptions import TypehintError, FunctionRedeclared
from .types import CChars, CInt8, CInt8U, CInt16, CInt16U, CInt32, CInt32U, CInt64, CInt64U

class FuncInfo(NamedTuple):
    name_py: str
    name_c: str
    annotations: dict
    options: dict


class ErrorInfo(NamedTuple):
    num: int
    code: str | None
    msg: str


class _Missing(NamedTuple):
    pass


_MISSING = _Missing()


def extract_func_info(func: Callable, *, name_c: str | None, scope: dict, registry: dict) -> FuncInfo:

    name_py = func.__name__
    name = scope.get('prefix', '') + (name_c or name_py)

    if name in registry:
        raise FunctionRedeclared(f'Unable to redeclare: {name} ({name_py})')

    annotated_args = {}
    annotations = func.__annotations__

    # Gather all args and annotations for them.
    for argname in inspect.getfullargspec(func).args:

        if argname == 'cfunc':
            continue

        annotation = annotations.get(argname, _MISSING)

        if argname == 'self' and annotation is _MISSING:
            # Pick class name from qualname.
            annotation = func.__qualname__.split('.')[-2]

        annotated_args[argname] = annotation

    annotated_args['return'] = annotations.get('return')

    return FuncInfo(name_py=name_py, name_c=name, annotations=annotated_args, options=scope)


def thint_str_to_obj(thint: str):

    fback = inspect.currentframe().f_back

    while fback:
        target = fback.f_globals.get(thint)

        if target:
            return target

        fback = fback.f_back


def cast_type(func_info, argname: str, thint: Any):

    if thint is None:
        return None

    if isinstance(thint, str):
        thint_orig = thint
        thint = thint_str_to_obj(thint)

        if thint is None:
            candidates = [*dir(ctyped_types), 'int', 'str', 'float', 'bool', 'bytes']
            close = get_close_matches(thint_orig, candidates, n=3, cutoff=0.6)
            suggestion = f" Did you mean: {', '.join(close)}?" if close else ''

            raise TypehintError(
                f'Unable to resolve type hint. '
                f'Function: {func_info.name_py}. Arg: {argname}. Type: {thint_orig}.{suggestion}')

    if thint is bool:
        thint = ctypes.c_bool

    elif thint is float:
        thint = ctypes.c_double

    elif thint is str:
        thint = func_info.options.get('str_type', CChars)

    elif thint is bytes:
        thint = ctypes.c_char_p

    elif thint is int:
        int_bits = func_info.options.get('int_bits')
        int_sign = func_info.options.get('int_sign')

        thint_map = {
            8: (CInt8, CInt8U),
            16: (CInt16, CInt16U),
            32: (CInt32, CInt32U),
            64: (CInt64, CInt64U),

        }

        if int_bits is None:
            int_bits = 32

        if int_bits not in thint_map:
            raise TypehintError(
                f'Wrong value passed for int_bits: {int_bits}. '
                f'Function: {func_info.name_py}. Arg: {argname}.')

        type_idx = 1 if (int_sign is not None and not int_sign) else 0

        thint = thint_map[int_bits][type_idx]

    return thint


def get_last_error() -> ErrorInfo:
    """Returns last error (``errno``) information named tuple:

    .. code-block:: python

        (err_no, err_code, err_message)

    """
    num = get_errno()
    code = errorcode.get(num)
    msg = strerror(num)

    return ErrorInfo(num=num, code=code, msg=msg)


def raises(exc: type[Exception], *, ok: Any = 0, describe: Callable[[Any], str] | dict | None = None) -> Callable:
    """Returns an errcheck callable raising the given exception
    when a function result is not equal to the expected value.

    .. code-block:: python

        @lib.f(errcheck=raises(ZlibError, describe=zError))
        def deflateInit2_(strm: CPointer, level: int) -> int:
            ...

    :param exc: Exception class to raise.

    :param ok: Expected (successful) result value.

    :param describe: Maps a result value to an error message.
        Either a callable or a ``{value: message}`` dict.
        If not set, the result value itself is used as a message.

    """
    def raises_(result, func, args):

        if result == ok:
            return result

        msg = result

        if callable(describe):
            msg = describe(result)

        elif describe is not None:
            msg = describe.get(result, result)

        raise exc(msg)

    return raises_


def check_errno(*, on: Any = -1, exc: type[Exception] = OSError) -> Callable:
    """Returns an errcheck callable raising the given exception
    with errno information when a function result is equal
    to the given sentinel value.

    .. code-block:: python

        @lib.f(errcheck=check_errno())
        def write(fd: int, buf: bytes, count: CSizeT) -> CSSizeT:
            ...

    :param on: Sentinel result value indicating an error.
        Use None for NULL-returning functions.

    :param exc: Exception class to raise. Is called with (errno, message).

    """
    def check_errno_(result, func, args):

        if result != on:
            return result

        err = get_last_error()
        raise exc(err.num, err.msg)

    return check_errno_


def c_callback(use_errno: bool = False) -> Callable:
    """Decorator to turn a Python function into a C callback function.

    .. code-block:: python

        @lib.f
        def c_func_using_callback(hook: CPointer) -> int:
            ...

        @c_callback
        def hook(num: int) -> int:
            return num + 10

        c_func_using_callback(hook)

    :param use_errno:

    """
    def cfunction_(func: Callable) -> Callable:

        func_info = extract_func_info(func, name_c=None, scope={}, registry={})
        annotations = func_info.annotations

        restype = cast_type(func_info, 'return', annotations.pop('return', None))
        argtypes = [cast_type(func_info, argname, argtype) for argname, argtype in annotations.items()]

        functype = CFUNCTYPE(restype, *argtypes, use_errno=use_errno)
        cfunc = functype(func)

        return cfunc

    if callable(use_errno):
        # Decorator without params.
        return cfunction_(use_errno)

    return cfunction_
