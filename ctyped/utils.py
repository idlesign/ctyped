from ctypes import get_errno
from errno import errorcode
from os import strerror

from typing import Tuple


def get_last_error() -> Tuple[int, str, str]:
    """Returns last error (``errno``) information tuple:

        (err_no, err_code, err_message)

    """
    num = get_errno()
    code = errorcode[num]
    msg = strerror(num)

    return num, code, msg
