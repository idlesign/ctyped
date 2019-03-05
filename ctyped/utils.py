import inspect
from collections import namedtuple
from ctypes import get_errno, CFUNCTYPE
from errno import errorcode
from os import strerror

from .exceptions import TypehintError, FunctionRedeclared
from .types import *

FuncInfo = namedtuple('FuncInfo', ['name_py', 'name_c', 'annotations', 'options'])
_MISSING = namedtuple('MissingType', [])


def extract_func_info(func: Callable, *, name_c: Optional[str], scope: dict, registry: dict) -> FuncInfo:

    name_py = func.__name__
    name = scope.get('prefix', '') + (name_c or name_py)

    if name in registry:
        raise FunctionRedeclared('Unable to redeclare: %s (%s)' % (name, name_py))

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

    fback = getattr(inspect.currentframe(), 'f_back')

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
            raise TypehintError(
                'Unable to resolve type hint. Function: %s. Arg: %s. Type: %s. ' %
                (func_info.name_py, argname, thint_orig))

    if thint is bool:
        thint = ctypes.c_bool

    elif thint is float:
        thint = ctypes.c_float

    elif thint is str:
        thint = func_info.options.get('str_type', CChars)

    elif thint is int:
        int_bits = func_info.options.get('int_bits')
        int_sign = func_info.options.get('int_sign', False)

        thint_map = {
            8: (CInt8, CInt8U),
            16: (CInt16, CInt16U),
            32: (CInt32, CInt32U),
            64: (CInt64, CInt64U),

        }

        if int_bits:
            assert int_bits in thint_map.keys(), 'Wrong value passed for int_bits.'

        else:
            int_bits = 64  # todo maybe try to guess

        type_idx = 1 if int_sign is False else 0

        thint = thint_map[int_bits][type_idx] or thint

    return thint


def get_last_error() -> Tuple[int, str, str]:
    """Returns last error (``errno``) information tuple:

        (err_no, err_code, err_message)

    """
    num = get_errno()
    code = errorcode[num]
    msg = strerror(num)

    return num, code, msg
