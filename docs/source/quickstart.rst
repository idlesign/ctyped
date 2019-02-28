Quickstart
==========


.. code-block:: python

    from typing import Callable
    from ctyped.toolbox import Library
    from ctyped.types import CInt

    # Define library.
    lib = Library('mylib.so')

    # Type less with function names prefixes.
    with lib.scope(prefix='mylib_'):

        # Describe function available in the library.
        @lib.function()
        def some_func(title: str, year: int) -> str:
            ...

        with lib.scope(prefix='mylib_grouped_', int_bits=64, int_sign=False):

            class Thing(CInt):

                @lib.method()
                def one(self, some: int) -> int:
                    # Implicitly pass Thing instance alongside
                    # with explicitly passed `some` arg.
                    ...

                @lib.method()
                def two(self, some:int, cfunc: Callable) -> int:
                    # `cfunc` is a wrapper, calling an actual ctypes function.
                    # If no arguments provided the wrapper will try detect them
                    # automatically.
                    result = cfunc()
                    return result + 1

        @lib.function()
        def get_thing() -> Thing:
            ...

    # Bind ctype types to functions available in the library.
    lib.bind_types()

    # Call function from the library.
    result_string = some_func('Hello!', 2019)

    thing = get_thing()

    thing.one(12)  # Call ``mylib_mylib_grouped_one``.
    thing.two(13)  # Call ``mylib_mylib_grouped_two``
