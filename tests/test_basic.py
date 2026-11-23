import ctypes
import faulthandler
from pathlib import Path

import pytest

from ctyped.exceptions import FunctionRedeclared, TypehintError, UnsupportedTypeError
from ctyped.toolbox import Library, get_last_error, c_callback
from ctyped.types import CInt, CChar, CCharsW, CFloat, CRef, CPointer

############################################################
# Library interface

# Watch for crashes.
faulthandler.enable()

MYLIB_PATH = Path(__file__).parent / 'mylib' / 'mylib.so'

mylib = Library(MYLIB_PATH, int_bits=32)


@mylib.structure(int_bits=8, pack=16)
class MyStruct:

    _hidden: 'dummy'
    first: int
    second: str
    third: 'MyStruct'

    def get_additional(self):
        return 10


@mylib.structure()
class WithArrays:

    coords: CInt * 4
    name: CChar * 8


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
    def float_to_float(val: CFloat) -> CFloat:
        ...

    @mylib.f
    def double_to_double(val: float) -> float:
        ...

    @mylib.function(int_bits=8, int_sign=False)
    def uint8_add(val: int) -> int:
        ...

    @mylib.f('char_p')
    def func_str(some: str) -> str:
        ...

    @mylib.f('bytes_p')
    def func_bytes(some: bytes) -> bytes:
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


def test_sniff():
    result = mylib.sniff()
    dumped = result.to_ctyped()
    assert "mylib.so')" in dumped
    assert 'def buggy1():' in dumped
    assert 'bind_types()' in dumped


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
    assert double_to_double(float_) == float_

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


def test_bytes():
    assert func_bytes(b'\xff\xfe mind') == b'hereyouare: \xff\xfe mind'


def test_null_string_result():

    lib = Library(MYLIB_PATH)

    with lib.scope('f_prefix_one_'):

        @lib.f('null_str')
        def null_str() -> str:
            ...

    lib.bind_types()
    assert null_str() is None


def test_get_last_error_unknown_errno():

    ctypes.set_errno(0)
    err = get_last_error()
    assert err.num == 0
    assert err.code is None


def test_invalid_int_bits():

    lib = Library(MYLIB_PATH)

    @lib.f(int_bits=7)
    def f_noprefix_1(val: int) -> int:
        ...

    with pytest.raises(TypehintError, match='int_bits'):
        lib.bind_types()


def test_default_int_is_32bit_signed():

    lib = Library(MYLIB_PATH)

    @lib.f()
    def f_noprefix_1() -> int:
        ...

    lib.bind_types()
    assert f_noprefix_1() == -10


def test_bare_decorator_no_prefix():

    lib = Library(MYLIB_PATH, int_bits=32)

    @lib.f
    def f_noprefix_1() -> int:
        ...

    lib.bind_types()
    assert f_noprefix_1() == -10


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


def test_unresolved_typehint_suggestion():

    lib = Library(MYLIB_PATH)

    @lib.f()
    def f_noprefix_1(val: 'CIn') -> int:
        ...

    with pytest.raises(TypehintError, match='Did you mean: CInt'):
        lib.bind_types()


def test_unsupported_type():

    class SomeType:
        pass

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
    assert f'{result.second}' == 'anything'
    assert result.second

    result.second = ''
    assert not result.second
    assert result.third.first == 15


def test_repr():
    assert repr(mylib) == f"<Library '{MYLIB_PATH}' funcs={len(mylib.funcs)}>"
    assert repr(CRef.cint(33)) == '<CRef(c_int(33))>'


def test_describe():

    desc = mylib.describe()

    func = desc['functions']['f_prefix_one_uint8_add']
    assert func['name_py'] == 'uint8_add'
    assert func['args'] == {'val': 'c_ubyte'}
    assert func['result'] == 'c_ubyte'
    assert func['errcheck'] is None

    struct = desc['structures']['MyStruct']
    assert struct['fields'] == {'first': 'c_byte', 'second': 'CChars', 'third': 'LP_MyStruct'}
    assert struct['size'] > 0


def test_struct_arrays():

    struct = WithArrays()

    struct.coords[1] = 7
    struct.name = b'ab'

    assert list(struct.coords) == [0, 7, 0, 0]
    assert struct.name == b'ab'
