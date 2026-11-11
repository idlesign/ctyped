ctyped
======
https://github.com/idlesign/ctyped

|release| |lic| |ci| |coverage|

.. |release| image:: https://img.shields.io/pypi/v/ctyped.svg
    :target: https://pypi.python.org/pypi/ctyped

.. |lic| image:: https://img.shields.io/pypi/l/ctyped.svg
    :target: https://pypi.python.org/pypi/ctyped

.. |ci| image:: https://img.shields.io/travis/idlesign/ctyped/master.svg
    :target: https://travis-ci.org/idlesign/ctyped

.. |coverage| image:: https://img.shields.io/coveralls/idlesign/ctyped/master.svg
    :target: https://coveralls.io/r/idlesign/ctyped


Description
-----------

*Build ctypes interfaces for shared libraries with type hinting*

**Requires Python 3.6+**

* Less boilerplate;
* Logical structuring;
* Basic code generator (.so function -> ctyped function);
* Useful helpers.

.. code-block:: python

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

    # Bind ctype types to functions available in the library.
    lib.bind_types()

    # Call library function.
    result_string = some_func('Hello!', 2019, Box(one=35, two='dummy'))


Read the documentation for more information.


Documentation
-------------

http://ctyped.readthedocs.org/
