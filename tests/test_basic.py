import faulthandler
import os

import pytest

from ctyped.exceptions import FunctionRedeclared, TypehintError, UnsupportedTypeError
from ctyped.toolbox import Library, get_last_error, c_callback
from ctyped.types import CInt, CCharsW, CRef, CPointer

############################################################
# Library interface

# Watch for crashes.
faulthandler.enable()

MYLIB_PATH = os.path.join(os.path.dirname(__file__), 'mylib', 'mylib.so')

mylib = Library(MYLIB_PATH, int_bits=32)


@mylib.structure(int_bits=8, pack=16)
class MyStruct:

    _hidden: 'dummy'
    first: int
    second: str
    third: 'MyStruct'

    def get_additional(self):
        return 10


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
    def backcaller(val: CPointer) -> int:
        ...

    @mylib.f
    def handle_mystruct(val: MyStruct) -> MyStruct:
        ...

    @mylib.f
    def byref_int(val: CRef) -> None:
        ...

    @mylib.f
    def bool_to_bool(val: bool) -> bool:
        ...

    @mylib.f
    def float_to_float(val: float) -> float:
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
    assert not bool_to_bool(True)
    assert bool_to_bool(False)

    float_ = 1.3
    assert float_to_float(float_) == pytest.approx(float_)

    prober = get_prober()
    assert isinstance(prober, Prober)

    prober_val = prober.value

    assert prober.probe_add_one() == prober_val + 1
    assert prober.probe_add_three() == prober_val + 3

    byref_val = CRef.cint()
    assert byref_int(byref_val) is None
    assert int(byref_val) == 33
    assert byref_val == 33
    assert byref_val != 34
    assert 32 < byref_val < 34
    assert 32 <= byref_val <= 34
    assert byref_val
    assert float(byref_val) == pytest.approx(float(33))
    assert str(byref_val) == '33'


def test_cref_instantiation():
    assert isinstance(CRef.carray(bool, size=10), CRef)
    assert isinstance(CRef.cbool(True), CRef)
    assert isinstance(CRef.cfloat(10.25), CRef)


def test_with_errno():
    assert with_errno() == 333
    err = get_last_error()
    assert err.num == 2
    assert err.code == 'ENOENT'
    assert 'such file' in err.msg


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


def test_callback():

    @c_callback
    def hook(num: int) -> int:
        return num + 10

    assert backcaller(hook) == 43


def test_struct():

    struct = MyStruct(first=2, second='any', third=MyStruct(first=10))

    assert struct.get_additional() == 10  # verify method is copied

    result = handle_mystruct(struct)
    assert result.first == 4
    assert result.second == 'anything'
    assert '%s' % result.second == 'anything'
    assert result.second

    result.second = ''
    assert not result.second
    assert result.third.first == 15
