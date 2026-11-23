import gzip
import zlib
from ctypes.util import find_library

import pytest

from ctyped.toolbox import Library
from ctyped.types import CIntU, CLongU, CPointer, CRef

if find_library('z') is None:
    pytest.skip('libz is not available', allow_module_level=True)

zlib_lib = Library('z', int_bits=32)


@zlib_lib.f
def zlibVersion() -> str:
    ...


@zlib_lib.f
def crc32(crc: CLongU, buf: str, length: CIntU) -> CLongU:
    ...


@zlib_lib.f
def adler32(adler: CLongU, buf: str, length: CIntU) -> CLongU:
    ...


@zlib_lib.f
def compressBound(source_len: CLongU) -> CLongU:
    ...


@zlib_lib.f
def gzopen(path: str, mode: str) -> CPointer:
    ...


@zlib_lib.f
def gzread(file: CPointer, buf: CRef, length: CIntU) -> int:
    ...


@zlib_lib.f
def gzclose(file: CPointer) -> int:
    ...


zlib_lib.bind_types()


def test_version():
    assert zlibVersion() == zlib.ZLIB_VERSION


def test_checksums():

    data = 'some data to checksum'
    data_len = len(data)

    assert crc32(0, data, data_len) == zlib.crc32(data.encode())
    assert adler32(1, data, data_len) == zlib.adler32(data.encode())


def test_compress_bound():
    assert compressBound(100) > 100


def test_gzread(tmp_path):

    payload = b'gzipped payload'

    file_gz = tmp_path / 'data.gz'
    file_gz.write_bytes(gzip.compress(payload))

    handle = gzopen(str(file_gz), 'rb')
    assert handle

    buf = CRef.carray(str, size=64)
    read = gzread(handle, buf, 64)

    assert gzclose(handle) == 0
    assert read == len(payload)
    assert str(buf) == payload.decode()
