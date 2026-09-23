"""Install local Python dependencies and download the two Kokoro model files."""
from pathlib import Path
import os
import subprocess
import sys
import urllib.request
import venv

ROOT = Path(__file__).resolve().parents[1]

def main():
    if sys.version_info < (3, 10):
        raise SystemExit('Python 3.10 or newer is required.')
    target = ROOT / '.venv'
    python = target / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.exists():
        print('Creating an isolated Python environment...', flush=True)
        venv.create(target, with_pip=True)
    subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(ROOT / '_engine/tts/requirements.txt')], check=True)
    base = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/'
    for name in ('kokoro-v1.0.int8.onnx', 'voices-v1.0.bin'):
        dest = ROOT / name
        if dest.exists() and dest.stat().st_size > 1_000_000:
            print(f'Found {name}')
            continue
        partial = dest.with_suffix(dest.suffix + '.partial')
        print(f'Downloading {name}...', flush=True)
        urllib.request.urlretrieve(base + name, partial)
        if partial.stat().st_size < 1_000_000:
            raise RuntimeError(f'Download was too small: {name}. Rerun setup.')
        partial.replace(dest)
    print('Voice setup complete. Run npm run doctor to check rendering dependencies.')

if __name__ == '__main__':
    main()
