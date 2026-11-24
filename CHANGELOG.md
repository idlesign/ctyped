# ctyped changelog

### Unreleased
* !! Changed 'float' type hint to map to C 'double' instead of C 'float'. Use the new CFloat hint for C 'float'.
* !! Changed CRef.carray() 'float' shortcut to map to C 'double', consistent with the 'float' hint. Pass CFloat explicitly for C 'float' arrays.
* !! Changed default 'int' hint mapping from 64 to 32 bits (C 'int'). Use CLong/CLongLong hints or int_bits=64 for wider integers.
* !! Changed string results (CChars/CCharsW): a NULL pointer from C now produces None instead of an empty string.
* !! Dropped Python 3.10 support (end of life); Python 3.11+ is required now. Type hints modernized accordingly.
* ++ Added 'bytes' type hint support: raw binary data as C chars pointer (no UTF-8 encoding).
* ++ Added CChar and CCharU type hints (C 'char' and 'unsigned char').
* ++ Added CFloat and CDouble type hints.
* ++ Added check_errno() errcheck helper turning C errno failures into exceptions (OSError by default).
* ++ Added CSizeT and CSSizeT type hints (C 'size_t' and 'ssize_t').
* ++ Added human-readable __repr__ for Library and CRef.
* ++ Added Library.describe() returning a structured description of the declared interface (functions, structures, bound types).
* ++ Added raises() errcheck helper and 'errcheck' parameter for .function()/.method() decorators.
* ++ Library.sniff() can now be used without loading the library into the process (autoload=False).
* ++ Library.sniff() now enriches sniffed symbols with function signatures from DWARF debug info when pyelftools package is available; external debug files (e.g. dbgsym packages) are used for stripped libraries.
* ++ Unresolved type hint errors now suggest close matches.
* ** Cleaned up ctyped.utils imports (no more star import).
* ** CRef is now explicitly unhashable since the referenced value may change from C side.
* ** Fixed code generation for versioned symbols (name@@VERSION produced invalid Python); stubs without line info now use 'pass' instead of an empty docstring.
* ** Fixed get_last_error() raising KeyError on unknown errno values; ErrorInfo.code is None in that case.
* ** Fixed int_sign=0 being treated as signed; falsy int_sign values now consistently mean unsigned.
* ** Fixed Library.sniff() failing for libraries loaded by name: library path is now resolved via ldconfig cache.
* ** Fixed sniffing crash on C++ libraries: mangled C++ symbols (unusable via ctypes anyway) are now skipped.
* ** Fixed TypeError on bare decorator (@lib.f/@lib.m without parentheses) usage when no prefix was set.
* ** Functions without a return type annotation are now documented as having a void result.
* ** Invalid int_bits value now raises TypehintError instead of AssertionError.
* ** Sniffing no longer drops all underscore-prefixed symbols (e.g. sanitizer runtimes APIs); only known loader internals are skipped.

### v0.8.1 [2026-11-14]
* ** Fixed missing Optional import in utils (import error on Python <3.14).

### v0.8.0 [2019-11-21]
* ++ Added .so sniffing with ctyped code generation support.
* ++ Library now can handle Path objects.

### v0.7.1 [2019-10-14]
* ** Fixed 'Library.load()' LD search.
* ** Fixed 'Unable to find library' message.

### v0.7.0
* ++ Added basic structures support.
* ++ CRef.carray() constructor now allows shortcuts for bool and float.
* ** CObject simplified.

### v0.6.0
* ++ 'get_last_error()' now returns ErrorInfo named tuple.
* ++ Basic support for callback functions.
* ** Class methods performance improved (less wrappers).

### v0.5.0
* ++ Added 'CRef' helper to pass by reference in arguments.
* ++ Now '-> None' annotation can be used for 'void' result.
* ++ Proper 'bool' handling.

### v0.4.0
* ++ 'function/f' and 'method/m' decorators now allow no params (less brackets).
* ++ Added 'Library.cls' decorator for classes.

### v0.3.0
* ++ 'functions_prefix' context manager is replaced by advanced 'scope'.

### v0.2.0
* ++ Added 'int_bits' shortcut option.
* ++ Added 'int_sign' shortcut option.
* ++ Added CObject convenience.
* ++ Added support for Python strings as wide chars.
* ** Result is now casted with 'errcheck'.

### v0.1.0
* ++ Basic functionality.
