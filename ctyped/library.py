import ctypes
import inspect
import logging
import os
from contextlib import contextmanager
from ctypes.util import find_library
from functools import partial, partialmethod, reduce
from typing import Any, Optional, Callable, Union, List, Dict, Type, ContextManager

from .exceptions import UnsupportedTypeError, TypehintError, CtypedException
from .types import CChars, CastedTypeBase, CStruct
from .utils import cast_type, extract_func_info, FuncInfo

LOGGER = logging.getLogger(__name__)


class Scopes:

    def __init__(self, params: dict):
        self._scopes: List[Dict] = []
        self._keys = ['prefix', 'str_type', 'int_bits', 'int_sign']
        self.push(params)

    def __call__(
            this,
            prefix: Optional[str] = None,
            str_type: Type[CastedTypeBase] = CChars,
            int_bits: Optional[int] = None,
            int_sign: Optional[bool] = None,
            **kwargs) -> ContextManager['Scopes']:
        """

        :param prefix: Function name prefix to apply to functions under the manager.

        :param str_type: Type to represent strings.

            * ``CChars`` - strings as chars (ANSI) **default**
            * ``CCharsW`` - strings as wide chars (UTF)

        :param int_bits: int length to be used in function.

            Possible values: 8, 16, 32, 64

        :param int_sign: Flag. Whether to use signed (True) or unsigned (False) ints.

        :param kwargs:

        """
        return this.context(locals())

    def push(self, params: dict):

        scope = {key: params.get(key) for key in self._keys}
        self._scopes.append(scope)

    def pop(self):
        self._scopes.pop()

    def flatten(self):

        scopes = self._scopes
        keys_bool = {'int_sign'}
        keys_concat = {'prefix'}
        result = {}

        def choose(current, prev):
            return current or prev

        def pick_bool(current, prev):
            return current if current is not None else prev

        def concat(current, prev):
            return (prev or '') + (current or '')

        for key in self._keys:

            if key in keys_concat:
                reducer = concat

            elif key in keys_bool:
                reducer = pick_bool

            else:
                reducer = choose

            result[key] = reduce(reducer, (scope[key] for scope in scopes[::-1]))

        return result

    @contextmanager
    def context(self, params: dict):
        self.push(params)
        yield self
        self.pop()


class Library:
    """Main entry point to describe C library interface.

    Basic usage:

    .. code-block:: python

        lib = Library('mylib')

        with lib.scope(prefix='mylib_'):

            @lib.function()
            def my_func():
                ...

        lib.bind_types()

    """

    def __init__(
            self, name: str, *, autoload: bool = True,
            prefix: Optional[str] = None,
            str_type: Type[CastedTypeBase] = CChars,
            int_bits: Optional[int] = None,
            int_sign: Optional[bool] = None
    ):
        """

        :param name: Shared library name or filepath.

        :param autoload: Load library just on Library object initialization.

        :param prefix: Function name prefix to apply to functions in the library.

            Useful when C functions have common prefixes.

        :param str_type: Type to represent strings.

            * ``CChars`` - strings as chars (ANSI) **default**
            * ``CCharsW`` - strings as wide chars (UTF)

            .. note:: This setting is global to library. Can be changed on function definition level.

        :param int_bits: int length to use by default.

            Possible values: 8, 16, 32, 64

            .. note:: This setting is global to library. Can be changed on function definition level.

        :param int_sign: Flag. Whether to use signed (True) or unsigned (False) ints.

            .. note:: This setting is global to library. Can be changed on function definition level.

        """
        self.scope = Scopes(locals())
        self.s = self.scope

        self.name = name
        self.lib = None
        self.funcs: Dict[str, Union[Callable, partialmethod[Any]]] = {}

        autoload and self.load()

    def load(self):
        """Loads shared library."""
        name = self.name

        if not os.path.exists(name):
            name = find_library(name)

        lib = ctypes.CDLL(name, use_errno=True)

        if lib._name is None:
            lib = None

        if lib is None:
            raise CtypedException('Unable to find library: %s' % name)

        self.lib = lib

    def structure(
            self, *,
            pack: Optional[int] = None,
            str_type: Optional[CastedTypeBase] = None,
            int_bits: Optional[int] = None,
            int_sign: Optional[bool] = None,
    ):
        """Class decorator for C structures definition.

        .. code-block:: python

            @lib.structure
            class MyStruct:

                first: int
                second: str
                third: 'MyStruct'

        :param pack: Allows custom maximum alignment for the fields (as #pragma pack(n)).

        :param str_type: Type to represent strings.

        :param int_bits: int length to be used in function.

        :param int_sign: Flag. Whether to use signed (True) or unsigned (False) ints.

        """
        params = locals()

        def wrapper(cls_):

            annotations = {
                attrname: attrhint for attrname, attrhint in cls_.__annotations__.items()
                if not attrname.startswith('_')}

            with self.scope(**params):

                cls_name = cls_.__name__

                info = FuncInfo(
                    name_py=cls_name, name_c=None,
                    annotations=annotations, options=self.scope.flatten())

                # todo maybe support big/little byte order
                struct = type(cls_name, (CStruct, cls_), {})

                ct_fields = {}
                fields = []

                for attrname, attrhint in annotations.items():

                    if attrhint == cls_name:
                        casted = ctypes.POINTER(struct)
                        ct_fields[attrname] = struct

                    else:
                        casted = cast_type(info, attrname, attrhint)

                        if issubclass(casted, CastedTypeBase):
                            ct_fields[attrname] = casted

                    fields.append((attrname, casted))

                LOGGER.debug('Structure %s fields: %s', cls_name, fields)

                if pack:
                    struct._pack_ = pack

                struct._ct_fields = ct_fields
                struct._fields_ = fields

            return struct

        return wrapper

    def cls(
            self, *,
            prefix: Optional[str] = None,
            str_type: Optional[CastedTypeBase] = None,
            int_bits: Optional[int] = None,
            int_sign: Optional[bool] = None,
    ):
        """Class decorator. Allows common parameters application for class methods.

        .. code-block:: python

            @lib.cls(prefix='common_', str_type=CCharsW)
            class Wide:

                @staticmethod
                @lib.function()
                def get_utf(some: str) -> str:
                    ...

        :param prefix: Function name prefix to apply to functions under the manager.

        :param str_type: Type to represent strings.

        :param int_bits: int length to be used in function.

        :param int_sign: Flag. Whether to use signed (True) or unsigned (False) ints.

        """
        self.scope.push(locals())

        def wrapper(cls_):
            # Class body construction is done, unwind scope.
            self.scope.pop()
            return cls_

        return wrapper

    def function(
            self, name_c: Optional[Union[str, Callable]] = None, *, wrap: bool = False,
            str_type: Optional[CastedTypeBase] = None,
            int_bits: Optional[int] = None,
            int_sign: Optional[bool] = None,

    ) -> Callable:
        """Decorator to mark functions which exported from the library.

        :param name_c: C function name with or without prefix (see ``.scope(prefix=)``).
            If not set, Python function name is used.

        :param wrap: Do not replace decorated function with ctypes function,
            but with wrapper, allowing pre- or post-process ctypes function call.

            Useful to organize functions to classes (to automatically pass ``self``)
            to ctypes function to C function.

            .. code-block:: python

                class Thing(CObject):

                    @lib.function(wrap=True)
                    def one(self, some: int) -> int:
                        # Implicitly pass Thing instance alongside
                        # with explicitly passed `some` arg.
                        ...

                    @lib.function(wrap=True)
                    def two(self, some:int, cfunc: Callable) -> int:
                        # `cfunc` is a wrapper, calling an actual ctypes function.
                        # If no arguments provided the wrapper will try detect them
                        # automatically.
                        result = cfunc()
                        return result + 1

        :param str_type: Type to represent strings.

            .. note:: Overrides the same named param from library level (see ``__init__`` description).

        :param int_bits: int length to be used in function.

            .. note:: Overrides the same named param from library level (see ``__init__`` description).

        :param int_sign: Flag. Whether to use signed (True) or unsigned (False) ints.

            .. note:: Overrides the same named param from library level (see ``__init__`` description).

        """
        def cfunc_wrapped(*args, f: Callable, **kwargs):

            if not args:
                argvals = inspect.getargvalues(getattr(inspect.currentframe(), 'f_back'))
                loc = argvals.locals
                args = tuple(loc[argname] for argname in argvals.args if argname != 'cfunc')

            return f(*args)

        def function_(func_py: Callable, *, name_c: Optional[str], scope: dict):

            info = extract_func_info(func_py, name_c=name_c, scope=scope, registry=self.funcs)
            name = info.name_c

            func_c = getattr(self.lib, name)

            # Prepare for late binding in .bind_types().
            func_c.ctyped = info

            if wrap:
                func_args = inspect.getfullargspec(func_py).args

                if 'cfunc' in func_args:
                    # Use existing function, pass `cfunc`.

                    LOGGER.debug('Func [ %s -> %s ] uses wrapped manual call.', name, info.name_py)

                    func_swapped = partialmethod(func_py, cfunc=partial(cfunc_wrapped, f=func_c))

                else:
                    # Automatically bind first param (self, cls)

                    LOGGER.debug('Func [ %s -> %s ] uses wrapped auto call.', name, info.name_py)

                    func_swapped = partialmethod(func_c)

                setattr(func_swapped, 'cfunc', func_c)
                func_out = func_swapped

            else:

                LOGGER.debug('Func [ %s -> %s ] uses direct call.' % (name, info.name_py))

                func_out = func_c

            self.funcs[name] = func_out

            return func_out

        if callable(name_c):
            # Decorator without params.
            scope = self.scope.flatten()
            py_func, name_c = name_c, None
            return function_(py_func, name_c=name_c, scope=scope)

        # Decorator with parameters.
        with self.scope(**locals()) as scope:
            scope = scope.flatten()

        return partial(function_, name_c=name_c, scope=scope)

    def method(self, name_c: Optional[str] = None, **kwargs):
        """Decorator. The same as ``.function()`` with ``wrap=True``."""
        return self.function(name_c=name_c, wrap=True, **kwargs)

    def bind_types(self):
        """Deduces ctypes argument and result types from Python type hints,
        binding those types to ctypes functions.

        """
        LOGGER.debug('Binding signature types to ctypes functions ...')

        for name_c, func_out in self.funcs.items():

            func_c = getattr(func_out, 'cfunc', func_out)
            func_info: FuncInfo = func_c.ctyped

            name_py = func_info.name_py
            annotations = func_info.annotations
            errcheck = None

            try:
                return_is_annotated = 'return' in annotations
                restype = cast_type(func_info, 'return', annotations.pop('return', None))

                if restype and issubclass(restype, CastedTypeBase):
                    errcheck = restype._ct_res

                argtypes = [cast_type(func_info, argname, argtype) for argname, argtype in annotations.items()]

            except TypehintError:
                # Reset annotations to allow subsequent .bind_types() calls w/o exceptions.
                func_info.annotations.clear()
                raise

            try:
                if argtypes:
                    func_c.argtypes = argtypes

                if restype or return_is_annotated:
                    func_c.restype = restype

                if errcheck:
                    func_c.errcheck = errcheck

            except TypeError as e:

                raise UnsupportedTypeError(
                    'Unsupported types declared for %s (%s). Args: %s. Result: %s. Errcheck: %s.' %
                    (name_py, name_c, argtypes, restype, errcheck)) from e

    #####################################################################################
    # Shortcuts

    f = function
    """Shortcut for ``.function()``."""
    
    m = method
    """Shortcut for ``.method()``."""
    
    s = None  # type: ignore
    """Shortcut for ``.scope()``."""
