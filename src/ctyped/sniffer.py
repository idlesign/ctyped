import keyword
import logging
import subprocess
from typing import NamedTuple
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import ClassVar

from .exceptions import SniffingError

try:
    from elftools.elf.elffile import ELFFile
    from elftools.common.exceptions import DWARFError, ELFRelocationError

    _PARSE_ERRORS = (KeyError, DWARFError)

except ImportError:
    ELFFile = None
    _PARSE_ERRORS = (KeyError,)

LOGGER = logging.getLogger(__name__)


def _get_dwarf_info(elf):
    """Returns DWARF info.

    Sections are read without relocations applied (those are only needed
    for address attributes we do not use); relocated reading is retried
    as a fallback.

    """

    try:
        return elf.get_dwarf_info(relocate_dwarf_sections=False)

    except ELFRelocationError:  # pragma: nocover
        return elf.get_dwarf_info()


def resolve_lib_path(name: str) -> str:
    """Resolves a library name or soname into a full filesystem path.

    Uses ldconfig cache when the given name is not a path itself.

    """
    if Path(name).exists():
        return name

    try:
        result = subprocess.run(['ldconfig', '-p'], capture_output=True)

    except FileNotFoundError:  # pragma: nocover
        result = None

    if result is not None and not result.returncode:

        for line in result.stdout.decode().splitlines():

            soname, sep, candidate = line.strip().partition(' => ')

            if sep and soname.split(' ')[0] == name and Path(candidate).exists():
                return candidate

    raise SniffingError(f'Unable to resolve library path: {name}')


class SniffedSymbol(NamedTuple):
    name: str
    address: str
    line: str
    args: list | None = None
    result: str | None = None
"""Represents a symbol sniffed from a library."""


class SniffResult:
    """Represents a library sniffing results."""

    def __init__(self, *, libpath: str):
        self.symbols: list[SniffedSymbol] = []
        self.libpath = libpath

    def add_symbol(self, symbol: SniffedSymbol):
        """Added a symbol to the result."""
        self.symbols.append(symbol)

    def to_ctyped(self):
        """Generates ctyped code from sniff result."""

        dumped = [
            '###',
            f'# Code below was automatically generated {datetime.utcnow()} UTC',
            f'# Total functions: {len(self.symbols)}',
            '###',
            f"lib = Library('{self.libpath}')",
        ]

        hints_builtin = {'int', 'str', 'float', 'bool', 'bytes', 'None'}
        hints_used = set()

        stubs = []

        for symbol in self.symbols:

            doc = f'"""{symbol.line}"""' if symbol.line else 'pass'

            if symbol.args is None:
                stub = f'''
                    @lib.f
                    def {symbol.name}():
                        {doc}
                    '''

            else:
                args = ', '.join(
                    f'{argname}_: {hint}' if keyword.iskeyword(argname) else f'{argname}: {hint}'
                    for argname, hint in symbol.args)
                result = f' -> {symbol.result}' if symbol.result else ''

                hints_used.update(hint for _, hint in symbol.args)

                if symbol.result:
                    hints_used.add(symbol.result)

                stub = f'''
                    @lib.f
                    def {symbol.name}({args}){result}:
                        {doc}
                    '''

            stubs.append(dedent(stub))

        hints = sorted(hints_used - hints_builtin)

        if hints:
            dumped.append(f'from ctyped.types import {", ".join(hints)}')

        dumped.append('')

        dumped.extend(stubs)
        dumped.append('\nlib.bind_types()')

        return '\n'.join(dumped)


class DwarfSniffer:
    """Extracts function signatures from DWARF debug information.

    Requires ``pyelftools`` package: when it is not installed,
    sniffing falls back to plain symbol names without signatures.

    """

    _TYPE_HINT_MAP: ClassVar[dict] = {
        'void': 'None',
        'bool': 'bool', '_Bool': 'bool',
        'char': 'CChar', 'signed char': 'CChar', 'unsigned char': 'CCharU',
        'short': 'CShort', 'short int': 'CShort', 'unsigned short': 'CShortU',
        'int': 'int', 'unsigned int': 'CIntU', 'unsigned': 'CIntU',
        'long': 'CLong', 'long int': 'CLong', 'unsigned long': 'CLongU',
        'long long': 'CLongLong', 'unsigned long long': 'CLongLongU',
        'float': 'CFloat', 'double': 'float',
        'int8_t': 'CInt8', 'uint8_t': 'CInt8U',
        'int16_t': 'CInt16', 'uint16_t': 'CInt16U',
        'int32_t': 'CInt32', 'uint32_t': 'CInt32U',
        'int64_t': 'CInt64', 'uint64_t': 'CInt64U',
        'size_t': 'CSizeT', 'ssize_t': 'CSSizeT',
    }

    def __init__(self, libpath: str | Path):
        """

        :param libpath: Library path to sniff for signatures.

        """
        self.libpath = str(libpath)

    @classmethod
    def is_available(cls) -> bool:
        """Whether signature sniffing is available (pyelftools is installed)."""
        return ELFFile is not None

    @staticmethod
    def _get_name(die) -> str | None:
        # Follows indirections common for optimized builds.

        for ind_attr in ('DW_AT_abstract_origin', 'DW_AT_specification'):

            if ind_attr in die.attributes:

                try:
                    die = die.get_DIE_from_attribute(ind_attr)

                except _PARSE_ERRORS:
                    return None

                break

        name_attr = die.attributes.get('DW_AT_name')
        return name_attr.value.decode() if name_attr else None

    def _resolve_type(self, die, depth=0) -> str | None:

        if depth > 10:
            return None

        for ind_attr in ('DW_AT_abstract_origin', 'DW_AT_specification'):

            if ind_attr in die.attributes:

                try:
                    die = die.get_DIE_from_attribute(ind_attr)

                except _PARSE_ERRORS:
                    return None

                break

        if 'DW_AT_type' not in die.attributes:
            return 'void'

        ref = die.get_DIE_from_attribute('DW_AT_type')
        tag = ref.tag

        if tag in ('DW_TAG_base_type', 'DW_TAG_typedef'):
            name_attr = ref.attributes.get('DW_AT_name')
            return name_attr.value.decode() if name_attr else None

        if tag in ('DW_TAG_const_type', 'DW_TAG_volatile_type', 'DW_TAG_restrict_type'):
            return self._resolve_type(ref, depth + 1)

        if tag == 'DW_TAG_pointer_type':
            inner = self._resolve_type(ref, depth + 1)
            return f'{inner} *' if inner else None

        if tag == 'DW_TAG_structure_type':
            name_attr = ref.attributes.get('DW_AT_name')
            return f'struct {name_attr.value.decode()}' if name_attr else None

        if tag == 'DW_TAG_enumeration_type':
            return 'int'

        return None

    def _resolve_hint(self, die) -> str | None:

        ctype = self._resolve_type(die)

        if ctype is None:
            return None

        if ctype.endswith(' *'):
            return 'str' if ctype[:-2] == 'char' else 'CPointer'

        return self._TYPE_HINT_MAP.get(ctype)

    @staticmethod
    def _get_build_id(elf) -> str | None:

        note = elf.get_section_by_name('.note.gnu.build-id')

        if note is None:
            return None

        data = note.data()
        namesz = int.from_bytes(data[0:4], 'little')
        desc_offset = 12 + ((namesz + 3) & ~3)

        return data[desc_offset:].hex() or None

    def _find_debug_file(self, elf) -> str | None:
        """Locates an external debug information file for a stripped library
        (see .gnu_debuglink), e.g. from a dbgsym package."""

        link_section = elf.get_section_by_name('.gnu_debuglink')

        if link_section is None:
            return None

        build_id = self._get_build_id(elf)

        if build_id:

            candidate = Path(f'/usr/lib/debug/.build-id/{build_id[:2]}/{build_id[2:]}.debug')

            if candidate.exists():
                return str(candidate)

        link_name = link_section.data().split(b'\x00')[0].decode()
        libdir = Path(self.libpath).parent

        for candidate in (
                libdir / link_name,
                libdir / '.debug' / link_name,
                Path('/usr/lib/debug') / libdir.relative_to('/') / link_name):

            if candidate.exists():
                return str(candidate)

        return None

    def _sniff_dwarf(self, dwarf) -> dict | None:

        signatures = {}
        skipped = 0
        cus = 0

        for cu in dwarf.iter_CUs():

            cus += 1

            # Subprogram entries reside at the compilation unit top level.
            for die in cu.get_top_DIE().iter_children():

                if die.tag != 'DW_TAG_subprogram' or 'DW_AT_declaration' in die.attributes:
                    continue

                try:
                    name = self._get_name(die)

                    if not name:
                        continue

                    args = []
                    unknown = False

                    for child in die.iter_children():

                        if child.tag == 'DW_TAG_unspecified_parameters':
                            # Variadic function.
                            unknown = True

                        if child.tag != 'DW_TAG_formal_parameter':
                            continue

                        hint = self._resolve_hint(child)
                        args.append((self._get_name(child) or f'arg{len(args)}', hint))
                        unknown = unknown or hint is None

                    result = self._resolve_hint(die)

                except _PARSE_ERRORS:
                    skipped += 1
                    continue

                if unknown or name in signatures:
                    continue

                signatures[name] = (args, result)

        if skipped:
            LOGGER.debug('Skipped %d unresolvable entries in %s', skipped, self.libpath)

        return signatures if cus else None

    def sniff(self) -> dict:
        """Sniffs library DWARF data for function signatures.

        Returns {function_name: (args, result)}, where args is a list
        of (name, hint) tuples, and result is a return type hint.
        Hints are ctyped hint names. Functions with types that can not
        be fully resolved are skipped.

        For stripped libraries an external debug information file
        (e.g. from a dbgsym package) is used when available.

        """
        with Path(self.libpath).open('rb') as libfile:

            elf = ELFFile(libfile)
            signatures = None

            if elf.has_dwarf_info():
                signatures = self._sniff_dwarf(_get_dwarf_info(elf))

            if signatures is not None:
                return signatures

            # Stripped library with .gnu_debuglink only.
            debug_path = self._find_debug_file(elf)

        if debug_path is None:
            return {}

        with Path(debug_path).open('rb') as libfile:
            signatures = self._sniff_dwarf(_get_dwarf_info(ELFFile(libfile)))

        return signatures or {}


class NmSymbolSniffer:
    """Uses 'nm' command from 'binutils' package to sniff a library for exported symbols."""

    def __init__(self, libpath: str | Path):
        """

        :param libpath: Library path to sniff for symbols.

        """
        self.libpath = str(libpath)

    def _run(self) -> list[str]:

        try:
            result = subprocess.run(
                ['nm', '-DCl', self.libpath],
                capture_output=True,
            )

        except FileNotFoundError:  # pragma: nocover

            raise SniffingError(
                "Command 'nm' execution failed. "
                "Make sure 'nm' command from 'binutils' package is available.") from None

        if result.returncode:  # pragma: nocover
            raise SniffingError(f"Command 'nm' execution failed: {result.stderr.decode()}")

        return result.stdout.decode().splitlines()

    def _get_symbols(self, lines: list[str]) -> list[SniffedSymbol]:

        symbols = []
        seen = set()

        for line in lines:

            if line.startswith(' '):
                continue

            chunks = line.split(' ')
            chunks_len = len(chunks)

            if chunks_len < 2 or chunks[1] != 'T':
                continue

            if len(chunks) != 3:  # pragma: nocover
                raise SniffingError(
                    f"Command 'nm' execution failed: 3 chunks line expected, but given {chunks}")

            address, symtype, name = chunks

            if symtype != 'T' or name.startswith('_'):
                continue

            name, _, srcline = name.partition('\t')

            base, sep, version = name.partition('@')

            if sep and not version.startswith('@'):
                # Non-default symbol version (name@VER).
                continue

            name = base

            if name in seen:
                continue

            seen.add(name)

            symbols.append(
                SniffedSymbol(
                    name=name,
                    address=address,
                    line=srcline,
                )
            )

        return symbols

    def sniff(self) -> SniffResult:
        """Runs symbols sniffing for library.

        When ``pyelftools`` is installed and the library has DWARF debug
        information, sniffed symbols are enriched with function signatures.

        """
        result = SniffResult(libpath=self.libpath)
        signatures = {}

        if DwarfSniffer.is_available():
            signatures = DwarfSniffer(self.libpath).sniff()

        for symbol in self._get_symbols(self._run()):

            signature = signatures.get(symbol.name)

            if signature:
                args, res = signature
                symbol = symbol._replace(args=args, result=res)

            result.add_symbol(symbol)

        return result
