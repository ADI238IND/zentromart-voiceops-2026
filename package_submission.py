"""Build a submission only when real required deliverables are present."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent
FILES = ['README.md','.env.example','.gitignore','requirements.txt','run.py','app.py','evaluate.py',
    'setup_dataset.py','make_report.py','package_submission.py','publish_github.ps1','SUBMIT.md',
    'report.pdf','report_notes.json','REPOSITORY_URL.txt']
FOLDERS = ['src','tests','docs','sample_outputs']

def selected():
    result = [ROOT/x for x in FILES if (ROOT/x).is_file()]
    for folder in FOLDERS:
        result.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.name!='.env' and not p.name.startswith('.env.') and p.name!='tickets_created.csv')
    return result

def preflight(demo_seconds=None):
    errors=[]
    for f in FILES:
        if not (ROOT/f).exists():
            errors.append(f'Missing {f}')
    url_file=ROOT/'REPOSITORY_URL.txt'
    url=url_file.read_text(encoding='utf-8-sig').strip() if url_file.exists() else ''
    if not re.fullmatch(r'https://github\.com/[\w.-]+/[\w.-]+/?',url):
        errors.append('REPOSITORY_URL.txt needs the actual public repository URL')
    elif url not in (ROOT/'README.md').read_text(encoding='utf-8-sig'):
        errors.append('README.md must include the actual repository URL')
    scores=ROOT/'sample_outputs/live_scores.json'
    if not scores.exists():
        errors.append('Run python evaluate.py with real LLM credentials; live_scores.json is missing')
    else:
        try:
            values=json.loads(scores.read_text())
            counts = {name: values.get(name,{}).get('count',0) for name in ('step1','step2','conversations')}
            if counts['step1'] <= 0 or counts['step1'] != counts['step2'] or counts['conversations'] <= 0:
                errors.append('Complete the matched baseline/RAG evaluation and a conversation evaluation')
            for name,count in counts.items():
                lines=(ROOT/f'sample_outputs/{name}.jsonl').read_text().splitlines()
                if len(lines)!=count:
                    errors.append(f'{name}.jsonl is incomplete')
        except (ValueError,KeyError,FileNotFoundError):
            errors.append('Live evaluation files are malformed or incomplete')
    demo=ROOT/'demo.mp4'
    if not demo.exists() or demo.stat().st_size==0:
        errors.append('Record a real spoken demo.mp4 (maximum 120 seconds)')
    else:
        probe=shutil.which('ffprobe')
        if probe:
            try:
                duration=float(subprocess.check_output([probe,'-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(demo)],text=True,stderr=subprocess.DEVNULL))
            except (ValueError,subprocess.CalledProcessError):
                errors.append('Unable to read demo.mp4 duration')
                duration=0
        else:
            duration=demo_seconds or 0
            if not duration:
                errors.append('Install ffprobe, or inspect video duration yourself and pass --demo-seconds N')
        if duration>120 or duration<0:
            errors.append('Demo must be at most 120 seconds')
    audio=ROOT/'sample_outputs/audio'
    if not list(audio.rglob('*.wav')) or not list(audio.rglob('*.txt')) or not list(audio.rglob('*.json')):
        errors.append('Copy genuine batch text, speech and source records to sample_outputs/audio/')
    manifests=list(audio.rglob('manifest.json'))
    if not manifests:
        errors.append('Include a real batch manifest.json with successful audio samples')
    for manifest in manifests:
        try:
            records=json.loads(manifest.read_text())
            if not records or any(r.get('status')!='ok' for r in records):
                errors.append('Sample batch manifest contains failed or empty results')
        except (ValueError,TypeError):
            errors.append('Invalid sample manifest')
    try:
        from pypdf import PdfReader
        reader = PdfReader(ROOT/'report.pdf')
        if scores.exists() and any('NOT RUN' in (page.extract_text() or '') for page in reader.pages):
            errors.append('Regenerate report.pdf after live evaluation')
        if len(reader.pages)>4:
            errors.append('Report exceeds four pages')
    except ImportError:
        errors.append('Install requirements, including pypdf, to check report page count')
    # Runtime notes must be updated after actual testing.
    if scores.exists() and b'NOT RUN' in (ROOT/'report.pdf').read_bytes():
        errors.append('Regenerate report.pdf after live evaluation')
    return errors

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--team',default='AdityaSinghal')
    p.add_argument('--demo-seconds',type=float,help='Manually verified duration, used only if ffprobe is unavailable')
    a=p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',a.team):
        p.error('Use only letters, numbers, underscore and hyphen in team name')
    errors=preflight(a.demo_seconds)
    if errors:
        raise SystemExit('Submission not ready:\n- '+'\n- '.join(errors))
    path=ROOT/(a.team+'_voiceops.zip')
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for file in selected()+[ROOT/'demo.mp4']:
            z.write(file,file.relative_to(ROOT))
    print('Created '+str(path))
    print('Review the ZIP and public repository access before submitting. Preflight does not certify answer accuracy or demo quality.')
if __name__=='__main__':
    main()
