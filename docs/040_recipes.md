# Recipes

Common C interop scenarios and how to express them with `ctyped`.

## Fixed-size arrays in structures

Use the native ctypes `type * size` syntax in field hints:

```python
@lib.structure
class Record:

    coords: CInt * 4   # int coords[4]
    name: CChar * 32   # char name[32]


record = Record()
record.coords[0] = 7
record.name = b'abc'
```

!!! note
    Use `CChar` (single chars) for char buffers, not `CChars`
    (which is a `char *` pointer, so `CChars * 8` means `char *name[8]`).

## Strings into out-buffers

When C fills a caller-provided buffer (like `gzgets` does), allocate it with `CRef.carray`:

```python
@lib.f
def gzgets(file: CPointer, buf: CRef, length: int) -> str:
    ...


buf = CRef.carray(str, size=64)
gzgets(handle, buf, 64)
text = str(buf)
```

## Callback fields in structures

Some structs carry function pointers (e.g. `zalloc`/`zfree` hooks in zlib's `z_stream`).
Declare such fields as `CPointer`:

```python
@lib.structure
class Stream:

    zalloc: CPointer
    zfree: CPointer
    opaque: CPointer
```

Pass callback functions made with the `c_callback` decorator.

## Binary data

Use the `bytes` hint for raw binary data. Unlike `str`, it is passed
to C without UTF-8 encoding:

```python
@lib.f
def gzwrite(file: CPointer, buf: bytes, length: CIntU) -> int:
    ...
```

!!! warning
    `bytes` objects are immutable, so never use them for buffers that C
    writes into — allocate a writable buffer with `CRef.carray` instead.
    On the result side `bytes` is read up to the first NUL byte.

## Error handling

Functions returning a status code (zlib, sqlite, libcurl style) can be
turned into raising ones with the `raises` errcheck helper.
The error message is produced from a dict or a callable:

```python
class ZlibError(Exception):
    """zlib call failed."""


@lib.f
def zError(errcode: int) -> str:
    ...


@lib.f(errcheck=raises(ZlibError, describe=zError))
def compress2(dest: CRef, dest_len: CRef, source: bytes, source_len: CLongU, level: int) -> int:
    ...
```

Functions following the errno convention (return `-1` or `NULL` and set
`errno`) are handled by `check_errno`, raising `OSError` by default:

```python
@lib.f(errcheck=check_errno())          # -1 means failure
def close(fd: int) -> int:
    ...


@lib.f(errcheck=check_errno(on=None))   # NULL means failure
def fopen(path: str, mode: str) -> CPointer:
    ...
```
