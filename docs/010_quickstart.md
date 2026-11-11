# Quickstart

```python
from typing import Callable
from ctyped.toolbox import Library
from ctyped.types import CInt

# Define a library.
lib = Library('mylib.so')

# Structures are defined with the help of `structure` decorator
@lib.structure
class Box:

    one: int
    two: str
    innerbox: 'Box'  # That'll be a pointer.

# Type less with function names prefixes.
with lib.scope(prefix='mylib_'):

    # Describe function available in the library.
    @lib.function(name='otherfunc')
    def some_func(title: str, year: int) -> str:
        ...

    @lib.f  # `f` is a shortcut for function.
    def struct_func(src: Box) -> Box:
        ...

    with lib.s(prefix='mylib_grouped_', int_bits=64, int_sign=False):  # `s` is a shortcut for scope.

        class Thing(CInt):

            @lib.method(int_sign=True)  # Override `int_sign` from scope.
            def one(self, some: int) -> int:
                # Implicitly pass Thing instance alongside
                # with explicitly passed `some` arg.
                ...

            @lib.m  # `m` is a shortcut for method.
            def two(self, some:int, cfunc: Callable) -> int:
                # `cfunc` is a wrapper, calling an actual ctypes function.
                result = cfunc()
                # If no arguments, the wrapper will try to detect them automatically.
                return result + 1

    @lib.function
    def get_thing() -> Thing:
        ...

# Or you may use classes as namespaces.
@lib.cls(prefix='common_', str_type=CCharsW)
class Wide:

    @staticmethod
    @lib.function
    ...
```
