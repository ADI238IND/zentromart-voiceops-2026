"""Small configuration surface; secrets never appear in source or logs."""
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
TODAY = '2026-10-20'

def load_env():
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

def dataset_path():
    load_env()
    p = Path(os.environ.get('DATASET_DIR', ROOT / 'dataset')).expanduser().resolve()
    if not (p / 'kb').is_dir() or not (p / 'data/orders.csv').exists():
        raise RuntimeError('Set DATASET_DIR to the extracted supplied dataset folder containing kb/, data/, tools/ and practice/.')
    return p
