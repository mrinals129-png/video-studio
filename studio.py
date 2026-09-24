"""Cross-platform entry point for local narrated videos."""
import argparse
import html
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from _engine.tts.generate import generate_voice, read_script

ROOT = Path(__file__).resolve().parent

def environment():
    env = dict(os.environ, PYTHONUTF8='1', HYPERFRAMES_NO_UPDATE_CHECK='1', DO_NOT_TRACK='1')
    if not env.get('HYPERFRAMES_FFMPEG_PATH'):
        import imageio_ffmpeg
        env['HYPERFRAMES_FFMPEG_PATH'] = shutil.which('ffmpeg') or imageio_ffmpeg.get_ffmpeg_exe()
    if not env.get('HYPERFRAMES_FFPROBE_PATH'):
        probe = subprocess.check_output(['node', '-p', "require('@ffprobe-installer/ffprobe').path"], cwd=ROOT, text=True).strip()
        env['HYPERFRAMES_FFPROBE_PATH'] = shutil.which('ffprobe') or probe
    return env

def hyperframes(*args):
    subprocess.run(['node', str(ROOT/'node_modules/hyperframes/bin/hyperframes.mjs'), *map(str, args)], cwd=ROOT, env=environment(), check=True)

def probe(path):
    cmd = [environment()['HYPERFRAMES_FFPROBE_PATH'], '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]
    return json.loads(subprocess.check_output(cmd, text=True))

def metadata(path):
    text = Path(path).read_text(encoding='utf-8-sig')
    parts = re.split(r'^##\s+(.+?)\s*$', text, flags=re.MULTILINE)
    result = {parts[i].strip().lower(): parts[i+1].strip() for i in range(1, len(parts)-1, 2)}
    result['narration'] = read_script(str(path))
    if not result['narration']:
        raise ValueError('Add text under a ## Narration heading in your script.')
    return result

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-') or 'video'

def timings(transcript):
    duration = float(transcript['duration'])
    if not math.isfinite(duration) or duration < 6:
        raise ValueError('Use at least six seconds of narration for this three-scene template.')
    ends = [w['end'] for w in transcript['words'] if w['word'].endswith(('.', '!', '?'))]
    first = min(ends, key=lambda t: abs(t-duration*.25)) if ends else duration*.25
    first = max(2., min(first, duration-4.))
    candidates = [t for t in ends if first+2 <= t <= duration-2]
    last = min(candidates, key=lambda t: abs(t-duration*.75)) if candidates else max(first+2, duration*.75)
    last = min(last, duration-2)
    return duration, round(first, 3), round(last, 3)

def fill_template(template, values):
    missing = set(re.findall(r'\{\{(\w+)\}\}', template)) - values.keys()
    if missing:
        raise ValueError(f'Missing template values: {sorted(missing)}')
    # Single pass: text containing braces is data, never another template.
    return re.sub(r'\{\{(\w+)\}\}', lambda match: str(values[match[1]]), template)

def build(script, out, transcript, image=None, video=None, video_start=0., video_volume=0.):
    data = metadata(script)
    duration, first, last = timings(transcript)
    if not math.isfinite(video_start) or video_start < 0:
        raise ValueError('--video-start must be a finite non-negative number.')
    if not math.isfinite(video_volume) or not 0 <= video_volume <= 1:
        raise ValueError('--video-volume must be between 0 and 1.')
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    title = data.get('feature name') or Path(script).stem
    tagline = data.get('tagline') or 'Your story, ready to share.'
    sentences = re.split(r'(?<=[.!?])\s+', data['narration'])
    body = ' '.join(sentences[1:-1]) or data['narration']
    visual = '<div class="workflow"><div><span>01</span> Write your story</div><div><span>02</span> Bring it to life</div><div><span>03</span> Share your video</div></div>'
    if image or video:
        source = Path(image or video).resolve()
        if not source.is_file():
            raise ValueError(f'Asset not found: {source}')
        name = 'source' + source.suffix.lower()
        if video:
            info = probe(source)
            if not any(s['codec_type']=='video' for s in info['streams']):
                raise ValueError('Recording must have a video stream.')
            available = float(info['format']['duration'])-video_start
            if available < last-first:
                raise ValueError(f'Recording needs {last-first:.1f}s after the trim point; only {available:.1f}s remain.')
            visual = f'<video id="recording" class="clip" src="{name}" muted data-start="{first}" data-hf-media-start-basis="global" data-duration="{round(last-first,3)}" data-media-start="{video_start}" data-volume="{video_volume}" data-track-index="4"></video>'
        else:
            if source.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.webp'):
                raise ValueError('Use a PNG, JPG, or WebP screenshot.')
            visual = f'<img src="{name}" alt="{html.escape(title, quote=True)}">'
        if source != (out/name).resolve():
            shutil.copy2(source, out/name)
    values = {k: html.escape(v, quote=True) for k,v in {
        'FEATURE_NAME':title, 'FEATURE_TAGLINE':tagline,
        'PRODUCT_NAME':data.get('product name') or 'Video Studio',
        'DEMO_HEADING':title, 'DEMO_BODY':body,
        'CTA_LINE1':tagline, 'CTA_LINE2':''}.items()}
    values.update(VISUAL=visual, TOTAL_DURATION=duration, SCENE1_DURATION=first,
                  SCENE1_EXIT=first-.4, SCENE2_START=first, SCENE2_DURATION=round(last-first,3),
                  SCENE2_EXIT=last-.4, SCENE3_START=last, SCENE3_DURATION=round(duration-last,3))
    for scene, start, offsets in ((2,first,(.3,.6,.4)), (3,last,(.2,1.0))):
        for offset in offsets:
            values[f'SCENE{scene}_START_PLUS_{offset:.1f}'.replace('.', '_')] = round(start+offset,3)
    template = (ROOT/'_engine/templates/feature-scene.html').read_text(encoding='utf-8')
    (out/'index.html').write_text(fill_template(template,values),encoding='utf-8')
    shutil.copy2(ROOT/'_engine/templates/brand.css', out/'brand.css')
    shutil.copy2(ROOT/'node_modules/gsap/dist/gsap.min.js', out/'gsap.min.js')
    return duration

def verify(path, expected=None):
    info = probe(path)
    types = {s['codec_type'] for s in info['streams']}
    if not {'video','audio'} <= types:
        raise ValueError('Export must contain both video and audio.')
    duration = float(info['format']['duration'])
    if expected is not None and abs(duration-expected) > .5:
        raise ValueError(f'Export duration {duration} does not match narration {expected}.')
    subprocess.run([environment()['HYPERFRAMES_FFMPEG_PATH'], '-v','error','-xerror','-i',str(path),'-f','null','-'],check=True)
    print(f'Verified: {path} ({duration:.2f}s, video + audio, full decode passed)')

def main():
    parser = argparse.ArgumentParser(description='Make narrated videos with Codex or Claude Code.')
    commands = parser.add_subparsers(dest='command',required=True)
    commands.add_parser('doctor')
    make = commands.add_parser('make')
    make.add_argument('--script', required=True, type=Path)
    make.add_argument('--voice',default='af_heart',choices=['af_heart','am_adam','bf_emma','bm_george'])
    visual = make.add_mutually_exclusive_group()
    visual.add_argument('--image',type=Path)
    visual.add_argument('--video',type=Path)
    make.add_argument('--video-start',type=float,default=0.)
    make.add_argument('--video-volume',type=float,default=0.)
    make.add_argument('--build-only',action='store_true')
    make.add_argument('--force',action='store_true',help='Replace an existing composition after intentionally approving regeneration.')
    render = commands.add_parser('render')
    render.add_argument('composition',type=Path)
    render.add_argument('--output',required=True,type=Path)
    preview = commands.add_parser('preview')
    preview.add_argument('composition',type=Path,nargs='?',default=Path('compositions/hello-studio'))
    check = commands.add_parser('verify')
    check.add_argument('video',type=Path)
    args = parser.parse_args()
    if args.command=='doctor':
        import kokoro_onnx, soundfile
        env = environment()
        for name in ('kokoro-v1.0.int8.onnx','voices-v1.0.bin'):
            if not (ROOT/name).is_file():
                raise ValueError(f'Missing {name}; run npm run setup.')
        print(f'Python {sys.version.split()[0]}; speech libraries and model files found.',flush=True)
        node_version = subprocess.check_output(['node','--version'],text=True).strip()
        if int(node_version.lstrip('v').split('.')[0]) < 22:
            raise ValueError('Node.js 22 or newer is required.')
        print(f'Node {node_version}', flush=True)
        for name in ('FFMPEG','FFPROBE'):
            result = subprocess.run([env[f'HYPERFRAMES_{name}_PATH'],'-version'],capture_output=True,text=True,check=True)
            print(result.stdout.splitlines()[0], flush=True)
        hyperframes('browser','ensure')
        print('Core studio dependencies are ready. Run npm run demo for a full production check.')
    elif args.command=='make':
        data = metadata(args.script)
        slug = slugify(args.script.stem)
        out = ROOT/'compositions'/slug
        if out.exists() and not args.force:
            raise ValueError(f'{out} already exists. Use --force to rebuild, or studio render to keep manual edits.')
        generate_voice(data['narration'], str(out),args.voice)
        transcript = json.loads((out/'transcript.json').read_text(encoding='utf-8'))
        duration = build(args.script,out,transcript,args.image,args.video,args.video_start,args.video_volume)
        hyperframes('lint',out)
        if not args.build_only:
            dest=ROOT/'output'/f'{slug}.mp4'
            dest.parent.mkdir(exist_ok=True)
            hyperframes('render',out,'--output',dest,'--workers','1')
            verify(dest,duration)
        print(f'Composition: {out}')
    elif args.command=='render':
        args.output.parent.mkdir(parents=True,exist_ok=True)
        hyperframes('lint',args.composition)
        hyperframes('render',args.composition,'--output',args.output,'--workers','1')
        verify(args.output)
    elif args.command=='preview':
        hyperframes('preview',args.composition,'--no-open')
    elif args.command=='verify':
        verify(args.video)

if __name__=='__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError, ImportError) as exc:
        print(f'Studio: {exc}',file=sys.stderr)
        sys.exit(1)
