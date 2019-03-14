Quickstart
==========


.. code-block:: python

    from typing import Callable
    from ctyped.toolbox import Library
    from ctyped.types import CInt

    # Define a library.
    lib = Library('mylib.so')

    # Type less with function names prefixes.
    with lib.scope(prefix='mylib_'):

        # Describe function available in the library.
        @lib.function(name='otherfunc')
        def some_func(title: str, year: int) -> str:
            ...

        with lib.scope(prefix='mylib_grouped_', int_bits=64, int_sign=False):

            class Thing(CInt):

                @lib.method(int_sign=True)  # Override `int_sign` from scope.
                def one(self, some: int) -> int:
                    # Implicitly pass Thing instance alongside
                    # with explicitly passed `some` arg.
                    ...

                @lib.method
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
        def get_utf(some: str) -> str:
            ...

    # Bind ctype types to functions available in the library.
    lib.bind_types()

    # Call function from the library.
    result_string = some_func('Hello!', 2019)  # Call ``mylib_otherfunc``
    result_wide = Wide.get_utf('some')  # Call ``common_get_utf``

    thing = get_thing()

    thing.one(12)  # Call ``mylib_mylib_grouped_one``.
    thing.two(13)  # Call ``mylib_mylib_grouped_two``

