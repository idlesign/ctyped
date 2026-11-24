# Sniffing

`ctyped` can inspect a shared library and generate draft interface declarations
for it, so you do not have to write them from scratch.

Sniffing uses `nm` from the binutils package to list exported functions.
When the `pyelftools` package is installed and the library carries DWARF debug
information (either embedded or in a separate dbgsym file), the generated
declarations also include deduced argument and result type hints.

## Basic usage

Call `.sniff()` on a library and dump the result with `.to_ctyped()`:

```python
from ctyped.toolbox import Library

lib = Library('z')

result = lib.sniff()
print(result.to_ctyped())
```

This produces ready to review declarations like:

```python
lib = Library('/lib/x86_64-linux-gnu/libz.so.1')
from ctyped.types import CIntU, CLongU, CPointer


@lib.f
def adler32(adler: CLongU, buf: str, length: CIntU) -> CLongU:
    """adler32.c:166"""


@lib.f
def gzopen(path: str, mode: str) -> CPointer:
    """gzlib.c:105"""


lib.bind_types()
```

## Sniffing without loading

The library does not have to be loaded into the process —
useful for libraries with hostile initialization routines:

```python
lib = Library('z', autoload=False)
result = lib.sniff()
```

## Notes and limitations

- Review the generated hints before use: pointers are mapped to `CPointer`,
  so adjust them to structures, `CRef`, etc. where appropriate.
- Signatures can not be deduced for aliases and ifunc-resolved symbols,
  variadic functions, and functions taking structures by value;
  those stubs are generated without annotations.
- C++ symbols (mangled, unusable via `ctypes` anyway) are skipped.
- Libraries without debug information produce plain `pass` stubs.
