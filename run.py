"""Organizer entrypoint: one folder of audio in, text/audio/source records out."""
import argparse
import json
import re
import sys
from pathlib import Path
from src.config import dataset_path
from src.llm import API
from src.retrieval import Index
from src.agent import Agent
from src.voice import Voice

AUDIO = {'.wav','.mp3','.flac','.ogg','.m4a'}

def audio_files(folder):
    return sorted((p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in AUDIO),key=lambda p:[int(x) if x.isdigit() else x.lower() for x in re.split(r'(\d+)',p.name)])

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--output',type=Path,default=Path('outputs'))
    p.add_argument('--stt-language',default='en-IN')
    p.add_argument('--tts-language',default='en-IN')
    p.add_argument('--independent',action='store_true',help='Reset state for every file, rather than keeping one session per folder.')
    args = p.parse_args()
    if not args.input.is_dir():
        p.error('--input must be a folder')
    # Root files = one conversation. Each immediate child folder = a separate conversation.
    folders = [args.input] + sorted(d for d in args.input.iterdir() if d.is_dir())
    groups = [(d,audio_files(d)) for d in folders if audio_files(d)]
    if not groups:
        p.error('No supported audio files found in input folder or its immediate subfolders')
    data = dataset_path()
    api, voice = API(), Voice()
    index = Index(data,api)
    failed = 0
    manifest = []
    for session_i,(folder,files) in enumerate(groups):
        agent = Agent(data,index,api)
        out = args.output / (f'{session_i:03d}_'+folder.name)
        out.mkdir(parents=True,exist_ok=True)
        for i,audio in enumerate(files,1):
            if args.independent:
                agent = Agent(data,index,api)
            stem = f'{i:03d}_{audio.stem}'
            try:
                result = voice.turn(audio,agent,out/(stem+'.wav'),args.stt_language,args.tts_language)
                (out/(stem+'.txt')).write_text(result['answer'],encoding='utf-8')
                (out/(stem+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
                manifest.append({'input':str(audio.relative_to(args.input)), 'status':'ok','result':str((out/(stem+'.json')).relative_to(args.output))})
            except Exception as exc:
                failed += 1
                # Never log raw SDK exception strings, which may include request details.
                record = {'status':'error','error_type':type(exc).__name__,'message':'Turn failed; inspect key/quota/network/audio format, then retry. No successful reply claimed.'}
                (out/(stem+'.error.json')).write_text(json.dumps(record,indent=2))
                manifest.append({'input':str(audio.relative_to(args.input)),**record})
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(f'Processed {len(manifest)} files; {failed} failed. Outputs: {args.output}')
    return 1 if failed else 0

if __name__=='__main__':
    try:
        sys.exit(main())
    except RuntimeError as exc:
        print(str(exc),file=sys.stderr)
        sys.exit(2)
