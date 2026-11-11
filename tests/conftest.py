import subprocess
from pathlib import Path

path_so = Path(__file__).parent / 'mylib' / 'mylib.so'

if not path_so.exists():
    subprocess.run(
        ['gcc', '-Wall', '-g', '-shared', '-o', str(path_so), '-fPIC', f'{path_so.with_suffix(".c")}'],
        check=True,
    )
