import subprocess
from collections import namedtuple
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import List, Union

from .exceptions import SniffingError


SniffedSymbol = namedtuple('SniffedSymbol', ['name', 'address', 'line'])
"""Represents a symbol sniffed from a library."""


class SniffResult:
    """Represents a library sniffing results."""

    def __init__(self, *, libpath: str):
        self.symbols: List[SniffedSymbol] = []
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
            ''
        ]

        for symbol in self.symbols:
            dumped.append(dedent(
                f'''
                @lib.f
                def {symbol.name}():
                    """{symbol.line}"""
                '''
            ))

        dumped.append('\nlib.bind_types()')

        return '\n'.join(dumped)


class NmSymbolSniffer:
    """Uses 'nm' command from 'binutils' package to sniff a library for exported symbols."""

    def __init__(self, libpath: Union[str, Path]):
        """

        :param libpath: Library path to sniff for symbols.

        """
        self.libpath = str(libpath)

    def _run(self) -> List[str]:

        try:
            result = subprocess.run(
                ['nm', '-DCl', self.libpath],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        except FileNotFoundError:  # pragma: nocover

            raise SniffingError(
                "Command 'nm' execution failed. "
                "Make sure 'nm' command from 'binutils' package is available.")

        if result.returncode:  # pragma: nocover
            raise SniffingError(f"Command 'nm' execution failed: {result.stderr.decode()}")

        return result.stdout.decode().splitlines()

    def _get_symbols(self, lines: List[str]) -> List[SniffedSymbol]:

        symbols = []

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

            symbols.append(
                SniffedSymbol(
                    name=name,
                    address=address,
                    line=srcline,
                )
            )

        return symbols

    def sniff(self) -> SniffResult:
        """Runs symbols sniffing for library."""

        result = SniffResult(libpath=self.libpath)

        for symbol in self._get_symbols(self._run()):
            result.add_symbol(symbol)

        return result
