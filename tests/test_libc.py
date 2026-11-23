from ctypes.util import find_library

import pytest

from ctyped.toolbox import Library, check_errno
from ctyped.types import CPointer

if find_library('c') is None:
    pytest.skip('libc is not available', allow_module_level=True)

libc = Library('c')


@libc.f(errcheck=check_errno())
def close(fd: int) -> int:
    ...


@libc.f(errcheck=check_errno(on=None))
def fopen(path: str, mode: str) -> CPointer:
    ...


libc.bind_types()


def test_check_errno_on_int():

    with pytest.raises(OSError, match='Bad file descriptor'):
        close(-1)


def test_check_errno_on_null():

    with pytest.raises(OSError, match='No such file'):
        fopen('/ctyped_nonexistent_probe', 'rb')
