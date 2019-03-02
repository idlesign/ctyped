import os
import faulthandler

import pytest

from ctypes import c_int
from ctyped.exceptions import FunctionRedeclared, TypehintError, UnsupportedTypeError
from ctyped.toolbox import Library, get_last_error
from ctyped.types import CInt, CCharsW, CRef

############################################################
# Library interface

# Watch for crashes.
faulthandler.enable()

MYLIB_PATH = os.path.join(os.path.dirname(__file__), 'mylib', 'mylib.so')

mylib = Library(MYLIB_PATH, int_bits=32)


@mylib.f()
def f_noprefix_1() -> int:
    ...


@mylib.f()
def with_errno() -> int:
    ...


with mylib.scope('f_prefix_one_'):

    @mylib.function('func_1')
    def function_one() -> int:
        ...

    @mylib.function()
    def func_2() -> int:
        ...

    @mylib.f
    def byref_int(val: CRef) -> None:
        ...

    @mylib.function(int_bits=8, int_sign=False)
    def uint8_add(val: int) -> int:
        ...

    @mylib.f('char_p')
    def func_str(some: str) -> str:
        ...

    @mylib.cls(prefix='wchar_', str_type=CCharsW)
    class Wide:

        @staticmethod
        @mylib.f('p')
        def func_str_utf(some: str) -> str:
            ...

    with mylib.s('prefix_two_'):

        @mylib.f('func_3')
        def func_prefix_two_3() -> int:
            ...

    class Prober(CInt):

        @mylib.m
        def probe_add_one(self) -> int:
            ...

        @mylib.m('probe_add_two')
        def probe_add_three(self, cfunc) -> int:
            result = cfunc()
            return result + 1

    @mylib.f
    def get_prober() -> Prober:
        ...


mylib.bind_types()

############################################################
# Tests


def test_basic():
    assert f_noprefix_1() == -10
    assert function_one() == 1
    assert func_2() == 2
    assert func_prefix_two_3() == 3
    assert uint8_add(4) == 5

    prober = get_prober()
    assert isinstance(prober, Prober)

    prober_val = prober.value

    assert prober.probe_add_one() == prober_val + 1
    assert prober.probe_add_three() == prober_val + 3

    byref_val = CRef.int()
    assert byref_int(byref_val) is None
    assert int(byref_val) == 33
    assert byref_val == 33
    assert byref_val != 34
    assert 32 < byref_val < 34
    assert 32 <= byref_val <= 34


def test_with_errno():
    assert with_errno() == 333
    err_num, err_code, err_msg = get_last_error()
    assert err_num == 2
    assert err_code == 'ENOENT'
    assert 'such file' in err_msg


def test_strings():

    assert func_str('mind') == 'hereyouare: mind'
    assert Wide.func_str_utf('пример') == 'вот: пример'


def test_no_redeclare():

    with pytest.raises(FunctionRedeclared):

        @mylib.f()
        def f_noprefix_1() -> int:
            ...


def test_unresolved_typehint():

    @mylib.f()
    def buggy1(one: 'SomeDummyType') -> int:
        ...

    with pytest.raises(TypehintError) as e:
        mylib.bind_types()

    assert 'SomeDummyType' in str(e.value)


def test_unsupported_type():

    class SomeType: pass

    @mylib.f()
    def buggy2(one: SomeType) -> int:
        ...

    with pytest.raises(UnsupportedTypeError) as e:
        mylib.bind_types()

    assert 'buggy2 (buggy2)' in str(e.value)
