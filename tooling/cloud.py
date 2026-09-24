"""Small, data-only bridge between GitHub Actions and the existing studio."""
from pathlib import Path
import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from studio import environment, fill_template, metadata

VOICES = ('af_heart', 'am_adam', 'bf_emma', 'bm_george')

def request(script, voice):
    if not re.fullmatch(r'scripts/[a-z0-9][a-z0-9-]*\.md', script):
        raise ValueError('Choose scripts/lowercase-name.md from this repository.')
    path = (ROOT/script).resolve()
    if not path.is_relative_to(ROOT/'scripts') or not path.is_file():
        raise ValueError('The script must exist inside the repository scripts folder.')
    if voice not in VOICES:
        raise ValueError('Choose one of the supported voices.')
    metadata(path)  # Fail before installation if narration is missing.
    return path, path.stem

def timestamp(seconds):
    milliseconds = max(0, round(seconds*1000))
    hours, remainder = divmod(milliseconds, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}'

def captions(transcript):
    lines = ['WEBVTT', '']
    chunk = []
    for word in transcript['words']:
        chunk.append(word)
        if word['word'].endswith(('.', '!', '?')) or len(chunk) >= 12:
            lines.extend([f'{timestamp(chunk[0]["start"])} --> {timestamp(chunk[-1]["end"])}',
                          html.escape(' '.join(w['word'] for w in chunk)), ''])
            chunk = []
    if chunk:
        lines.extend([f'{timestamp(chunk[0]["start"])} --> {timestamp(chunk[-1]["end"])}',
                      html.escape(' '.join(w['word'] for w in chunk)), ''])
    return '\n'.join(lines)

def page(script, slug):
    data = metadata(script)
    output = ROOT/'.site'
    output.mkdir(exist_ok=True)
    transcript = json.loads((ROOT/'compositions'/slug/'transcript.json').read_text(encoding='utf-8'))
    shutil.copy2(ROOT/'output'/f'{slug}.mp4',output/'video.mp4')
    (output/'captions.vtt').write_text(captions(transcript),encoding='utf-8')
    subprocess.run([environment()['HYPERFRAMES_FFMPEG_PATH'],'-v','error','-y','-ss','2',
                    '-i',str(output/'video.mp4'),'-frames:v','1',str(output/'poster.jpg')],check=True)
    values = {
        'TITLE': html.escape(data.get('feature name') or slug),
        'TAGLINE': html.escape(data.get('tagline') or 'Made with Video Studio.'),
        'NARRATION': html.escape(data['narration']),
        'DURATION': f'{transcript["duration"]:.1f}',
    }
    template = (ROOT/'site/index.html').read_text(encoding='utf-8')
    (output/'index.html').write_text(fill_template(template,values),encoding='utf-8')
    (output/'.nojekyll').touch()
    print(f'Playback page: {output}')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode',choices=['prepare','render','page'])
    args = parser.parse_args()
    script, slug = request(os.environ.get('STUDIO_SCRIPT','scripts/hello-studio.md'),
                           os.environ.get('STUDIO_VOICE','af_heart'))
    if args.mode=='prepare':
        output = os.environ.get('GITHUB_OUTPUT')
        if output:
            with open(output,'a',encoding='utf-8') as handle:
                handle.write(f'slug={slug}\n')
        print(f'Validated script: {script.name}')
    elif args.mode=='render':
        subprocess.run([sys.executable,str(ROOT/'studio.py'),'make','--script',str(script),
                        '--voice',os.environ.get('STUDIO_VOICE','af_heart')],cwd=ROOT,check=True)
    else:
        page(script,slug)

if __name__=='__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f'Studio: {exc}')
