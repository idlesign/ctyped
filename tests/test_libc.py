from ctypes.util import find_library
from pathlib import Path

import pytest

from ctyped.sniffer import DwarfSniffer
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


def test_sniff_external_debug_file():

    if not DwarfSniffer.is_available():
        pytest.skip('pyelftools is not installed')

    libc_so = Path('/lib/x86_64-linux-gnu/libc.so.6')

    if not libc_so.exists():
        pytest.skip('libc.so.6 path not found')

    sigs = DwarfSniffer(str(libc_so)).sniff()

    if not sigs:
        pytest.skip('no debug information available for libc')

    assert len(sigs) > 100
    assert {'read', 'write', 'getenv', 'memcpy'} & set(sigs)
