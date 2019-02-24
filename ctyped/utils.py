from ctypes import c_char_p, c_wchar_p, get_errno
from errno import errorcode
from os import strerror

from typing import Tuple


def str_to_char_p(value: str) -> bytes:
    """Creates a char * from Python string.

    :param value: Python string

    """
    return c_char_p(value.encode('utf-8'))


def str_from_char_p(value: bytes) -> str:
    """Creates Python string from char *.

    :param value: char * value

    """
    return c_char_p(value).value.decode('utf-8')


def str_to_wchar_p(value: str) -> bytes:
    """Creates a wide char * from Python string.

    :param value: Python string

    """
    return c_wchar_p(value)


def str_from_wchar_p(value: bytes) -> str:
    """Creates Python string from wide char *.

    :param value: char * value

    """
    return c_wchar_p(value).value


def get_last_error() -> Tuple[int, str, str]:
    """Returns last error (``errno``) information tuple:

        (err_no, err_code, err_message)

    """
    num = get_errno()
    code = errorcode[num]
    msg = strerror(num)

    return num, code, msg
