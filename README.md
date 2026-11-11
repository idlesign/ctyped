# ctyped

<https://github.com/idlesign/ctyped>

[![release](https://img.shields.io/pypi/v/ctyped.svg)](https://pypi.python.org/pypi/ctyped)
[![lic](https://img.shields.io/pypi/l/ctyped.svg)](https://pypi.python.org/pypi/ctyped)
[![coverage](https://img.shields.io/coveralls/idlesign/ctyped/master.svg)](https://coveralls.io/r/idlesign/ctyped)

## Description

*Build ctypes interfaces for shared libraries with type hinting*

**Requires Python 3.10+**

* Less boilerplate;
* Logical structuring;
* Basic code generator (.so function -> ctyped function);
* Useful helpers.

```python
from ctyped.toolbox import Library

# Define library.
lib = Library('mylib.so')

@lib.structure
class Box:

    one: int
    two: str

# Type less with function names prefixes.
with lib.scope(prefix='mylib_'):

    # Describe function available in the library.
    @lib.function
    def some_func(title: str, year: int, box: Box) -> str:
        ...
```

## Documentation

<https://ctyped.readthedocs.io/>
