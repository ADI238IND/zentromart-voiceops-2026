"""Import the provided ZIP locally; the dataset is excluded from Git and submission."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('zip_path',type=Path)
a = p.parse_args()
dest = Path(__file__).resolve().parent/'dataset'
if dest.exists():
    raise SystemExit('dataset/ already exists. Use it or move it aside before importing another copy.')
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp).resolve()
    with zipfile.ZipFile(a.zip_path) as z:
        for member in z.infolist():
            if not (root/member.filename).resolve().is_relative_to(root):
                raise SystemExit('Unsafe ZIP path rejected')
        z.extractall(root)
    candidates = [f.parent for f in root.rglob('validate_dataset.py') if (f.parent/'kb').is_dir()]
    if len(candidates)!=1:
        raise SystemExit('Could not uniquely identify supplied dataset root')
    subprocess.run([sys.executable,str(candidates[0]/'validate_dataset.py')],cwd=candidates[0],check=True)
    shutil.copytree(candidates[0],dest)
print('Dataset imported to dataset/. It must not be committed or included in your submission ZIP.')
